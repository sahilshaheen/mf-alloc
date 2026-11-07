import random
import re
import string
from collections import Counter
from collections.abc import Collection
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import NamedTuple

import pymupdf

FIXTURE_PASSWORD = "Fixture@123"
MIN_NAME_TOKEN_LENGTH = 3
MIN_IDENTIFIER_LENGTH = 6
SEGMENT_GAP = 24.0
COLUMN_TOLERANCE = 6.0
LINE_GAP_FACTOR = 2.0

# The parser depends on ISINs, so they are never redacted, even when a digit run inside one looks like a folio.
ISIN = re.compile(r"IN[A-Z0-9]{9}\d")
ISIN_WORD = re.compile(rf"\b{ISIN.pattern}\b")

# Digit runs of 6+ catch folio numbers and PIN codes; amounts never match because they carry separators.
DETECTED_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    "mobile": re.compile(r"(?<!\d)[6-9]\d{9}(?!\d)"),
    "folio or PIN": re.compile(r"(?<![\d.,])\d{6,}(?:\s*/\s*\d+)?(?![\d.,])"),
}


class Char(NamedTuple):
    text: str
    box: pymupdf.Rect


class Word(NamedTuple):
    text: str
    rect: pymupdf.Rect
    line: tuple[int, int]
    chars: list[Char]
    origin: pymupdf.Point
    size: float


@dataclass(frozen=True)
class Redaction:
    targets: list[str]
    fake_words: set[str]


def open_statement(path: Path, password: str) -> pymupdf.Document:
    doc = pymupdf.open(path)
    if doc.needs_pass and not doc.authenticate(password):
        raise ValueError(f"wrong password for {path.name}")
    return doc


def fake_like(value: str, rng: random.Random) -> str:
    def swap(char: str) -> str:
        if char.isdigit():
            return rng.choice(string.digits)
        if char.isascii() and char.isalpha():
            return rng.choice(
                string.ascii_uppercase if char.isupper() else string.ascii_lowercase
            )
        return char

    return "".join(swap(char) for char in value)


def normalize(word: str) -> str:
    return "".join(char for char in word.casefold() if char.isalnum())


def shape(value: str) -> str:
    """The value with letters and digits masked, safe to show in a message."""
    return re.sub(r"[a-z]", "a", re.sub(r"[A-Z]", "A", re.sub(r"\d", "9", value)))


def is_long_identifier(token: str) -> bool:
    """Folio-like tokens can be glued to a prefix or suffix in the PDF, so they match inside a word."""
    return len(token) >= MIN_IDENTIFIER_LENGTH and any(char.isdigit() for char in token)


def union(rects: list[pymupdf.Rect]) -> pymupdf.Rect:
    box = pymupdf.Rect(rects[0])
    for rect in rects[1:]:
        box |= rect
    return box


def make_word(chars: list[dict], line: tuple[int, int], size: float) -> Word:
    boxes = [Char(char["c"], pymupdf.Rect(char["bbox"])) for char in chars]
    return Word(
        text="".join(char.text for char in boxes),
        rect=union([char.box for char in boxes]),
        line=line,
        chars=boxes,
        origin=pymupdf.Point(chars[0]["origin"]),
        size=size,
    )


def split_runs(chars: list[dict]) -> list[list[dict]]:
    """Characters split at spaces and wherever the text jumps back to the left, which marks a new text run."""
    runs: list[list[dict]] = []
    current: list[dict] = []
    for char in chars:
        jumped_back = current and char["origin"][0] < current[-1]["origin"][0]
        if char["c"].isspace() or jumped_back:
            if current:
                runs.append(current)
            current = []
        if not char["c"].isspace():
            current.append(char)
    if current:
        runs.append(current)
    return runs


def extract_words(page: pymupdf.Page) -> list[Word]:
    """Words with their characters, split at spaces, at font changes and at backward jumps."""
    words: list[Word] = []
    for block in page.get_text("rawdict")["blocks"]:
        for line_number, line in enumerate(block.get("lines", [])):
            for span in line["spans"]:
                key = (block["number"], line_number)
                words.extend(
                    make_word(run, key, span["size"])
                    for run in split_runs(span["chars"])
                )
    return words


