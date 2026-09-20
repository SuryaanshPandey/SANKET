# SANKET redesign: audit and structured prompt

## Blunt verdict first

Two things in your request need pushback.

1. **"Redesign the whole frontend without breaking anything" in one prompt is a contradiction.** A one-shot full rewrite by an AI agent is the fastest way to break the graph, the map, or the workflow canvas. The prompt below is built as a phased, gated migration: tokens first, then shell, then pages, riskiest last.
2. **Your worst problems are not visual.** In a forensic tool, showing **90% confidence** on the same name ("S. Sabinbuddin Monda?") extracted as complainant, accused, victim and investigating officer is a trust failure. No palette fixes that. I list these separately below, because the redesign must not paper over them.

## Part 1: Audit

### A. Palette and colour mistakes

- **Too many hues with no system.** Teal, green, amber, red, purple, blue, orange and yellow all appear. The workflow node palette gives every node type a different icon colour (blue, purple, yellow, red, orange, green) with no meaning behind it. Colour should carry meaning, not decoration.
- **Semantic colours are diluted.** Green "90%" pills appear on every row, so green stops meaning "good". Red is used for a KPI, a full card tint and a badge, so it stops meaning "urgent".
- **Low-contrast secondary text.** Grey-on-navy at 9–11px (sidebar group labels, the "5 documents in case" indicator, descriptions inside workflow nodes, "BBOX" tags) looks well below WCAG AA 4.5:1. I'm estimating this by eye, so verify with a contrast checker.
- **Blue-black background with teal glow.** It reads as "hacker terminal", not "evidence you would defend in court". It also clashes with the scanned documents, which are white paper images dropped onto a dark shell.
- **The Contradictions card is tinted red-brown across the whole surface.** It is heavy and muddy. A neutral card with a red left edge and a red icon is enough.
- **Graph node colours don't match the legend.** The legend lists Person, Officer, Witness, Asset and Event, but the canvas shows grey and red nodes that appear nowhere in it.
- **Map marker colours are decorative.** Four colours with no key.

### B. Typography

- Micro-labels are 9–11px monospace, uppercase, with wide letter-spacing, applied to everything. This is the biggest readability problem in the app.
- Monospace is used for headings, labels, buttons and IDs alike, so it stops signalling "this is a code or identifier".
- Button casing is inconsistent. "RUN WORKFLOW / RESET / DELETE" are uppercase and large, while other pages use sentence case.
- Raw system keys are exposed to users: `party:complainant/informant_1`, `date:Date of FIR Registration/Reporting`, bbox `12,354,678,10`, and a GUID-style provenance ID.

### C. Layout and information architecture

- **The chrome eats the screen.** The header plus the always-on document strip take about 140px before any content. The strip appears on pages where it does nothing (Locations, Entity network, Workflow, Quality).
- **The document count appears three times:** "5 documents loaded", "5 source documents" and "5 documents in case".
- **Every page has a double heading.** For example "Quality & analytics" is followed by "Quality & analytical signals", each with its own eyebrow and description. Overview does the same with "Everything important, kept together." This is marketing copy in an operational tool.
- **Sidebar badges are inconsistent.** Some are numbers, Ledger is the text "FIELDS", and "1" on Evidence review looks identical to an informational "5" on Overview. Attention counts and informational counts should look different.
- **Cards stretch to fill height with almost nothing in them.** Case summary on Overview, Contradictions on Evidence review, and the huge empty pane above the document scan in Document inspector.
- **The Next.js dev badge overlaps the sidebar footer and the graph legend.**

### D. Screen-by-screen

- **Overview:** the Case summary is one concatenated string, and the "Remembered entities" names include role fragments ("Casualty Medical Officer: Aims, New Delhi"). The four KPI cards have equal weight, so "12 Needs review" is red while its caption says "1 conflict".
- **Entity network:** labels collide into unreadable text, nodes sit in a rigid grid although "Force" is selected, and almost no edges show. Sentences like "Extracted via forensic heuristi…" appear as entities. The legend is overlapped by the dev badge.
- **Locations:** the map is watermarked "API KEY REQUIRED / carto.com/basemaps/apikey" across the whole surface, so the map is effectively broken. The list panel covers the map and collides with the zoom buttons. Only 3 of 4 markers are visible, and the markers are tiny.
- **Workflow:** the canvas clips at the right edge, and the "Scoped execution / Evidence trace / Reproducible flow" chips float awkwardly over the tab strip. Delete sits directly beside Run with no separation. "READY" is shown on every node, which is noise for a default state. Node descriptions are about 9px.
- **Ledger:** 
  - The same filename and "Fir Report" pill repeat on every row.
  - All 74 rows show an identical 90% pill, so the confidence column carries no information.
  - Empty values show "—" at 90% confidence, and "0.00" for a stolen-property amount.
  - The row action is a heavy bordered icon box repeated per row.
  - Long text breaks row rhythm.
