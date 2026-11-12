# Client: decisions and status

Working log for the `client/` build, kept so work can resume in a fresh session. The Claude Design boards
are the visual reference, but where this file disagrees with them, this file wins. Update it when a
decision changes.

## Where things stand

Built: i18n (en, hi, ml), shell and header, statement parsers (CAMS Summary; CAMS Detailed, not yet run on a real file), bundle loader and ISIN join,
Welcome (hero, steps, sealed section, upload and password), Overview, Data and method (short, with cited sources), Funds (table, search,
fund detail panel at `/funds/:isin`), Returns (`/returns`), Privacy, Breakdowns (`/breakdowns/:bucket`).

Next, in order: the rest of the
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

## Agreed plan (12 Nov 2026)

In order. Phase 1 is done; the rest is not started.

1. **Pipeline correctness** (done): overseas funds as foreign equity, sector fallback for quant, CDMDF as debt,
   category plausibility checks, override candidates. Still open: run October 2026 and add a month-over-month diff.
2. **Information architecture.** Nav becomes Overview, Allocation, Funds, plus an About dropdown (Get your
   statement, Data and method, Privacy); Save and Open another move to a statement menu in the header.
   Overview becomes a true overview (value, invested, gain, return or XIRR; look-through bar; equity makeup; top
   funds and contributors; data-quality line). Allocation is Breakdowns renamed and takes Level 1 and the full
   asset-class table. Returns merges into Funds as a Holdings/Returns column switch; `/returns` redirects.
3. **Data visualisation** with d3 (added with `npm install`; d3 computes scales and shapes, React renders):
   interactive strata bar, Net/Gross morph with a callout, contribution chart, in-cell bars.
4. **Motion**: staged progress while reading, bundle skeleton, first-render grow-in, route cross-fades, all under
   the reduced-motion rule.
5. Checking the Detailed parser on a real statement is the owner's job, not part of this plan.

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

**Detailed statement parser.** `statement/camsDetailed.ts`, chosen when the PDF has an "Opening Unit
Balance". Its layout comes from casparser's description of CAMS Detailed statements (MIT,
codereverser/casparser), not from a real file: casparser's test PDFs are encrypted, and no public sample
was found. Lines are rebuilt from pdf.js items; numbers go to the Amount, Units, Price or Unit Balance
column whose header right edge is nearest, so pdf.js item widths are needed. It fails loudly if units don't
add up to each printed running balance or the closing balance, or units × NAV disagrees with the market
value. Closed schemes keep their transactions but give no holding. Checked so far only on unit tests and
a synthetic PDF built to the same assumed layout; **run it on a real redacted Detailed statement before
relying on it**, and fix the fixtures to match.

**Returns.** Gain and absolute return use the statement's cost value. XIRR (Detailed only) treats
purchases, SIPs, switches in, stamp duty, STT and TDS as money in; redemptions, switches out, reversals
and IDCW payouts as money out; reinvested IDCW as neither. Switches cancel in the portfolio total. A fund
held before the statement period has no XIRR (unknown cost). Under a year, only the gain is shown.
The explanations of Invested, Return, XIRR and Contribution sit in `InfoTip` tooltips next to those terms, not as
paragraphs on the page; only the situational note about funds held before the statement starts is a footnote.

**Capital gains facts (not built; rules for when it is).** Units of an equity-oriented fund bought before
1 Feb 2018 have a grandfathered cost: the higher of actual cost and the lower of (fair market value on
31 Jan 2018, sale value). Income-tax Act, 2025, s.90(7); fair market value for an unlisted unit is its NAV on
31 Jan 2018, s.90(8)(b)(iii) (read from a reproduction of the Act; the official site refused the fetch, so
re-check against incometaxindia.gov.in before shipping). The NAVs are in the pipeline's
`nav-2018-01-31.json`, by ISIN, from AMFI's NAV history report for that day (three spot-checked against
mfapi.in). It is never applied by guess, and every gain it cannot apply to says so next to the figure:
- **ISIN not in the file** (a scheme merged or changed ISIN since 2018, or the file dropped it as malformed
  or conflicting): no grandfathered cost; the gain is shown on actual cost and marked "31 Jan 2018 value
  not available for this fund".
- **ETFs and other listed units**: the Act uses the exchange's highest price on 31 Jan 2018, which we do not
  have; same marking.
- **"Equity-oriented"** is a tax test on what the fund holds, not its SEBI category; a fund whose category does
  not settle it (hybrids, fund-of-funds) is marked rather than assumed.
- A standing note on the page: these are facts from the statement and published NAVs, not tax payable, and
  the user's own tax filing may differ.

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
- A fund whose name says gold, silver, bond and the like gets no equity floor even under an equity index category: AMFI files ABSL's gold and silver ETFs under "Equity ETF".
- Mapping uses AMFI's category text, not each scheme's offer document. A few funds may sit in a
  different SEBI category than AMFI shows.

