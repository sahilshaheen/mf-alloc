# TrueHold — Design spec for Claude Design

## 1. What we are designing

**TrueHold** (repo codename `mf-alloc`) is a private, client-only web app (installable PWA) for Indian retail investors. The user uploads their consolidated account statement (CAMS/KFintech CAS, or NSDL/CDSL CAS). The app shows their *true* asset allocation by looking through each mutual fund to its underlying holdings.

The problem it solves: a "Balanced Advantage" fund with 45% net equity, or an arbitrage fund that is economically cash, is counted as 100% equity by every other tool. TrueHold shows what the money is actually in.

**The one thing the design must make obvious:** *your statement never leaves your device.* Privacy is the product's main trust signal. It should be visible, specific and checkable, not a footer badge.

**Deliverables requested**
- Screens in section 7, at desktop (1440 wide) and mobile (390 wide), in light and dark.
- Design tokens (colour, type, spacing, motion) and a small component sheet.
- The reference sketch (Overview hero) is the aesthetic anchor; see section 4.1.
- A logo, wordmark and app icon for TrueHold (section 4.0).
- The illustration set in section 5, as inline-SVG-friendly vector art.
- Key screens (Welcome, Overview, Funds table) shown in English, Hindi and Malayalam (section 10.1), including the language switcher.

## 2. Audience