- **Document inspector:** the scan is small and pushed to the bottom of a large empty area, and it is cropped. "SHA-256" looks like an action button but is information. Pass/fail states rely on text only, with no icon or colour.
- **Evidence review:** the badge says "2 open" but one contradiction is visible, so verify whether there is a scroll or clipping issue. There are no resolution actions on a review queue (no "mark reviewed", "choose canonical value", "add note"). The huge circular "OBSERVED" stamp is out of scale.
- **Quality & analytics:** the coverage bars are far from their labels (about 300px gap), and every bar is 80–90%, so they are hard to tell apart. There is no threshold marker, although the 85% review threshold is the whole point. "Observed role mix" is seven rows that all say "1". The lower cards are cut off, and two buttons duplicate the sidebar navigation.

### E. Functional and data bugs the redesign must NOT hide

These need fixing separately. The prompt tells the agent to report them, not silently patch them.

1. Map tiles need an API key. This is config, not design.
2. Entity network layout isn't applying, and junk sentence-entities are being created.
3. Confidence is over-reported. The same person is assigned to 4 roles at 90%, and empty fields are also at 90%.
4. Counts disagree across screens: 
   - Entities: 12 (Overview and sidebar) vs 32 (Entity network).
   - Conflicts: 1 (Overview, Quality) vs 2 (Evidence review).
   - Records: 71 (Evidence review) vs 74 (Ledger, Quality).
   - Overview's "12 Needs review" vs "1 conflict".
5. The Document inspector scan is mispositioned, which is a layout bug.
6. The Workflow canvas clips its right-hand nodes.

## Part 2: Design direction (what "creative and minimal" means here)

- **Minimal:** one accent colour, neutral graphite surfaces, borders instead of glows, and quiet defaults that are loud only for exceptions.
- **Creative, with a purpose:** a single signature idea, the "evidence thread". Every value with provenance carries a small source chip (`01 · p1`) that previews the scan region on hover, and confidence appears as a thin indicator, not a pill. That is distinctive, and it directly serves your product promise ("source-linked, traceable").
- **Confidence logic:** at or above threshold it is a muted number, between 85 and 89 it is amber, and below 85 it is red. This is the "exception-loud" rule that fixes the sea of identical green pills.

## Part 3: The redesign prompt

Paste this into Claude Code or Cursor with repo access, and attach the 8 screenshots. Run one phase at a time (see Part 4).