**What the data shows and why.** Equity funds may hold the rest in money market, gold and silver, and
InvITs (clause 2.6.3.3). Cash and REIT lines inside equity funds were traced to source disclosures and
are real, not pipeline bugs. Whether REITs count as equity-related from 1 Jan 2026 comes from secondary
summaries only. It is not confirmed against SEBI's own circular.

**Naming.** "Level 1" and "Level 2" are client terms: Level 1 is fund categories, Level 2 is look-through.
The pipeline's per-holding labels are called asset-class buckets, so the two do not clash.

**Data and method.** Follows the design board: hero with the calendar scene, worked net-versus-gross example, the
category explanation (Level 1), a data-sources table, a table of fund houses covered, known limits, a Terms entry
(Regular and Direct plans, stated neutrally), numbered sources with links, and the data-bundle version and hash
with Copy. Every claim must have a source in the list or be checkable in the repository; add a source whenever a
new rule is added. Differences from the board, on purpose: the board's month-by-month freshness strip is a
coverage table instead (the bundle has one date per scheme, not a history); AMFI list dates show "—" because the
bundle does not record them; disclosures are described as including futures only, because options are not parsed.

**Illustrations and icons.** The six scenes from the Illustrations board are React components in
`client/src/illustrations/` (Hero, Sealed, and in Scenes: Processing, EmptyPortfolio, Unreadable, Calendar), built
on theme variables so dark mode is free, with per-instance SVG ids. Used on: Welcome (Hero; Processing while
reading; Unreadable for unreadable or unsupported files; Sealed), Privacy (Sealed), Data and method (Calendar),
Funds search with no match (EmptyPortfolio). The favicon is the board's hand-tuned 16 px mark with a dark-mode
variant. Not yet used: the bucket spot icons (I7) and a PWA/app icon (needs PNGs; with the PWA work).

