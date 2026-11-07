# Client: decisions and status

Working log for the `client/` build, kept so work can resume in a fresh session. The Claude Design boards
are the visual reference, but where this file disagrees with them, this file wins. Update it when a
decision changes.

## Where things stand

Built: i18n (en, hi, ml), shell and header, statement parser (CAMS Summary), bundle loader and ISIN join,
Welcome (upload and password), Overview, Data and method (short, with cited sources). Funds, Asset classes
and Privacy are placeholders.

Next, in order: Funds table and fund drawer, Privacy, Asset classes, then the rest of the
Welcome design, mobile polish of the new screens, dark-mode toggle, PWA, export.

Run: see the root README. Check a change in a browser at 390, 768, 1024 and 1440 px, in English and
Malayalam (longest strings), with the redacted statement.

## Working agreements

- Commit at stages without asking; end messages with the Claude attribution line. Commit with
  `git commit -F <file>` (an email in the attribution can trip a commit hook when passed inline).
- Test-first for logic; lean tests. Run `npm test`, `npm run lint` and `npx tsc -b` in `client/` before each commit.
- Do not hand-write manifests; add packages with `npm install`.
- Edit files that contain Hindi or Malayalam with the edit tools or a script file run as
  `python3 -X utf8 script.py`; piping non-ASCII through a shell heredoc failed here.
- Check UI in a browser: start `npm run dev -- --port 5173 --strictPort` in `client/` (the bundle must be in
  `client/public/data/`), open `/welcome`, upload `tools/redact/cas-redacted.pdf` (git-ignored, real
  holdings, never commit) with password `Fixture@123`. A page reload drops the loaded statement, so use
  in-app navigation or upload again. Playwright screenshots must be saved under the repo.
- `.github/`, `deploy/` and `docs/fetching-statements.md` belong to someone else; leave them untracked and untouched.
- Say plainly when something was not verified, and do not claim a number is right without a source.

## Decisions

**Stack.** Vite, React 19, TypeScript, `react-router`, plain React state. No UI or i18n library.

**i18n.** Hand-rolled typed dictionary. `hi` and `ml` must define every key `en` does, enforced by the
type. Hindi and Malayalam text is machine-drafted and needs review by fluent speakers.

**Privacy.** The statement is parsed in the browser. The PDF is never uploaded, and the only network
requests are for the app and the exposure bundle. The Privacy screen must state exactly this and
nothing it can't prove.

**Statement parser.** CAMS Summary only. Rows are anchored on ISINs, so the layout can vary. It fails
loudly if a row's units × NAV disagrees with its value, or if the rows don't sum to the printed total.
Other statement types are rejected with a clear message. The redacted real statement is not committed
(its holdings are real), and the integration test skips when the file is absent.

**Net and gross.** Net counts hedged equity as cash-like. Gross is as reported. Funds missing from the
bundle sit in the "Not classified" asset class (internally the `other` bucket, which also holds anything
the pipeline could not classify) and as "Not in our data" under Level 1. They are never called "Other",
because we do not know what they hold.

**No comparison narrative.** We do not compare "what labels say" with "what funds hold". The labels give
only floors, so the comparison depended on an arbitrary choice of which labels count as equity. The
Overview has two separate levels:

- **Level 1, fund categories:** how SEBI files each fund, plus the equity those categories require at
  least (the floors below).
- **Level 2, look-through:** what the funds actually hold. This is the headline.

**Fund categories and floors.** Source: SEBI circular HO/24/13/15(2)2026-IMD-RAC4/I/5764/2026, 26 Feb 2026,
clause 2.6.3 (sources on the Data and method screen). Implemented in `client/src/portfolio/fundCategory.ts`.

- Equity floors: Multi Cap 75%, Large & Mid 35% + 35% (70%), Large Cap, Dividend Yield, Value, Contra,
  Focused, Sectoral, Thematic and ELSS 80%, Mid Cap, Small Cap and Flexi Cap 65%.
- Hybrid floors are the lower end of each stated range: Aggressive 65%, Balanced Hybrid 40%,
  Conservative 10%. Equity Savings uses its stated net equity floor of 15%.
- Arbitrage, Dynamic Asset Allocation (balanced advantage) and Multi Asset have no equity floor that
  survives hedging or allocation, so they count as 0.
- Index funds and ETFs must hold 95% in their index. Vague AMFI categories are read by fund name.
- Fund-of-funds and overseas funds are "Other Schemes" with no equity floor.
- Mapping uses AMFI's category text, not each scheme's offer document. A few funds may sit in a
  different SEBI category than AMFI shows.

**What the data shows and why.** Equity funds may hold the rest in money market, gold and silver, and
InvITs (clause 2.6.3.3). Cash and REIT lines inside equity funds were traced to source disclosures and
are real, not pipeline bugs. Whether REITs count as equity-related from 1 Jan 2026 comes from secondary
summaries only. It is not confirmed against SEBI's own circular.

**Naming.** "Level 1" and "Level 2" are client terms: Level 1 is fund categories, Level 2 is look-through.
The pipeline's per-holding labels are called asset-class buckets, so the two do not clash.

**Data and method.** Short on purpose: what each level is, known limits, and numbered sources with links. Detail
lives in the code, which readers can audit and dispute. Every claim on it must have a source in the list or be
checkable in the repository. Add a source whenever a new rule is added.

**Layout.** Compact header below 1180px (nav scrolls, language switch on its own row on phones); content
column is 960px. Controls must grow with their text and never use fixed heights that long Malayalam or
Hindi can overflow. Hide text that does not fit with a container query instead of clipping it.

## Open items

- Notes section on Overview (hedged funds, look-through, options), colour-blind pattern option, stale-data
  flags per scheme.
- `formatDate` prints "Sept" for September in English.
- Unsupported: NSDL and CDSL CAS, CAMS Detailed.
- Header is wider than the content column above 1180px. Deliberate, easy to change.
- The Overview caption lists tiny contributors (₹6, ₹1) next to a large gap. They are unresolved fund units
  (`unresolved_fund_units` flag: a fund holds a sliver of other funds the pipeline could not trace). Better:
  hide contributors under a small share of the bucket, or show "and N others".
- On phones the nav scrolls sideways and the active item can sit partly off-screen.
- The new Overview was checked in English (1440, 390) and Malayalam (390) only, not Hindi.
- Whether REITs count as equity-related from 1 Jan 2026 rests on secondary sources, not the circular.
- AMFI category text, not each scheme's offer document, decides its SEBI category.