```
ROLE
You are a senior product designer and senior frontend engineer. You are redesigning the presentation layer of SANKET v2.0, an evidence-intelligence web app for forensic/police case analysis (case memory, entity graph, map, investigation workflow, evidence ledger, document inspector, evidence review, quality analytics). Users are investigators and analysts working long sessions; trust, legibility and traceability matter more than decoration.

OBJECTIVE
Redesign the entire frontend to be visually appealing, creative, professional and minimal, with ZERO functional regressions. This is a presentation-layer refactor only.

HARD CONSTRAINTS (THE "DO-NOT-BREAK" CONTRACT)
1. Do not change: routes/URLs/query params, data fetching, API contracts, state stores/hooks, component public props/exports, event handlers, business logic, graph/map/workflow engine behaviour, CSV export, "Graph Contract" export, SHA-256 display/logic, keyboard shortcuts.
2. Preserve every existing id, name, aria-label, data-testid and CSS hook that tests, analytics or scripts may rely on. Search for them before renaming anything.
3. Preserve all user-facing legal/analytic disclaimers (e.g. "Analytical signals are leads and validation evidence, not legal conclusions") - restyle only.
4. No new heavy dependencies. Reuse the existing UI library, icon set and charting/graph/map libraries. A font (Geist or Inter + a mono) is the only permitted addition. Keep the bundle size within +5%.
5. If a design change would require touching logic, STOP, describe it, and continue with the rest. Never "fix" logic silently.
6. New UI (e.g. resolution actions) may only be added if it can be wired to an EXISTING handler; otherwise omit it and list it under "Proposed features".
7. Everything ships behind a flag (NEXT_PUBLIC_UI_V3 or equivalent) until visual parity and QA pass, so the old UI remains one toggle away.

WORKING METHOD - PHASES WITH GATES
Complete ONE phase per session. At the end of each phase, run type-check, lint, unit/e2e tests and a production build, then output the phase report (files changed, before/after notes, risks, bugs found but not fixed). Do not begin the next phase until told to.

Phase 0 - Discovery and baseline (NO code changes)
- Read package.json and the app structure; identify framework, styling system, component library, graph/map/workflow libraries, table implementation, test setup.
- Write an inventory: every page, shared component, design token/colour currently in use, and every test selector.
- Capture Playwright baseline screenshots of all 8 screens (Overview, Entity network, Locations, Workflow, Ledger, Documents, Evidence review, Quality & analytics) at 1920x1080 and 1440x900 using the built-in "Load Forensic Police Dossier - 5" demo case.
- Produce a "Bugs and inconsistencies found" list (see REPORT-DON'T-FIX list below).

Phase 1 - Design tokens and typography (no layout change)
Phase 2 - App shell (header, sidebar, source-scope bar, page header pattern)
Phase 3 - Shared primitives (buttons, chips, cards, KPI, table, tabs/segmented, dialog, tooltip, empty/skeleton/error states, copy-to-clipboard chip)
Phase 4 - Pages, lowest risk first: Overview, Quality & analytics, Ledger, Evidence review, Document inspector, Locations, Entity network, Workflow
Phase 5 - Accessibility, responsive pass, visual-regression sign-off, cleanup of dead styles

DESIGN SYSTEM
Principles: quiet by default, loud for exceptions; one accent; colour means status, never decoration; no glows/gradients/neon; borders and spacing create hierarchy; every number and value is traceable to its source.

Colour tokens (dark theme first; define semantic CSS variables so a light theme can be added by remapping):
- bg-canvas #0B0D10 | bg-surface #111418 | bg-raised #171B20 | bg-overlay #1D2228
- border-subtle #222831 | border-default #2C333C | border-strong #3A424D
- text-primary #E8EBEF | text-secondary #A3ACB7 | text-tertiary #7C8692 | text-disabled #565F6A
- accent (single brand colour, desaturated teal): accent-text #4FD1C0 | accent-solid #14B8A6 (text on it #04211E) | accent-subtle rgba(45,212,191,0.10) | accent-border rgba(45,212,191,0.35)
- status (ONLY for status): danger #F0686A | warning #E5A83A | success #4CC38A | info #6AA6F8, each with a 10% background tint and a 35% border tint
- entity categories (always paired with a distinct SHAPE, never colour alone): person #9AA5F5 circle | officer #4FD1C0 shield/hexagon | witness #7FD6A0 ring | asset #E5B85C diamond | event #A3ACB7 square | location #6AA6F8 pin
- Confidence scale: >= threshold = muted numeric text (no pill); 85-89 = warning; < 85 = danger. Threshold comes from the existing config value (85).
- Verify WCAG AA: 4.5:1 for text, 3:1 for UI components and focus rings. Adjust values if any pair fails and report it.

Typography: Geist Sans (or Inter) for UI, Geist Mono / JetBrains Mono ONLY for IDs, case numbers, hashes, bounding boxes and raw extracted values.
Scale: 12 / 13 / 14 / 16 / 20 / 24 / 32; weights 400/500/600; line-height 1.5 body, 1.25 headings. Minimum text size 12px anywhere. Remove all-caps + wide-tracking monospace from labels; sentence-case 12px medium in text-secondary. Uppercase eyebrows only at page level, 11px, 0.06em tracking, max one per page. Buttons: sentence case everywhere.

Spacing/shape/elevation: 4px grid (4/8/12/16/24/32/48). Radius 6 (controls), 10 (cards), 999 (chips). 1px borders, no shadows except overlays/popovers. Motion 120-180ms ease-out; honour prefers-reduced-motion; no decorative animation.

Signature element - "Evidence thread": any value with provenance shows a compact source chip ("01 · p1"), which on hover/focus previews the source region with its bounding box highlighted and offers "Open source". Confidence is a thin 2px indicator/underline or small ring plus the number. Use the same chip component on Ledger, Overview entities, Evidence review and Document inspector.

APP SHELL
- Header 56px. Left: SANKET wordmark with "v2.0" as a tertiary tag. Then Case ID (mono) with the case title in text-secondary. Right: single status line ("5 documents - Local inference"), case/dossier selector, "Ingest evidence" as the only primary button. Remove duplicated "5 documents ..." indicators (keep exactly one).
- Sidebar 232px, collapsible to a 64px icon rail (persist the choice). Group labels 11px text-tertiary. Badges: informational counts neutral; attention counts (Evidence review) use a danger-subtle dot/pill. Ledger shows its record count, not the text "FIELDS". Active item: accent-subtle background + 2px accent left bar.
- Document strip: keep the existing selection state/logic, but restyle as a compact 40px "Source scope" bar (chips with truncated filename, doc-type and a single flag indicator), and render it only on document-scoped pages (Documents, Ledger, Evidence review). On Overview, Entity network, Locations, Workflow and Quality it is hidden or collapsed to a single "All sources" control. Verify no page depends on it being mounted.
- Page header pattern (every page): one H1 (24/600), one description line (14, text-secondary), actions right-aligned on the same row. Delete the duplicate H2 + eyebrow + description blocks and marketing copy ("Everything important, kept together.") - keep any functional text.
- Hide framework dev overlays (Next.js badge) outside development; ensure the sidebar footer and legends are never overlapped.
- Content max-width 1440px, 24/32px padding, cards never stretch to fill height - size to content, with equal-height rows only inside a deliberate grid.

PAGE SPECIFICATIONS
1. Overview: 4 compact KPI cards (label 12px, value 28px). Only "Open conflicts" is emphasised, and only when > 0; make its label and value consistent with the data (report the 12-vs-1 mismatch). Case summary: render the existing summary string at max 68ch, 1.6 line-height, card height to content; add a structured facts row if the data already exists. Remembered entities: avatar initials, name truncated with tooltip, role beneath, source chip; strip or clamp role fragments visually without altering data. Master timeline: vertical timeline, date left, event right, source chip. Move "Explore network" (secondary) and "Start investigation" (primary) into the page-header actions.
2. Entity network: full-bleed canvas inside a card; toolbar (search, layout select, zoom, fit, fullscreen). Node size by degree, shape by category, labels shown only for selected/hovered nodes and when zoom passes a threshold, truncated to ~18 chars with a background halo; edge labels on hover. Legend is a collapsible panel listing every category actually present. Selecting a node opens a right inspector (existing data only). Auto fit-to-view on load. Do not alter the graph engine.
3. Locations: dock the location list as a 360px side panel that does NOT overlay the map. Numbered markers whose colour/number matches the list; selected location detail lives in the panel; zoom controls bottom-left. Restyle for the basemap in use; do NOT hardcode any API key - surface the missing-key state as a clear inline notice instead of a watermarked map (report the key issue).
4. Workflow: node cards ~240px wide; title 14/600, description 12px text-secondary, category shown by a 3px left bar + monochrome icon (no rainbow), status chip only when not "ready" (running / error / complete). Add fit-view, zoom and minimap controls using the existing canvas library's built-ins. Toolbar: "Run workflow" primary, "Reset" secondary, "Delete" ghost/destructive separated by a divider and confirmed via dialog. Sentence case, remove "//" jargon. Merge the three "Scoped execution / Evidence trace / Reproducible flow" chips into one subtle info line or popover in the header. Ensure nothing clips at canvas edges.
5. Ledger: 44px rows, sticky header, hover highlight, no zebra. Columns: Field (human label primary; raw key such as party:complainant/informant_1 as small mono secondary on hover/expand), Value (clamp to 3 lines with expand; empty shows "Not found" in muted italic, with a warning icon if the field is required), Confidence (per the confidence scale), Source (compact evidence-thread chip instead of repeating filename + document type on every row), Actions (ghost icon button visible on row hover/focus, aria-labelled). Bounding-box coordinates move into the expanded row/tooltip. Optional group-by-source with section rows.
6. Document inspector: two-pane layout, resizable. Left: viewer top-aligned, fit-to-width by default, toolbar (zoom, fit, rotate, Processed/Original segmented control, SHA-256 as a copyable chip with tooltip - not a button), selected-field bbox highlighted. Right (about 420px, independent scroll): a compact checks list with status icons (pass/review/info; never text-only), then a searchable, filterable field list (existing chips with counts). Remove the huge empty area above the scan (report if it is a bug in sizing logic).
7. Evidence review: master-detail. Left: contradiction cards on neutral surface with a 3px danger left border and severity chip; conflicting values shown as compared rows with source chips + "Open source". Right: searchable traceable-objects list and a provenance detail panel with a small status chip (replace the large circular "OBSERVED" stamp), a human-readable title, raw ID and GUID under a collapsible "Technical details" with copy, and a source reference card (page, bbox, truncated SHA + copy). Add resolution actions ONLY if existing handlers exist; otherwise list under "Proposed features".
8. Quality & analytics: KPI row; extraction coverage as a grid (filename 220px | bar flex | value 48px) with a marked threshold line at 85%, bars neutral above threshold and amber/red below, sorted by value, "n fields - n flags" as secondary text; role mix as compact chips or a single-line list (not seven rows of "1"); all cards visible with consistent heights; convert the duplicate "Evidence review"/"Investigation" buttons to quiet text links.

STATES AND QUALITY BAR
- Every interactive element: default, hover, focus-visible (2px accent ring, 2px offset), active, disabled, loading. Every data region: skeleton, empty (icon + one line + action), error (message + retry).
- Keyboard: full tab order, visible focus, Esc closes popovers/dialogs, table rows and graph nodes reachable. All icon-only buttons have aria-labels. No information conveyed by colour alone.
- Responsive: primary target >= 1280px; at 1024-1279 the sidebar collapses to the rail; at < 1024 show a usable read-only layout with horizontal scroll inside tables. Never scroll the page body horizontally.
- Performance: no layout shift on load, virtualise long lists/tables if already supported, no additional re-renders from theming.

REPORT-DON'T-FIX LIST (log each with file/line evidence; do not patch silently)
- Map basemap API key missing.
- Entity network ignores "Force" layout; sentence-like junk entities.
- Same person extracted as complainant/accused/victim/IO at 90% confidence; empty and 0.00 values at 90%.
- Count mismatches: entities 12 vs 32; conflicts 1 vs 2; records 71 vs 74; "Needs review 12" vs "1 conflict".
- Evidence review badge "2 open" but one contradiction visible.
- Document inspector scan mispositioned; workflow canvas clipping.

DELIVERABLES PER PHASE
1) Summary of what changed and why, 2) files touched, 3) screenshots or diff notes vs baseline, 4) test/lint/build results, 5) risks and open decisions, 6) new bugs found but not fixed, 7) proposed features requiring logic changes.

ACCEPTANCE CRITERIA (FINAL)
- All existing tests pass; no console errors; production build succeeds.
- Every route, export and interaction behaves identically to baseline.
- Contrast passes WCAG AA; no text under 12px.
- One accent colour; status colours only for status; no ad-hoc hex values outside the token file.
- The flag can be switched off to restore the previous UI.

Start with Phase 0 only. Do not modify any file yet.

```

## Part 4: Your action plan (accountability)

1. **Today:** run Phase 0 only. Do not let the agent touch code. Read its bug list and check it against Section E above.
2. **Fix the trust bugs in parallel, as a separate task, before or alongside the redesign.** The confidence calibration and count mismatches matter more than any colour. If an investigator spots "184/2026 vs 29/17" and inconsistent counts, they will distrust everything else.
3. **Gate every phase.** No phase is accepted without green tests, a build, and a screenshot comparison against the baseline. If the agent skips a gate, that phase is rejected.
4. **Do Workflow and Entity network last.** They are the riskiest because they wrap third-party engines. Don't let the agent "improve" them earlier.
5. **Check the tokens yourself** in a contrast checker before Phase 2. My values are a starting point, not a verified final palette.

The prompt also assumes your stack is Next.js-based (from the dev badge), so Phase 0 has the agent confirm it instead of guessing. Want this as a downloadable `.md` file too?