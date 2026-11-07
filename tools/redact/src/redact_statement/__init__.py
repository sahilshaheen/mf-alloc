import argparse
import sys
from pathlib import Path

from redact_statement.redaction import (
    FIXTURE_PASSWORD,
    find_leaks,
    open_statement,
    redact_pdf,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace personal data in a password-protected statement PDF with fakes of the same shape."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("password", help="password of the source PDF")
    parser.add_argument(
        "--name", required=True, help="your name as printed on the statement"
    )
    parser.add_argument(
        "--address",
        action="append",
        required=True,
        help="your address as printed; may wrap across lines. Repeat the option for separate parts",
    )
    args = parser.parse_args()

    redaction = redact_pdf(
        args.source, args.password, args.destination, args.name, args.address
    )
    leaks = find_leaks(
        args.destination, FIXTURE_PASSWORD, redaction.targets, redaction.fake_words
    )
    if leaks:
        args.destination.unlink()
        print("\n".join(leaks), file=sys.stderr)
        sys.exit("Verification failed; the output was deleted.")
    print(
        f"Replaced {len(redaction.targets)} values. Verification passed. Output password: {FIXTURE_PASSWORD}"
    )
    print("Top of page 1 of the output (check that nothing personal is left):")
    first_page = open_statement(args.destination, FIXTURE_PASSWORD)[0]
    print("\n".join(first_page.get_text(sort=True).splitlines()[:15]))
    print("Then open the output and read every page before sharing it.")
