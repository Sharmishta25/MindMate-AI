> Historical pre-expansion record. Current authenticated v4 behavior supersedes earlier no-login/plaintext-only feature descriptions. Follow README, SECURITY_AND_PRIVACY, DATA_RECOVERY, SCHEDULER_DEPLOYMENT and TEST_REPORT for current setup and verification. Legacy demo commands additionally require MINDMATE_LEGACY_LOCAL=true.

# Portfolio UI and QA report

Date: 2026-10-27. Scope: presentation and interaction quality; established persistence, analytics, safety routing and AI response contracts retained.

## Changes

- Added `ui/theme.py`: shared palette, typography, spacing, card/form/metric styling, visible focus, reduced-motion preference and narrow-screen stacking. Fonts are local; no font/CDN request was added.
- Reworked Welcome into a responsive two-column introduction, functional primary actions and tool cards. Kept purpose/limitations, visible privacy explanation and support access.
- Grouped date/time and journal date/title fields, clarified scales/instructions and primary save actions. New entries open saved/edit mode. Saved journal preview reads current stored content after editing.
- Styled shared Plotly charts and added daily and weekly table alternatives. Empty states explain what action provides missing data; numeric displays remain analytics-derived.
- Improved report action hierarchy, optional reflection guidance and persistent sidebar mode/privacy information.
- Added opt-in synthetic demo seeding and a persistent demo banner. No production data or external AI was used in it.

## Automated verification

Final command: `.\.venv\Scripts\python.exe -m pytest --basetemp=tmp/pytest-isolated`.

**172 passed in 21.88 seconds.** All 156 prior tests remain; 16 new parameterized cases cover presentation interactions and observed UX defects. No known failing test is hidden in this result.

| Interaction | Actual verification |
| --- | --- |
| Welcome primary/tool/privacy/support actions | AppTest clicks verify target navigation |
| All eight sidebar destinations | AppTest opens each on an empty database; rejects generic page-error state |
| Mood create/edit and repeated save | UI test verifies saved selection, update without duplicate, stored score |
| Journal create/edit/preview | UI test verifies saved/edit mode, one record after repeated save, fresh saved preview |
| Dashboard date filters | UI test checks recorded metric, empty range, reversed-range validation |
| Main mood-to-report journey | UI test records prior-week mood, edits it, views actual average, records helpful activity, generates report and checks stored evidence/export |
| Journal valid-provider consent flow | Existing mocked-provider UI test verifies explicit consent, source, dismissal, consumed consent and stale-result hiding |
| Missing credentials, timeout, rate limit, malformed output | Added UI tests verify labelled fallback, reasons, no missing-key call and Clear reflection |
| Activity forms/helpfulness | UI tests verify stored completion and report helpfulness count |
| Mood/journal/activity/report deletion | Existing and new tests confirm disabled-until-confirmed controls and correct data removal/session behaviour |
| Privacy reset and session clearing | Existing reset/rollback tests plus session-only clearing test |
| Report generation/refresh/saved selection/narrative | Existing UI/service tests, including duplicate/concurrent prevention, rollback, consent and stored snapshots |
| Download | AppTest verifies actual download control; service tests verify Markdown contents/escaping/errors. No browser download click was performed |
| Support/manual urgent/region selection | Existing synthetic support UI tests remain passing |
| Synthetic demo | New test verifies fourteen stored moods, labelled fictional journal content, persistent banner, opt-in config and no overwriting on repeat seed |

The first integration run had **9 failures / 147 passes** because an introduced missing colon in the report view prevented the shared router importing. The production exception boundary showed a generic error rather than leaking details. A synthetic diagnostic identified the syntax error; it was fixed and the complete existing suite passed 156 tests. Added QA tests then brought the final run to 172 passes. The defect was not bypassed by removing tests or weakening the error boundary.

## Startup and environment

Started an isolated synthetic demo using the existing patched `.venv` Streamlit runtime, port 8502. Startup output reported the local server running without an application startup error. Normal port 8501 and demo port 8502 both returned HTTP 200 with `ok` at `/_stcore/health`. Streamlit AppTest executed the application code and feature screens; a health response alone is not claimed as proof of every view.

No dependencies were changed in this UI pass. Previous safety-pass package audit results are historical, not a new vulnerability scan. All source/demo files stay within the project, with demo/test databases in ignored tmp/. Tests and demo have no live provider calls. A one-off synthetic `AppTest.from_string` diagnostic used the framework's temporary-script mechanism; it did not contain user content.

## Accessibility review scope

Calculated contrast of selected design-token pairs: primary body on app background 10.94:1; muted text on app background 6.23:1; body on sidebar 10.20:1; white on primary green 7.04:1; eyebrow green on app background 6.88:1. These are mathematical colour-pair checks, not measurements of browser-computed styles or full WCAG certification. Controls retain visible labels, charts retain axes/units and now have numeric table alternatives. CSS adds focus indicators, reduced-motion handling and column stacking below 760px.

## Browser limitation and outstanding issues

Browser automation was attempted with the computer-use skill. No browser connector was available; selecting the native Windows Edge surface stopped Computer Use because it could not determine the current browser URL confidently enough to enforce policy. No further browser input was attempted. No screenshots, browser workflow results or manual visual checks are claimed.

Outstanding checks: real desktop/narrow-screen visual layout, keyboard tab/focus order, screen-reader announcements, all rendered colour states and a browser Markdown download. The responsive CSS and labels are implemented but those checks require a future working browser session or human review. No live AI call, cost/latency benchmark, clinical evaluation, penetration test, mobile-device test or cross-browser certification was performed. Existing single-user, unencrypted-storage and safety-detector limitations remain documented in SAFETY_AND_PRIVACY.md.