def line_segments(words: list[Word]) -> list[list[int]]:
    """Runs of words on one line with no wide horizontal gap, so side-by-side columns come apart."""
    segments: list[list[int]] = []
    for _, group in groupby(range(len(words)), key=lambda i: words[i].line):
        current: list[int] = []
        for index in group:
            if (
                current
                and words[index].rect.x0 - words[current[-1]].rect.x1 > SEGMENT_GAP
            ):
                segments.append(current)
                current = []
            current.append(index)
        segments.append(current)
    return segments


def column_order(words: list[Word]) -> list[int]:
    """Word indices in column reading order: segments sharing a left edge and stacked closely form one stream."""
    boxed = [(union([words[i].rect for i in seg]), seg) for seg in line_segments(words)]
    boxed.sort(key=lambda item: (item[0].y0, item[0].x0))
    streams: list[list[tuple[pymupdf.Rect, list[int]]]] = []
    for box, segment in boxed:
        for stream in streams:
            last = stream[-1][0]
            gap = box.y0 - last.y1
            if (
                abs(box.x0 - last.x0) <= COLUMN_TOLERANCE
                and -last.height / 2 <= gap <= LINE_GAP_FACTOR * last.height
            ):
                stream.append((box, segment))
                break
        else:
            streams.append([(box, segment)])
    return [index for stream in streams for _, segment in stream for index in segment]


@dataclass(frozen=True)
class PageWords:
    words: list[Word]
    orders: list[list[int]]

    @classmethod
    def of(cls, page: pymupdf.Page) -> "PageWords":
        words = extract_words(page)
        return cls(words, [list(range(len(words))), column_order(words)])

    def find(self, target: str) -> set[tuple[int, ...]]:
        """Runs of page words that spell the target, ignoring case, punctuation and line breaks."""
        wanted = [token for token in map(normalize, target.split()) if token]
        runs: set[tuple[int, ...]] = set()
        if len(wanted) == 1 and is_long_identifier(wanted[0]):
            runs.update(
                (index,)
                for index, word in enumerate(self.words)
                if wanted[0] in normalize(word.text)
            )
        for order in self.orders:
            significant = [
                (index, key)
                for index in order
                if (key := normalize(self.words[index].text))
            ]
            keys = [key for _, key in significant]
            runs.update(
                tuple(significant[start + offset][0] for offset in range(len(wanted)))
                for start in range(len(keys) - len(wanted) + 1)
                if wanted and keys[start : start + len(wanted)] == wanted
            )
        return runs


def collect_targets(
    doc: pymupdf.Document, name: str, addresses: list[str]
) -> list[str]:
    text = ISIN_WORD.sub(" ", "\n".join(page.get_text() for page in doc))
    targets = {name, *addresses}
    targets.update(
        token
        for token in name.split()
        if len(normalize(token)) >= MIN_NAME_TOKEN_LENGTH
    )
    for pattern in DETECTED_PATTERNS.values():
        targets.update(match.strip() for match in pattern.findall(text))
    return sorted(targets, key=len, reverse=True)


def trimmed(box: pymupdf.Rect, others: list[pymupdf.Rect]) -> pymupdf.Rect | None:
    """The part of a character box that touches no other word's characters, or None if all of it does."""
    piece = pymupdf.Rect(box)
    for other in others:
        overlap = piece & other
        if overlap.is_empty:
            continue
        if overlap.width <= overlap.height:
            if other.x0 > piece.x0:
                piece.x1 = other.x0
            else:
                piece.x0 = other.x1
        elif other.y0 > piece.y0:
            piece.y1 = other.y0
        else:
            piece.y0 = other.y1
        if piece.is_empty:
            return None
    return piece


def fitted_size(fake: str, size: float, width: float) -> float:
    natural = pymupdf.get_text_length(fake, fontname="helv", fontsize=size)
    return size if natural <= width else size * width / natural


def claim_words(page_text: PageWords, targets: list[str]) -> tuple[set[int], set[str]]:
    claimed: set[int] = set()
    matched: set[str] = set()
    for target in targets:
        for run in sorted(page_text.find(target)):
            matched.add(target)
            claimed.update(
                index
                for index in run
                if not ISIN.fullmatch(page_text.words[index].text)
            )
    return claimed, matched


def altered_words(before: PageWords, claimed: set[int], after: PageWords) -> list[str]:
    kept = Counter(
        word.text for index, word in enumerate(before.words) if index not in claimed
    )
    kept.subtract(Counter(word.text for word in after.words))
    return [shape(text) for text, missing in kept.items() if missing > 0]


