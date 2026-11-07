from pathlib import Path

import pymupdf
import pytest

from redact_statement import main
from redact_statement.redaction import (
    DETECTED_PATTERNS,
    FIXTURE_PASSWORD,
    find_leaks,
    open_statement,
    redact_pdf,
)

SOURCE_PASSWORD = "Source@12345"
NAME = "John Quincy Tester"
ADDRESS = "12 Sample Street, Test Colony, Example City - 560001"
ADDRESS_LINES = ["12 Sample Street,", "Test Colony,", "Example City - 560001"]
SIDE_PARAGRAPH = ["Mutual fund investments are", "subject to market risks."]
EMAIL = "john.tester@example.com"
MOBILE = "9876543210"
FOLIOS = ["1234567890", "91011223344/0", "KFS7654321"]
ISINS = ["INF000A01234", "INF0R8301011", "INF204KC1097"]
SCHEME = "Example Flexi Cap Fund - Direct Growth"
KEPT = [*ISINS, SCHEME, "123.456", "405.1234", "50,012.34", "CAMS"]
CROWDED_ROWS = [("872386246609/5", "INF204KC1097"), ("70687145404/7", "INF247L01411")]
COLUMNS = "Folio No.  ISIN  Scheme Name  Cost Value (INR)  Unit Balance  NAV Date  NAV  Market Value (INR)  Registrar"


def save_encrypted(doc: pymupdf.Document, path: Path) -> Path:
    doc.save(
        path,
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw=SOURCE_PASSWORD,
        owner_pw=SOURCE_PASSWORD,
    )
    return path


def identity_box(page: pymupdf.Page) -> None:
    page.insert_text((72, 72), f"Email Id: {EMAIL}", fontsize=10)
    page.insert_text((72, 86), NAME.upper(), fontsize=10)
    for i, line in enumerate(ADDRESS_LINES):
        page.insert_text((72, 100 + 14 * i), line, fontsize=10)
        if i < len(SIDE_PARAGRAPH):
            page.insert_text((350, 100 + 14 * i), SIDE_PARAGRAPH[i], fontsize=10)
    page.insert_text((72, 142), f"Mobile: {MOBILE}", fontsize=10)


@pytest.fixture
def statement(tmp_path: Path) -> Path:
    doc = pymupdf.open()
    first = doc.new_page()
    identity_box(first)
    first.insert_text((36, 200), COLUMNS, fontsize=6)
    for row, (folio, isin) in enumerate(zip(FOLIOS, ISINS)):
        cells = [
            folio,
            isin,
            SCHEME,
            "50,000.00",
            "123.456",
            "07-Nov-2026",
            "405.1234",
            "50,012.34",
            "CAMS",
        ]
        first.insert_text((36, 220 + 14 * row), "  ".join(cells), fontsize=6)
    second = doc.new_page()
    second.insert_text((72, 72), f"Statement sent to {EMAIL}", fontsize=10)
    second.insert_text((72, 86), f"Dear {NAME.lower()},", fontsize=10)
    return save_encrypted(doc, tmp_path / "original.pdf")


@pytest.fixture
def crowded_statement(tmp_path: Path) -> Path:
    """A folio printed wide enough that its box reaches into the ISIN beside it."""
    doc = pymupdf.open()
    page = doc.new_page()
    identity_box(page)
    for row, (folio, isin) in enumerate(CROWDED_ROWS):
        page.insert_text((36, 220 + 14 * row), folio, fontsize=7)
        page.insert_text((80, 220 + 14 * row), isin, fontsize=7)
    return save_encrypted(doc, tmp_path / "crowded.pdf")


@pytest.fixture
def redacted(statement: Path, tmp_path: Path):
    out = tmp_path / "redacted.pdf"
    return out, redact_pdf(statement, SOURCE_PASSWORD, out, NAME, [ADDRESS])


def page_texts(path: Path) -> list[str]:
    return [page.get_text() for page in open_statement(path, FIXTURE_PASSWORD)]