| Persona | Needs |
|---|---|
| **Newcomer** (e.g. a salaried investor who started SIPs through an app, doesn't know the term "look-through") | Plain words, one clear next step per screen, reassurance, no jargon without an inline explanation. |
| **Pro** (DIY investor, advisor, finance-literate) | Density, precision, keyboard control, exports, and the ability to verify every number. |

**Design approach: one interface, progressive disclosure.** The default view is calm and simple. Detail is one click or keystroke away and never hidden permanently. Do not build a separate "advanced mode" or an "Expert/Beginner" switch, because users misjudge themselves. Instead:
- Every headline number has an **"How is this calculated?"** popover (plain-language sentence first, then the formula and source rows).
- Tables and charts have a visible density control and a column chooser, which are collapsed by default.
- Jargon terms (*look-through, net vs gross, FoF, notional, AAUM*) get a dotted underline and a short definition on hover, focus or tap.

## 3. Design principles

1. **One screen, one job, one primary action.** A single filled button per view.
2. **Show the answer, then the working.** Headline → chart → table → source rows.
3. **Trust through specificity.** Say "parsed on this device", "as of 31 Aug 2026", "3 funds not matched", not "secure" or "up to date".
4. **Never hide uncertainty.** Unmatched ISINs, stale data and unclassified holdings are shown in the UI with their own colour and a count.
5. **Calm, not cold.** Formal in tone, restrained in colour, a little warmth from paper tones, serif type and small moments of motion.
6. **No advice.** The analysis never suggests an action: no tax-loss harvesting, "book gains before March" or "you should rebalance" language. Returns, XIRR and capital gains facts (realised and unrealised, short- and long-term) are shown descriptively; tax rules must be checked against the current Act and cited, and we show gains, not tax payable. Never use red/green to imply good/bad allocation (red/green for gains and losses is fine). The product describes, it does not judge.

## 4. Visual language

### 4.0 Brand

- **Name:** **TrueHold** (one word, capital T and H). "True" is the look-through allocation; "Hold" is holdings. Never "True Hold" or "TRUEHOLD" in running text.
- **Tagline:** "See what your funds really hold." (welcome headline, share and install contexts)
- **Descriptor:** "Your true asset allocation across mutual funds." Plain statement of use; sits under the wordmark, in the page title and in the install prompt. Avoid the term "look-through" here.
- **Welcome subhead:** "Upload your statement and see what's really inside your mutual funds. It's read on your device and never uploaded."
- **Logo:** a wordmark in the display serif, plus a small mark of a lens over stacked layers. It should work in one colour and stay legible at 16 px. Provide an app icon and favicon.
- **Voice:** "we" for the product, "you" for the user. Plain, specific and calm.

### 4.1 Direction: quiet paper

An ultra-clean, calm, pleasing interface that feels like good paper and good typesetting, and still reads as formal and trustworthy. A reference sketch of the Overview hero accompanies this spec. Treat it as the spirit of the look, not a template: Design is free to change type, tones and layout.

- **Paper tones, with a designed dark mode.** Light mode is soft, slightly cool-grey paper with ink-dark text (the sketch uses a grey-green "bone", deliberately not cream). Dark mode is its own slate-paper sibling, not an inversion and not pure black.
- **Serif for headlines and large figures,** a quiet sans for UI and dense text. Headlines state the finding in a sentence ("53% in equities, 11 points less than your fund categories suggest"), with big serif numerals.
- **One calm column, generous whitespace.** Structure comes from type scale, spacing and thin rules, not from a grid of bordered cards. No heavy sidebar; navigation stays light. Each screen has one main answer that dominates.
- **One signature motif: layered sheets.** The idea of a sheet of paper (what the fund *labels* say) lying over another (what the funds *actually hold*). It shows up as a static comparison on Overview and in the logo and illustrations. It is not a gimmick: the comparison is the product's insight.
- **Avoid:** a generic SaaS dashboard look (rail plus identical bordered cards plus soft shadows), gradient washes, tracked all-caps eyebrow labels, accenting a single word in a headline, and decorative interactions with no function (for example pointer-following effects). We decided against an interactive "lens that follows the cursor" for this reason.

### 4.2 Colour

**Left to Design:** the paper tones, ink, brand/action colour, status colours, and the dark-mode surfaces. Constraints: WCAG AA text contrast, a visible focus ring.

**Asset-class colours: our recommendation (validated; keep unless there is a strong reason).** Each bucket has one fixed colour, used identically in every chart, legend, table chip and illustration layer, and not reused for anything else (including brand and status). The set was run through a colour-vision-deficiency validator on white and a dark navy surface.

| Order | Bucket | Light | Dark |
|---|---|---|---|
| 1 | Equity, domestic | blue `#2a78d6` | `#3987e5` |
| 2 | Debt | orange `#eb6834` | `#d95926` |
| 3 | Cash-like (incl. hedged arbitrage) | aqua `#1baf7a` | `#199e70` |
| 4 | Commodities (gold, silver) | yellow `#eda100` | `#c98500` |
| 5 | Real assets (REITs, InvITs) | magenta `#e87ba4` | `#d55181` |
| 6 | Equity, foreign | violet `#6250d6` | `#9085e9` |
| — | Other / unclassified | neutral grey, hatched; always last | |

- **Keep this order** in stacks and legends. Neighbouring pairs are what was validated; blue next to violet fails.
- If any colour changes, re-validate adjacent colour-blind separation (ΔE ≥ 8) and normal-vision separation (≥ 15).
- Yellow, aqua and magenta are below 3:1 on light surfaces, so every segment carries a visible text label or value, and charts offer a "View as table". Provide a pattern fallback (dots, lines, hatch) per bucket for colour-blind, print and forced-colour modes.
- Text never takes a series colour. Status colours are reserved, come with an icon and text, and never use red/green to judge an allocation.
- **Breakdowns inside a bucket use a light-to-dark ramp of that bucket's own colour** (cap size, sector, rating, maturity), not new hues.

### 4.3 Typography

**Left to Design.** The sketch pairs Newsreader (headlines, figures) with Hanken Grotesk (UI); neither is a requirement. Hard requirements:
- Tabular, lining numerals with right-aligned figures in tables and charts.
- Indian number formatting: ₹ with lakh/crore grouping (`₹12,34,567`, `₹1.2 Cr`), percentages to one decimal.
- Line length under 80 characters.
- **Three scripts, one system.** The type system must cover Latin, Devanagari (Hindi) and Malayalam. Choose or pair faces so the three look like one family at the same optical size, with tabular figures in each. Self-hosted, subset per script, and loaded only for the active language. See section 10.1.
- **All fonts and assets self-hosted.** The app's Content-Security-Policy blocks every origin except its own data CDN, so no Google Fonts or remote images or icons at runtime. Illustrations and icons ship as inline SVG.

### 4.4 Motion: small, charming, never in the way

A little warmth is welcome, as long as it is quick and purposeful.
- **Welcome:** a stamp that settles once ("On this device"); allocation segments that grow in once on first view; tick marks that draw as parsing stages complete; sheets that slide when switching net/gross or opening a drawer; a gentle paper-like settle on toasts.
- **Rules:** transform and opacity only; 120–200 ms for interactions, up to 400 ms for the one-time first-view moments. Never delay or block an action, and any interaction interrupts a running animation. No looping decoration, count-up numbers, parallax or scroll-in effects on every section. Skeletons rather than spinners for downloads. Respect `prefers-reduced-motion` (instant state changes).

### 4.5 Accessibility and charts
WCAG AA contrast, visible focus, full keyboard operation, 44 px touch targets, text that scales to 200%. Every chart has a legend with value, exact values on hover/focus, a "View as table" toggle, a dark variant, and a single axis (never two scales on one chart).

## 5. Illustration direction

**Theme: "looking through."** Layered sheets of paper, and sometimes a lens, revealing what lies beneath a labelled surface. Drawn in a quiet, papercraft-inspired editorial style: flat shapes, soft depth, fine line work, tones taken from the paper palette plus the asset-class colours (a layer that stands for a bucket uses that bucket's colour and nothing else). No people, stock-photo feel, coins or bull/bear clichés. Illustration does the emotional work, so keep it sparing and let the typography lead.

| # | Illustration | Used on |
|---|---|---|
| I1 | **Hero:** a "fund label" sheet over layered sheets, with a lens revealing the strata beneath (static) | Welcome |
| I2 | **Sealed on this device:** a laptop/phone with a closed padlock, a document going in, nothing going out | Welcome, Privacy, Upload |
| I3 | **Statement unwrapping:** a PDF page peeling into layered bands | Processing |
| I4 | **Empty portfolio:** an open folder with a faint outline of the page | Empty states |
| I5 | **Unreadable page:** a page with a magnifier over a smudged line, calm tone | Parse error |
| I6 | **Calendar sheet:** a monthly page with a bookmarked "as of" date | Data & method |
| I7 | **Spot icons:** one per asset class, plus fund, FoF, hedge, option, export, lock | Throughout |

Illustrations are decorative (`aria-hidden`) and must work in light and dark.

## 6. Information architecture and navigation

**Desktop:** light navigation (Overview · Asset classes · Funds · Data & method · Privacy), not a heavy sidebar; a quiet header with the data-freshness chip, net/gross toggle, search/command button, a **language switcher** (EN · हिन्दी · മലയാളം, always shown in its own script), and a persistent **"On this device" stamp** (click → Privacy proof).
**Mobile:** bottom tab bar with the same five items; toggles move into a sticky sub-header.

Before a statement is loaded, only Welcome, Get a statement, Privacy and Data & method are reachable. After loading, the app opens on Overview.

## 7. Screens

For each screen: purpose, content, primary action, states.

### S1. Welcome
- **Purpose:** explain the value in 10 seconds; get the user to upload (or try the sample).
- **Content:** headline ("See what your funds really hold."), one-line subhead, I1 hero, a three-step strip (*1 Get your statement → 2 Open it here, on your device → 3 See your real allocation*), a privacy block with I2 ("Your statement is read in this browser. There is no upload — check it yourself" with a link to S12), and a small teaser: "Category says 71% equity. Look-through says 58%."
- **Primary action:** **Upload statement.** Secondary: **Try a sample portfolio**, plus a text link "How do I get a statement?" (S2).
- **States:** returning user with a locally saved, encrypted portfolio sees "Unlock saved portfolio" (passphrase field) as the primary action instead.

### S2. Get your statement (guide)
- **Purpose:** newcomers don't have the file. Help them get it.
- **Background (why the choice is not "funds vs stocks"):** both statement families can show mutual funds, so the chooser is about what the user holds and what they want from the app.
  - **CAMS/KFintech CAS:** mutual fund folios held outside demat, across all AMCs (either registrar gives the full set). Comes as *Summary* (units, NAV, value per scheme) or *Detailed* (adds full transaction history). No demat holdings.
  - **NSDL/CDSL CAS:** demat holdings (shares, ETFs, bonds, G-Secs, Sovereign Gold Bonds, AIFs, NPS via CDSL, mutual funds held in demat) plus mutual fund folios held outside demat. Holdings only, no transaction history, and only investments where the user is the first holder.
- **Content:** a two-card chooser, then numbered steps for the chosen option, with annotated mock screenshots drawn as simple vector wireframes (not real site screenshots).
  - **Card 1, "I only hold mutual funds" → CAMS/KFintech CAS (Detailed).** Note: this is the only option that carries transaction history, which v1 does not use but later versions may.
  - **Card 2, "I also hold shares, ETFs or bonds in a demat account" → NSDL/CDSL CAS.** Note: it also lists mutual fund folios, so one file is usually enough.
  - A link "I'm not sure" with a one-line rule of thumb: *if you have a demat account, use the NSDL/CDSL statement; if you only invest through fund apps or AMCs, use CAMS/KFintech.*
  - A quiet line that both can be added together (S3 accepts two files) and that overlapping funds are merged (see S6).
  - Password note, per source: CAMS uses the PAN, KFintech uses a password the user sets on the request form, NSDL/CDSL use a PAN-based password. The PDF arrives by email, and must be the original file, not a "print to PDF" copy.
- **Primary action:** **I have my file** → S3.
- **Pro touch:** the copy-able direct request links for each registrar.
- **Open questions (verify against real statements before the parser is built):** whether folio rows in a depository CAS carry ISINs, and whether a CDSL statement includes NSDL accounts (sources conflict). Funds are matched by ISIN with AMFI code or name as fallback, since these fields can be missing.

### S3. Upload & unlock
- **Purpose:** take the PDF(s) and the password.
- **Content:** large drop zone (also click to browse, and paste on desktop), accepts one or two PDFs; each file becomes a row with name, size, a password field (with show/hide) and a status. Persistent reassurance line: "Opened in this browser. Nothing is sent anywhere."
- **Primary action:** **Read statement.**
- **States:** empty · file added, password needed · wrong password (inline, specific message, keeps focus on the field) · reading (S4) · both statements added.

### S4. Processing
- **Purpose:** make the wait feel legible and trustworthy.
- **Content:** I3 plus a real, staged progress list driven by actual work: *Unlocking PDF → Reading transactions → Finding holdings → Matching funds to the latest disclosures → Calculating look-through*. Each stage shows a tick when done. Small text: "Downloading the public fund-data bundle (same for everyone)" with size and version, and a skeleton, not a spinner.
- **Primary action:** none (a quiet Cancel).
- **States:** bundle already cached (stage skipped) · slow network (show bytes downloaded).

### S5. Couldn't read this statement
- **Purpose:** fail loudly and kindly; never guess a holding.
- **Content:** I5, a plain-language headline ("We don't recognise this statement layout"), what we know (statement type guess), what to try (re-download as "detailed", check the file isn't a screenshot), and an **error code and layout fingerprint** in a copyable box with a button **Copy error code to report** (no file contents, state this explicitly).
- **Primary action:** **Try another file.**

### S6. Review what we found (reconcile)
- **Purpose:** let the user confirm the parse before trusting the numbers; surface gaps.
- **Content:** summary line ("14 funds · 3 stocks · 1 ETF · total ₹18.4 L as of 31 Oct"), a compact table of positions with a status chip each: **Matched**, **Matched, data is 2+ months old**, **Not found in our data**. Not-found rows are grouped at the top with a short explanation of the effect ("counted as Other until we have data for it"). Duplicates merged across the two statements shown as a quiet note.
- **Primary action:** **Show my allocation.**
- **States:** everything matched (skip straight to S7 with a one-line toast) · many unmatched (caution banner with the percentage of portfolio affected).

### S7. Overview (dashboard)
- **Purpose:** the answer.
- **Layout:** a single calm column. Headline stating the finding in words, the allocation visual, a typographic legend list, then a few short notes.
  - **Headline:** the finding as a sentence ("53% in equities, 11 points less than your fund categories suggest"), with total value, as-of date and coverage ("96% of value matched").
  - **Allocation visual:** the layered-sheets comparison, static: a muted sheet showing what the fund *labels* say over a coloured sheet showing what the funds *actually hold*. A donut is an optional alternative. Hovering or focusing a segment highlights its legend row and shows the top contributing funds.
  - **Net / Gross toggle** (segmented control, "Net (true exposure)" is the default). Switching animates segment widths within 200 ms. Under it, a one-line explanation. When Gross is on, a delta strip shows how much moved from equity to cash-like because of hedges.
  - **Short notes (max 3, plain language, not cards):** e.g. "Hedged equity: ₹1.4 L of your equity is offset by futures and counts as cash-like." "2 funds hold other mutual funds; we looked through them." "1 fund uses options; shown at notional (flagged)."
- **Primary action:** none forced. Each note links into S8/S9.
- **Mobile:** headline → toggle → stacked sheets → legend list → notes.
- **States:** loading skeleton · sample-data banner ("You're viewing a sample") · partial coverage (caution strip).

### S8. Asset-class detail (drill-down)
- **Purpose:** break one bucket into its Level-2 detail.
- **Content:** tabs or a segmented control per bucket; each has the same structure, a headline value and a breakdown chart, a ranked table, and the funds contributing most.
  - **Domestic equity:** large/mid/small cap split and sector bars (top 10 plus "other", expandable).
  - **Debt:** by issuer type (G-sec, SDL, PSU, corporate, bank), credit-rating ladder, maturity-band histogram.
  - **Foreign equity:** by country/region where known; "unknown region" shown explicitly.
  - **Cash-like, Commodities, Real assets, Other:** a simple composition list.
- **Primary action:** none; the interaction is navigation and hover/focus detail.
- **Notes:** sector/market-cap tags depend on third-party classification, so show a small "Based on AMFI list dated 30 Jun 2026" footnote.

### S9. Funds table
- **Purpose:** the pro-user workhorse and the fund-by-fund view for everyone.
- **Columns (default):** Fund · Value · % of portfolio · SEBI category · Look-through equity / debt / cash-like mini-bar · As-of · Flags. **Optional columns** via the column chooser: gold, foreign equity, real assets, AMC, ISIN.
- **Row flags (icon + tooltip):** FoF · Options exposure · Hedged · Data older than 2 months · Not matched.
- **Interactions:** sort on any column, filter by flag or category or AMC, text search (name or ISIN), multi-select rows to see a combined allocation of just those funds, group by AMC or category. Density toggle (comfortable / compact).
- **Primary action:** clicking a row opens S10 in a side drawer (desktop) or full screen (mobile).
- **States:** no matches for filter · many rows (virtualised) · mobile shows a card list with the mini-bar and flags, and a "Filters" sheet.

### S10. Fund detail (drawer)
- **Purpose:** explain *why* a single fund looks the way it does.
- **Content:** fund name, AMC, ISIN, SEBI category, value in portfolio; **category vs look-through** comparison bars; a short, plain-language "What this fund really holds" paragraph; the exposure breakdown; a "Calculation" accordion (gross as-reported, hedge netting with the example numbers, FoF underlying funds listed with their weights); the as-of date with a stale-data warning if applicable.
- **Primary action:** none; links to the underlying fund (for FoFs) navigate within the drawer with a breadcrumb.

### S11. Data & method
- **Purpose:** credibility. Explain what the numbers are and how fresh they are.
- **Content:** I6; a plain-language explanation of look-through and net vs gross with the worked example (80% shares + 30% short futures → 50% net equity, 30% cash-like arbitrage); a table of fund-data sources (AMC monthly disclosures, AMFI market-cap list, AMFI scheme master) with last-updated date; **freshness** shown per AMC (a heat strip of months); a **known limits** list (month-end snapshots, options at notional, classification lag); a short **Terms** section of plain-language entries (e.g. Regular vs Direct plan: what each is, how the expense ratio differs, and that a distributor provides advice and service; stated neutrally, with no figures meant to persuade); data-bundle version and hash with a **Copy** button.

### S12. Privacy proof
- **Purpose:** turn the claim into something checkable.
- **Content:** I2; the guarantees from the design doc as short, plain statements, each with *how it's enforced* (parsing in the browser, no upload endpoint, identical requests for every user, CSP allows only the data CDN, no analytics, PII discarded at parse time, nothing stored unless you opt in); a **"Verify it yourself"** step list (open DevTools → Network tab → watch while loading a statement: only the data bundle is fetched) with a keyboard-shortcut hint; a live **"Requests made this session"** list showing every network request (URL, size) so users can see it for themselves; links to source code and the reproducible-build hash; the residual-risk note in plain words.
- **Primary action:** none.

### S13. Save & settings
- **Purpose:** optional local persistence and housekeeping.
- **Content:** **Save on this device** toggle (off by default) → passphrase creation with strength hint and a clear "we cannot recover this passphrase" notice; **Forget everything now** (destructive, confirm with a short dialog that lists exactly what will be deleted); **language** (English, हिन्दी, മലയാളം; the choice is remembered on this device only if saving is on, otherwise it follows the browser language), display options (theme light/dark/system, density, number format lakh/crore vs millions), keyboard-shortcut cheat sheet; app version and update status.

### Cross-cutting states and components
- **Empty states** (I4): no statement yet; filter with no results.
- **Stale-data banner:** schemes with holdings data older than two months, showing which ones.
- **Offline:** the app works offline once the bundle is cached; show a quiet "Offline, using data from 7 Nov" chip.
- **Toasts** for copy/export confirmations, 3 s, bottom-centre, no auto-dismiss on hover.
- **Dialogs:** only for destructive actions.
- **Update available** (new data bundle): a non-blocking banner with **Update** (never auto-refresh the numbers under the user).

## 8. Pro-user affordances (scoped to this app)

The app is read-only analysis, so "power" means speed, precision and portability, not configuration.

| Affordance | Where |
|---|---|
| **Command palette** (`⌘/Ctrl K`): jump to a screen, a fund, an asset class; toggle net/gross; export | Global |
| **Keyboard navigation:** `g o` Overview, `g a` Asset classes, `g f` Funds, `/` search, `n` net/gross toggle, `?` shortcut sheet, `Esc` closes drawers | Global, discoverable in the palette and S13 |
| **Sort/filter/group/column chooser, density toggle** | Funds table |
| **Multi-select funds → combined allocation** ("what is my equity inside just these funds?") | Funds table |
| **"How is this calculated?"** on every headline number: formula and the rows behind it | Everywhere |
| **Export:** allocation as CSV, full result as JSON, chart as PNG/SVG, print-friendly view (for sharing with an advisor) | Overview, S8, S9 |
| **Copy value / copy ISIN** on hover or focus | Tables |
| **Raw view:** gross, as-reported numbers beside the net numbers | Net/Gross toggle |

Not in v1: target-allocation setting, rebalancing, alerts, multi-portfolio comparison. Don't design for them yet, but leave room in the layout (e.g. next to the allocation visual) so a "vs. my target" could be added.

## 9. Responsive and platform notes
- Breakpoints: 390 (phone), 768 (tablet), 1024, 1440.
- It is an installable PWA, so design an **app-installed** state with no browser chrome, and an **iOS "Add to Home Screen" hint** shown once, dismissible.
- Touch: no hover-only interactions; every tooltip has a tap equivalent.
- Print stylesheet for Overview and Funds.

## 10. Content and tone
Plain, specific, calm. Short sentences. Explain a term once, in place.
- Prefer: "Your statement is read in this browser. Nothing is uploaded."
- Avoid: "Bank-grade military encryption", "Maximise your returns", "You're over-exposed!"
- Numbers always carry their as-of date. Percentages that don't add to 100 because of rounding get a "rounded" footnote.
- Errors say what happened, what we know, what to do next.

### 10.1 Languages and localisation

v1 ships in **English, Hindi (हिन्दी) and Malayalam (മലയാളം)**. Kerala is expected to be a large user group, and Hindi covers the widest readership; neither should feel like a translation bolted on. Design every screen for all three from the start.

- **Switching:** language switcher in the header (section 6) and in S13, and offered on S1 so a first-time visitor can read the privacy promise in their own language. Language names are always written in their own script. Switching is instant, keeps the user's place, and never reloads or re-reads the statement.
- **Default:** the browser language if it is one of the three, otherwise English. The choice is not sent anywhere and is stored only if the user turned on saving (S13).
- **Text expansion and script height:** Hindi and Malayalam run longer than English and have taller line boxes (Malayalam conjuncts and stacked marks need generous leading). Buttons, chips, table headers and the Overview figures must not clip or truncate at 390 wide. Design with roughly 30-40% extra width and a more open line-height for Indic scripts, and show it in the mock-ups.
- **Numbers:** keep lakh/crore grouping and Western digits (0-9) in all three languages (`₹12,34,567`), as statements and AMC data use them. The compact `₹1.2 Cr` form is kept as is.
- **Dates:** "as of 31 Oct 2026" is localised (month names in the active language), always with the year.
- **Jargon:** the dotted-underline terms (look-through, net vs gross, FoF, notional, AAUM) need a plain translated name plus the English term in brackets on first use, since many Indian investors know the English term from AMC material. Terms with no good translation stay in English transliterated into the script, with the definition popover in the active language.
- **Fund and company names stay as reported.** Scheme names, AMC names, issuer names, ISINs and SEBI category labels are shown in English exactly as in the statement and AMC files; only our own UI text and explanations are translated. Search matches on the English names.
- **Translation approach:** English is the source of truth. Terms are decided once in a glossary (English term, what Indian investors actually say, and a plain explanation) before any screen text is translated. Where people in practice say the English word (e.g. mutual fund, equity, debt, SIP), the UI keeps it, transliterated into the script. Translate a concept only when a natural word exists. Hindi is drafted with AI help; Malayalam drafts are marked unreviewed. The glossary and the privacy copy (S1, S12, the stamp) need a fluent human reviewer before a language ships; until then it is labelled "beta" in the switcher, and S11 has a "Report a wording problem" link.
- **Tone:** the same plain, calm voice as section 10, written natively, not machine-translated word for word. Avoid heavily Sanskritised Hindi and formal "bookish" Malayalam.
- **Privacy copy is the highest priority** for accurate translation: S1 subhead, S12 and the "On this device" stamp must be correct and equally strong in all three languages.
- **Charts and exports:** chart labels, legends, tooltips and the print view are localised; CSV and JSON exports keep English, machine-stable keys and codes.
- **Accessibility:** set the `lang` attribute per element so screen readers switch voices when English fund names appear inside Hindi or Malayalam text. Check that nothing relies on letter-based abbreviations (e.g. "Cr", "L") that do not exist in the other scripts.
- **Out of scope for v1:** right-to-left languages, and other Indian languages. Keep UI strings in a catalogue and avoid layouts that assume English word order or length so more languages can be added later.

## 11. Sample data for mock-ups (illustrative, not real)

Portfolio total ₹18,42,300 as of 31 Oct 2026.

| Fund (fictional names) | Value | SEBI category | Net equity | Debt | Cash-like | Gold |
|---|---|---|---|---|---|---|
| Orchid Flexi Cap Fund | ₹4,60,000 | Flexi cap | 94% | 0% | 6% | 0% |
| Harbour Balanced Advantage Fund | ₹3,10,000 | Balanced advantage | 45% | 22% | 33% | 0% |
| Meridian Arbitrage Fund | ₹2,40,000 | Arbitrage | 0% | 12% | 88% | 0% |
| Kestrel Corporate Bond Fund | ₹3,00,000 | Corporate bond | 0% | 97% | 3% | 0% |
| Summit Nifty 50 Index Fund | ₹2,50,000 | Index | 99% | 0% | 1% | 0% |
| Lantern Gold FoF | ₹1,20,000 | FoF (gold) | 0% | 0% | 2% | 98% |
| Globe US Equity FoF | ₹1,62,300 | FoF (overseas) | 0% | 0% | 3% | 0% (97% foreign equity) |

Include one fund with the "Data older than 2 months" flag, one "Not found in our data" position, and one FoF with a drill-through, so every state appears in the mock-ups.