def redact_page(
    page: pymupdf.Page,
    page_number: int,
    targets: list[str],
    fake_words: dict[str, str],
    rng: random.Random,
) -> set[str]:
    before = PageWords.of(page)
    claimed, matched = claim_words(before, targets)
    others = [
        char.box
        for index, word in enumerate(before.words)
        if index not in claimed
        for char in word.chars
    ]
    for index in claimed:
        for char in before.words[index].chars:
            if (piece := trimmed(char.box, others)) is not None:
                page.add_redact_annot(piece, fill=(1, 1, 1))
    page.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE
    )
    for index in sorted(claimed):
        word = before.words[index]
        fake = fake_words.setdefault(word.text, fake_like(word.text, rng))
        page.insert_text(
            word.origin,
            fake,
            fontname="helv",
            fontsize=fitted_size(fake, word.size, word.rect.width),
            color=(0, 0, 0),
        )
    damaged = altered_words(before, claimed, PageWords.of(page))
    if damaged:
        raise ValueError(
            f"page {page_number}: redaction altered words that were not targets, shaped {', '.join(damaged)}"
        )
    return matched


def strip_extras(doc: pymupdf.Document) -> None:
    doc.set_metadata({})
    doc.del_xml_metadata()
    doc.set_toc([])
    for name in doc.embfile_names():
        doc.embfile_del(name)
    for page in doc:
        for link in page.get_links():
            page.delete_link(link)


def redact_pdf(
    src: Path, src_password: str, dst: Path, name: str, addresses: list[str]
) -> Redaction:
    doc = open_statement(src, src_password)
    rng = random.SystemRandom()
    targets = collect_targets(doc, name, addresses)
    fake_words: dict[str, str] = {}
    matched: set[str] = set()
    for number, page in enumerate(doc, start=1):
        matched |= redact_page(page, number, targets, fake_words, rng)
    given = {
        "--name": name,
        **{f"--address #{i}": line for i, line in enumerate(addresses, start=1)},
    }
    missing = [label for label, value in given.items() if value not in matched]
    if missing:
        raise ValueError(f"not found on any page: {', '.join(missing)}")
    strip_extras(doc)
    doc.save(
        dst,
        garbage=4,
        deflate=True,
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw=FIXTURE_PASSWORD,
        owner_pw=FIXTURE_PASSWORD,
    )
    return Redaction(targets=targets, fake_words=set(fake_words.values()))


def document_parts(doc: pymupdf.Document) -> dict[str, str]:
    parts = {
        f"page {number} text": page.get_text()
        for number, page in enumerate(doc, start=1)
    }
    parts["metadata"] = " ".join(str(value) for value in doc.metadata.values() if value)
    parts["xml metadata"] = doc.get_xml_metadata()
    for xref in range(1, doc.xref_length()):
        parts[f"object {xref}"] = doc.xref_object(xref, compressed=True)
    return parts


def is_made_of_fakes(match: str, fake_words: Collection[str]) -> bool:
    pieces = [piece for piece in re.split(r"[\s/]+", match) if piece]
    return all(any(piece in fake for fake in fake_words) for piece in pieces)


def contains_word(text: str, target: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(target.casefold())}(?![a-z0-9])"
    return re.search(pattern, text.casefold()) is not None


def find_leaks(
    path: Path, password: str, targets: Collection[str], fake_words: Collection[str]
) -> list[str]:
    doc = open_statement(path, password)
    leaks: list[str] = []
    for number, page in enumerate(doc, start=1):
        page_text = PageWords.of(page)
        leaks.extend(
            f"page {number}: a value shaped {shape(target)} was not replaced"
            for target in targets
            if page_text.find(target)
        )
    for where, text in document_parts(doc).items():
        if not where.startswith("page"):
            leaks.extend(
                f"{where}: contains a value shaped {shape(target)}"
                for target in targets
                if contains_word(text, target)
            )
            continue
        for kind, pattern in DETECTED_PATTERNS.items():
            shapes = {
                shape(match.strip())
                for match in pattern.findall(ISIN_WORD.sub(" ", text))
                if not is_made_of_fakes(match, fake_words)
            }
            if shapes:
                leaks.append(
                    f"{where}: unreplaced {kind} pattern(s) shaped {', '.join(sorted(shapes))}"
                )
    return leaks
