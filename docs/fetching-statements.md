# Fetching your statements

TrueHold v1 reads current holdings only. This guide gets you one real sample statement, so the parser is built against a real layout. It is also the draft for the in-app "Get your statement" guide (S2 in the design spec), so note every place where the real site differs from what is written here.

Mark each step `OK` if it worked as written, or write what was different. Steps marked **(verify)** come from secondary sources.

## What to fetch

One statement for now: the **CAMS CAS, Summary**. It covers all your mutual fund folios across AMCs (CAMS + KFintech): units, NAV and value per scheme.

Why this one:

- CAMS returns your whole mutual fund set, so a KFintech request would add a layout without adding funds.
- Summary has what v1 needs (units, NAV, value). Detailed adds transactions, which only the XIRR roadmap item needs.

Deferred: a depository (demat) CAS for shares, ETFs and bonds. See "Deferred: demat statement" at the end.

## Before you start

- Use the PAN, email and mobile registered on your folios and demat account. A mismatch is the most common reason a request returns nothing.
- Each PDF is password protected. **Record the password for each file**, in a password manager, not in this repo.
- Save the original PDFs **outside the repository** (for example `~/Documents/statements-original/`).
- Keep each file exactly as delivered. Do not print to PDF or re-save it.

## 1. CAMS CAS, Summary

Walked through in a browser on 2026-11-08 up to, but not including, submitting the form. Screenshots are in `.playwright-mcp/` (git-ignored): `cams-02-cas-page.png`, `cams-03-form.png`. No captcha appeared before the form.

**Link:** <https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement>

On first visit a cookie banner (choose "Essential only") and sometimes a promo popup (close with its X) may cover the page.

1. Make sure the **CAS - CAMS+KFintech** tile is selected (top left). Do not pick **CAS-CAMS** next to it, which is a different, CAMS-only statement.
2. Statement Type: **Summary** (already selected).
3. As On: today's date (pre-filled).
4. Folio Listing: **Without zero balance folios** (already selected).
5. Email: the one registered on your folios.
6. PAN: optional, leave it blank.
7. Password and Confirm Password: you choose it, and it is the only thing that opens the PDF. Rules: 8 to 15 characters, starts with a letter, at least one uppercase letter and one digit, and at least one of `@ # $ * _`. Record it.
8. **Submit.** The statement is emailed, encrypted with your password.

**Which folio listing to choose** (the form's own hint for each option in quotes):

| Option | Use it? | Why |
|---|---|---|
| **Without zero balance folios** | **Yes** | "Excludes folios with zero balance." Only folios that hold units today, which is what the allocation needs. The default. |
| With zero balance folios | No | "All folio listing." Adds closed folios with nothing in them. |
| Transacted folios and folios with balance | No | "Folios with balance and folios where transactions took place for the selected period." Meant for period statements; we use an as-on snapshot. |

**Not yet observed** (needs a real submit): the confirmation message after Submit, how long the email takes, and the PDF itself. Record them when you submit, including whether the PDF lists ISINs or only scheme names, and whether it shows AMFI codes.

## What to hand back

A one-line entry, kept privately (not in the repo): date requested, password, anything different from this guide. And the answer to:

- Does the CAMS Summary carry ISINs, AMFI codes, or only scheme names?

## After fetching: original and sanitised copies

For the original PDF we want a **sanitised copy** with no password and no personal data. Everything below happens on your machine. Do not paste any original statement into a chat, issue or search.

### What counts as PII here

Redact or replace all of these:

- Name, address, PIN code, email, phone number.
- PAN (also appears in headers, footers and in KYC lines).
- Folio numbers, demat account numbers, DP IDs, client IDs, BO IDs.
- Bank account numbers and nominee names.
- Barcodes, QR codes and any digital signature block.
- Metadata: author, title, creator, XMP, embedded files.

Keep (these are not personal and the parser needs them): scheme and AMC names, ISINs, AMFI codes, dates, NAVs, units, transaction types, section headings, page structure. Your balances and amounts are not identifying on their own once the name and folio are gone; keep them so the parser meets real number formats, unless you have a reason to change them.

### How to do it properly

Drawing a black box over text is **not** redaction: the text stays in the file and can be copied out. Remove the text from the file itself.

1. **Strip the password first.** Do this with a tool, not by printing, so layout and fonts stay identical. For example `qpdf --password=<pw> --decrypt original.pdf unlocked.pdf`. The password goes on the command line, so type it with a leading space or read it from a prompt so it stays out of shell history.
2. **Replace, don't delete.** Swap each PII string for a fake of the *same shape and length* (a 10-digit folio becomes another 10-digit number, a PAN becomes `ABCDE1234F`-style, the name becomes `TEST INVESTOR`). A parser tested on empty gaps, or on strings of different width, would be tested against a different layout. Use one fake value per real value, consistently across all pages.
3. **Use a real redaction engine.** PyMuPDF's redact annotations (`add_redact_annot` then `apply_redactions`) remove the underlying text and let you write the replacement in the same place. Run it from a throwaway script in a scratch directory, not in the repo.
4. **Strip metadata and extras.** Clear the document info and XMP, and drop embedded files and attachments. A digitally signed PDF will no longer verify after any edit; that is expected.
5. **Verify with search, not by eye.** Extract the text of the result (`pdftotext`) and search it for every real value: your name and its parts, PAN, email, phone, PIN code, every folio and account number, and the password. Check metadata with `exiftool` and `qpdf --show-encryption`. Also search the raw bytes (`strings`) since text can hide in unused objects. Then open the result and read every page, including headers, footers and the first page's address block.
6. **Keep the redaction map private.** The real→fake mapping is itself PII. Do not commit it. Delete it once you have verified the file.
7. **Decide where each file lives.** Originals stay outside the repo. Sanitised copies are the only ones that may enter the repo as test fixtures; `*.pdf` is currently git-ignored, so adding them will need an explicit exception in `.gitignore`, which we should decide on together.

If any check in step 5 finds a real value, treat the file as unsafe and redo the redaction rather than patching.

A script for steps 1 to 5 is a small job, and I can write it with its verification step when you are ready.

## Deferred: demat statement

Not in scope until the CDSL login works. Findings so far (2026-11-08):

- **CDSL:** <https://www.cdslindia.com/cas/logincas.aspx> asks for PAN, BO ID (16-digit demat account number), date of birth and a reCAPTCHA. A real login attempt returned "Internal Error Occurred Please try after some time." Nothing past login is verified. CDSL's FAQ says dispatched statements can be downloaded from the CAS tab, password is the first holder's PAN in capitals. Another CDSL service, "My Easi" (`web.cdslindia.com/myeasitoken/home/login`), is unexplored.
- **NSDL:** <https://nsdlcas.nsdl.com/> only offers "Subscribe to e-CAS" (CAS ID, PAN, captcha); its FAQ says to ask NSDL or your DP for a duplicate. Both need a subscription or a request, so it is not a candidate for the guide.
- A depository CAS comes from your default depository (the one holding your earliest-opened demat account), and the design spec's open questions apply: do MF rows carry ISINs, and does a CDSL statement include NSDL accounts?

## Sources

- CDSL CAS FAQ: <https://www.cdslindia.com/cas/faq.html>
- NSDL CAS site and FAQ: <https://nsdlcas.nsdl.com/>, <https://investor.nsdl.com/portal/en/kb/articles/faqs-on-cas-26-10-2023>