def test_output_is_protected_by_the_fixture_password_not_the_original(redacted):
    out, _ = redacted
    assert pymupdf.open(out).needs_pass
    assert not pymupdf.open(out).authenticate(SOURCE_PASSWORD)
    assert pymupdf.open(out).authenticate(FIXTURE_PASSWORD)


def test_personal_data_is_gone_whatever_its_case_or_line_wrapping(redacted):
    out, _ = redacted
    text = "\n".join(page_texts(out)).casefold()
    secrets = [
        "john",
        "quincy",
        "tester",
        "sample street",
        "test colony",
        "example city",
        EMAIL,
        MOBILE,
        "1234567890",
        "91011223344",
        "7654321",
        "560001",
    ]
    for secret in secrets:
        assert secret not in text


def test_isins_scheme_names_and_neighbouring_text_are_untouched(redacted):
    out, _ = redacted
    text = "\n".join(page_texts(out))
    for kept in [*KEPT, *SIDE_PARAGRAPH]:
        assert kept in text


def test_a_folio_reaching_into_the_next_column_does_not_damage_its_neighbour(
    crowded_statement: Path, tmp_path: Path
):
    out = tmp_path / "crowded-out.pdf"
    redact_pdf(crowded_statement, SOURCE_PASSWORD, out, NAME, [ADDRESS])
    text = "\n".join(page_texts(out))
    for folio, isin in CROWDED_ROWS:
        assert isin in text
        assert folio[:8] not in text


def test_same_value_gets_the_same_fake_on_every_page(redacted):
    out, _ = redacted
    first, second = page_texts(out)
    fake_email = DETECTED_PATTERNS["email"].findall(first)[0]
    assert fake_email != EMAIL
    assert fake_email in second


def test_wrong_source_password_is_rejected(statement: Path, tmp_path: Path):
    with pytest.raises(ValueError, match="password"):
        redact_pdf(statement, "wrong", tmp_path / "out.pdf", NAME, [ADDRESS])


def test_name_or_address_not_on_any_page_is_an_error(statement: Path, tmp_path: Path):
    with pytest.raises(ValueError, match=r"--name, --address #1"):
        redact_pdf(
            statement,
            SOURCE_PASSWORD,
            tmp_path / "out.pdf",
            "Nobody Here",
            ["1 Nowhere Lane"],
        )


def test_leak_check_passes_on_redacted_and_fails_on_original(redacted, statement: Path):
    out, redaction = redacted
    assert (
        find_leaks(out, FIXTURE_PASSWORD, redaction.targets, redaction.fake_words) == []
    )
    assert find_leaks(
        statement, SOURCE_PASSWORD, redaction.targets, redaction.fake_words
    )


def test_leak_check_ignores_chance_matches_inside_binary_streams(tmp_path: Path):
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Nothing personal", fontsize=10)
    xref = doc.get_new_xref()
    doc.update_object(xref, "<<>>")
    doc.update_stream(xref, b"\x00xxanixx\x01")
    path = tmp_path / "binary.pdf"
    doc.save(path)
    assert find_leaks(path, "", ["ani"], []) == []


def run_cli(statement: Path, tmp_path: Path, monkeypatch) -> Path:
    out = tmp_path / "cli-out.pdf"
    argv = [
        "redact-statement",
        str(statement),
        str(out),
        SOURCE_PASSWORD,
        "--name",
        NAME,
        "--address",
        ADDRESS,
    ]
    monkeypatch.setattr("sys.argv", argv)
    main()
    return out


def test_cli_redacts_with_file_password_name_and_address(
    statement: Path, tmp_path: Path, monkeypatch
):
    out = run_cli(statement, tmp_path, monkeypatch)
    assert "tester" not in "\n".join(page_texts(out)).casefold()


def test_cli_deletes_output_when_a_value_survives(
    statement: Path, tmp_path: Path, monkeypatch
):
    monkeypatch.setattr("redact_statement.find_leaks", lambda *args: ["page 1: leak"])
    with pytest.raises(SystemExit):
        run_cli(statement, tmp_path, monkeypatch)
    assert not (tmp_path / "cli-out.pdf").exists()
