# Expanded profile demonstration

- Configure and retain a private encryption key; leave legacy mode false. Register a synthetic profile and retain its recovery code.
- Create mood/journal, request labelled fallback, view dashboard and generate a weekly report.
- Add lifestyle observations, view timeline/calendar, generate/edit/complete/skip a plan.
- Switch Hindi/Marathi and explain partial English fallback.
- Download JSON/CSV/backup; preview merge before applying.
- Enable in-app reminders with consent and explicitly run worker once; explain timing/catch-up and no external delivery.
- Show owner isolation with a second synthetic account, logout and restart persistence. Never expose keys/recovery codes.
- Rehearse the original presentation, record at least two minutes, verify audio/duration, and share only clean source/video links after review.

## Earlier compatibility-mode demo

Old seeding commands require MINDMATE_LEGACY_LOCAL=true and demonstrate original tools only.

# Assessment demo checklist

Use this checklist for rehearsal and recording. Unchecked boxes are tasks for the applicant, not claims that an action was completed. The automated status is recorded separately in [SUBMISSION_STATUS.md](SUBMISSION_STATUS.md).

## A. Set up a clean review environment

- [ ] Open the project root; use Python 3.12 and README Windows setup. Run with the project .venv interpreter.
- [ ] Install runtime requirements or the exact development lock snapshot. Protect .env; never record a real key.
- [ ] Run the full suite and dependency consistency check:

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp=tmp/pytest-assessment
.\.venv\Scripts\python.exe -m pip check
```

The documentation-preparation run passed 172 tests. Re-running is a local verification step, not a model-quality benchmark.

## B. Start the separate synthetic demo

In a separate PowerShell session, from the project root:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_demo
$env:MINDMATE_DB_PATH = 'tmp/demo/mindmate-demo.sqlite3'
$env:MINDMATE_DEMO_MODE = 'true'
$env:MINDMATE_LLM_ENABLED = 'false'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

- [ ] Open http://127.0.0.1:8502 and confirm SYNTHETIC DEMO DATA. It must be the demo database as well as the banner flag.
- [ ] Inspect actual dates. A fresh seed has fourteen moods over the previous two completed weeks, two journals and seven activity records. An existing populated demo is preserved; do not assume dates/counts are fresh or unchanged after rehearsal.
- [ ] Choose an unused UTC date for the new check-in. If already recorded, edit that entry or choose another date; do not reset personal data for a demo.
- [ ] Keep the normal app/database separate. Clear these process variables or close this shell before normal use. Close unrelated tabs/windows and conceal personal paths/content in any recording.

## C. Main user journey

- [ ] Welcome: explain the purpose and limitations; click Start a check-in.
- [ ] Save a fictional mood (for example 4), stress and selected emotions. Optional text must be labelled synthetic. Confirm the saved entry opens in edit mode.
- [ ] Edit it and Save changes; verify a single entry remains for that date. Do not claim an extra record was created.
- [ ] Dashboard: choose a range containing saved dates. Show real count/mean/median and chart/table values. Explain missing days, incomplete weeks and comparison withholding where applicable.
- [ ] Try a range with no records and a reversed range during rehearsal; verify useful messages. Do not show unnecessary error detours in the short final video.
- [ ] Wellness activities: complete one optional activity on a date in the reporting week, optionally rate helpfulness 4 or 5, and inspect saved history.
- [ ] Weekly reports: choose any day of a week containing entries, confirm Monday-Sunday UTC dates, generate and inspect. If your new check-in is in the current week, show its incomplete-week label; a prior complete week can show fuller history.
- [ ] Generate the same week again; verify it refreshes rather than creating another full snapshot.
- [ ] Click Download Markdown report and open the genuine file before claiming a successful browser download. Service/export and control availability were automated-tested; the browser download remains a human rehearsal check.
- [ ] Restart the app during rehearsal and reopen saved records/report. Do not confuse session-only AI results with persisted SQLite records.

## D. Journal reflection and honest AI demonstration

### Reliable no-key path for the video

- [ ] Select a saved fictional journal. If needed, use: `SYNTHETIC ENTRY. I feel calm after a walk. I made time to rest after work today.`
- [ ] Review/redact the excerpt. Choose an allowed activity preference if you want a suggestion.
- [ ] Leave sharing consent unchecked; Request reflection.
- [ ] Show the **Rule-based fallback (not an LLM)** source, tentative topics, explicit-feeling extraction, evidence and optional questions. Do not present this as a live model result.
- [ ] Dismiss a suggestion/Clear reflection if useful. Explain that results/preferences are session-only.

### Mocked provider integration evidence

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ai.py tests/test_ai_ui.py tests/test_ui_quality.py --basetemp=tmp/pytest-demo-ai
```

- [ ] Identify this as mocked test execution: it checks valid provider output, consent consumption, missing credentials, failures and malformed/unsupported conclusions without network calls or API credits.
- [ ] The UI failure tests are `test_reflection_failure_states_in_ui`; valid consent/dismissal is covered by `test_reflection_consent_fallback_dismiss_and_llm`. Do not claim the test runner is a mock-LLM toggle inside the app; no such production toggle exists.

### Optional live provider path (not verified during development)

- [ ] Only if you intentionally choose to make a real call: configure your own Anthropic key/model through ignored .env as in README, restart, use fictional excerpts and review the transmission notice.
- [ ] Demo commands set the process enable flag false. Remove/override that flag intentionally in a separate controlled run; configuration alone still does not authorize transmission.
- [ ] Check explicit per-request consent and Request reflection. Show LLM source only if a real validated response actually returns. If it fails, show labelled fallback honestly.
- [ ] Do not record the credential entry, claim a live call occurred before it did, or imply a model-quality/clinical evaluation.

## E. Safety and privacy rehearsal

- [ ] Open Get support manually; it works without text or a detector trigger. Do not make real emergency/support calls during a software demonstration.
- [ ] Explain that rules can miss or misunderstand distress; no match means no conclusion about safety. No risk score, diagnosis or automated contact exists.
- [ ] Privacy & data: show unencrypted storage disclosure and reset acknowledgement/phrase. Do not delete real user records for a recording. Deletion tests use synthetic fixtures.
- [ ] Confirm no keys/private journals appear in screenshots/video/export. Only genuine screenshots may be added later, with synthetic data and an accurate date/context.

## F. Package and final assessment readiness

- [ ] Rehearse [VIDEO_PRESENTATION.md](VIDEO_PRESENTATION.md), record at least two minutes, and check actual duration/audio/visibility.
- [ ] Review README, prompt history, AI design, user guide and project summary against what is shown.
- [ ] Use the prepared source archive in output/submission/; check its SHA-256 file and manifest. It excludes personal databases, .env, .venv and caches. The evaluator generates fictional data locally.
- [ ] Upload/share the source package or a repository and verify reviewer access. Localhost is not a public access link. No upload, public deployment or email submission has been performed here.
- [ ] Personally review the employer job description and mandatory terms. Add your own truthful prior-experience explanation if applicable.
- [ ] Only after these items are complete, submit according to the original brief. This checklist does not send anything.