**Funds.** Rows are merged by ISIN (several folios of one fund become one row), sorted by value until a column header is clicked. The Net/Gross
choice lives in the portfolio context, so Overview and Funds share it. The design's "category says vs
look-through says" bar is replaced by the SEBI category line and its stated equity minimum (or "SEBI states no
minimum"), then the look-through bar and a table by asset class for the selected view only (the panel follows the Net/Gross
toggle; it never shows both at once). The bundle has no per-holding
data, so the calculation shows only what the gross and net vectors support. Flags: hedged (gross equity
exceeds net by more than 0.5% of the fund), hedge of unpublished size (`hedge_notional_missing`: Net equals Gross for that fund), partial look-through (more than 0.5% of the fund left in `fund_unit`; the pipeline's flag is not used because it fires on any amount), not in our data,
and holdings more than two months older than the statement date. Categories are shown without AMFI's scheme-family prefix (`categoryLabel`), since AMFI spells it two ways.
Per-fund breakdown in the panel: the look-through bar is interactive. Selecting an asset-class segment zooms it
(the segment grows to fill the bar and the others collapse, 200 ms, with the parts fading in; "← All asset
classes" reverses it). Domestic equity offers market cap or sector, shown as shares of the equity the fund holds
(they add up to 100%), with rupee amounts, and the bar shows the top six sectors plus one merged segment while
the list shows every sector. All other asset classes zoom too and say "no further breakdown yet, coming".
Cap and sector are gross, before hedges, so they do not follow the toggle (the panel says so). Logic and tests:
`schemeBreakdown` in `portfolio/breakdownModel.ts`.

Deferred from the design: row selection with an aggregate bar, Category/AMC/Group filters, Columns and density
controls, the holdings-as-of column, CSV export, AMC display names (the bundle holds only AMC codes), and the
mobile card layout (phones show name, ISIN, value, return and flags only).

**Privacy page.** Every claim on it is something the code does today, checked by reading the code and by
inspecting the page's own request list in a browser (all requests same-origin, none carrying the file).
It says: the PDF is read in the browser; the only network request in the code is a plain download of the
public fund data; the data is identical for everyone; no analytics or third-party resources; the app keeps
fund name, folio, ISIN, units, NAV and value in memory and not name, PAN or address; nothing is stored on the
device unless the user chooses "Save on this device" (see below). It deliberately does not claim, because they
are not true or not built yet: a content-security-policy (one exists in untracked `deploy/_headers` but is not
confirmed live), a reproducible-build hash, and discarding folio numbers (they are kept in memory and, if the
user saves, in the encrypted copy).
The live request list reads `performance.getEntriesByType('resource')`; sizes are body sizes, and request
bodies cannot be shown, so the page does not claim to show them. Re-check these claims whenever storage, a
service worker (PWA), analytics or any new network call is added.

**Save on this device** (`/save`, optional, off by default). Stores the parsed statement (the same fields the
app keeps in memory, never the PDF, never name, PAN or address) in `localStorage` under `truehold.saved`,
encrypted in the browser: PBKDF2-SHA-256 (600,000 iterations, random salt) derives an AES-256-GCM key from the
user's passphrase (minimum 8 characters, entered twice); a random IV per save. The save date is stored
unencrypted, and the page says so. There is no recovery: a forgotten passphrase means opening the PDF again.
On a visit with a saved copy, Welcome asks for the passphrase and rebuilds the portfolio by joining the saved
holdings to the current fund-data bundle, so a restored portfolio reflects newer fund data. "Open another
statement" (`/welcome?new`) re-uploads a PDF; the saved copy changes only when the user replaces or forgets it.
Logic and tests are in `portfolio/savedStatement.ts`. Checked in a browser: the stored text holds no ISIN, fund
name, folio or amount; a wrong passphrase is refused; the right one restores the same totals; Forget empties
storage. The Privacy page's "nothing is stored" promise now reads "unless you ask". Re-check it if the saved
fields ever change.

**Breakdowns** (renamed from "Asset classes": the page holds more than asset classes). One tab per asset class at
`/breakdowns/:bucket`, following the Net/Gross toggle. Domestic equity adds market cap (large, mid, small, size not
known) and sector (top 10, expandable); clicking a group lists the funds behind it. Every tab lists the funds
behind that asset class. Market cap and sector are **gross only**: the bundle's cap and sector weights sum
exactly to each scheme's gross domestic equity, so they do not follow the toggle and the page says so
(scaling them to net would assume hedges are spread evenly, which is a guess). Sector names are shown as the
data has them, in English. Not available because the pipeline does not collect it yet: debt quality, issuer type,
maturity, foreign equity by country (shown as "no further breakdown yet", and listed on Data and method).
Fund names here are not links yet (contributors carry no ISIN).

**Navigation.** Before a statement is open the header offers Open statement, Get your statement, Data and method and Privacy; the portfolio screens (Overview, Breakdowns, Funds, Returns) appear only once one is open, since they redirect to `/welcome` without it. The guide asks for the Detailed statement (Specific Period from 01-Jan-1990, with zero-balance folios) and says Summary works without XIRR.

**Funds return column.** Return (gain over the statement's cost value) with the rupee gain beneath, from
`returnsModel`, so it matches the Returns screen. XIRR stays on Returns.

**Overview bar.** Facts on the left as plain text (portfolio line, then fund-data date); the two actions (Save on
this device, Open another statement) on the right as matching outlined buttons of equal weight.

**Tables.** Data tables (Funds, Returns) sort by clicking any column header (`SortableHeader`, `sortRows`):
text columns start A to Z, numbers largest first, a second click reverses, and missing values always sort last.
Funds' look-through column sorts by equity share (domestic + foreign).

**No advice disclaimer.** The "Describes your portfolio. It doesn't give advice." line was removed everywhere at
the owner's request.

**Layout.** Compact header below 1180px (nav scrolls, language switch on its own row on phones); content
column is 960px. Controls must grow with their text and never use fixed heights that long Malayalam or
Hindi can overflow. Hide text that does not fit with a container query instead of clipping it.

## Motion and interaction

Minimum in place: side panels (fund detail on Funds, funds-behind on Breakdowns) share one `SidePanel`
component and slide in from the right over 200 ms (a full-width sheet below 1100 px); every clickable item
gets the `--hover` background shade with a 120 ms fade (rows, tabs, nav, buttons, legend rows); whole Funds rows
are clickable, not only the name. Reduced motion turns it all off (global rule in `base.css`). Panels animate in
only; closing is instant. Use the tokens (`--dur-*`, `--ease`) for anything new, transform and opacity only.

Ideas to try later (unbuilt, none promised):
- Close animation for panels (slide out, then unmount).
- Numbers on the Overview count up once on first view, and segments grow in (`--dur-first`, once).
- The logo's lens sweeps across the "looking through" bar when the Net/Gross toggle flips.
- Shared-element move: a fund row's look-through bar glides into the panel's bar when it opens.
- Cap and sector bars slide to their new widths when you switch tabs or flip Net/Gross.
- Hovering a fund in the table highlights where its money sits in the Overview strata.
- The "On this device" stamp settles into place on first load, then stays still.
- Soft cross-fade between routes.

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
- Confirm `deploy/_headers` (CSP with `connect-src 'self'`) is what is deployed, then add the CSP promise to the Privacy page.
- Whether REITs count as equity-related from 1 Jan 2026 rests on secondary sources, not the circular.
- AMFI category text, not each scheme's offer document, decides its SEBI category.
