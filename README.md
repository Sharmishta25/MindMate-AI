# MindMate AI

A local-first mental wellbeing and emotional pattern-tracking application, prepared for the **AI Growth & Automation Associate assessment** as one healthcare/technology web-application project.

**Status:** implemented local prototype; not published or submitted. Core tools run without an API key. External AI integration is implemented and tested with mocks; no live model request or model-quality benchmark has been performed.

## Problem and intended users

Daily feelings, reflections and personally helpful activities can be difficult to review together over time. MindMate AI brings these self-reported records into a small, explainable workflow: check in, reflect, notice descriptive patterns, and save a weekly report.

The intended users are individuals seeking general wellbeing reflection on a trusted personal device. This is a design objective, not a finding from user research. The app is not clinically validated, does not diagnose/treat/predict psychiatric conditions or self-harm risk, and does not replace qualified care. It is not an emergency monitoring service.

Current expansion verification: **197 tests passed**; see [test evidence](docs/TEST_REPORT.md). Historical counts below describe earlier assessment phases.

## Implemented features

| Tool | What works |
| --- | --- |
| Mood tracker | One check-in per UTC date; mood 1-5, stress 0-10, selected emotions, optional triggers/reflection; create, edit and confirmed deletion |
| Journal | Create/read/edit/delete; optional check-in association; bounded plain text; new saves open in edit mode |
| Dashboard | Actual count/recent/mean/median mood, date filtering, daily/weekly Plotly charts, table alternatives, missing-day coverage, emotion/stressor frequencies and guarded comparisons |
| Wellness activities | Optional grounding, reflective writing and gentle breathing; completion history and optional helpfulness rating |
| Weekly reports | Explicit Monday-Sunday UTC period, saved deterministic snapshot, refresh without duplicate full snapshots, view/delete and Markdown download with a text chart |
| Optional journal AI | Consent-gated, evidence-linked topic/emotion/question/activity selection; validated output and labelled local fallback |
| Optional report AI | Aggregate-only section selection; all prose/numbers rendered locally from engine evidence |
| Get support | Local conservative phrase-based support routing, always-available manual guidance, reviewed India resource option and official-local-resource fallback elsewhere; no automatic contacts |
| Privacy & data | Actual storage disclosure, current-session clearing and acknowledged typed-confirmation reset of all record tables |

Authenticated local profiles, owner-filtered encrypted records, lifestyle tracking, timeline/calendar/search, editable weekly plans, JSON/CSV portability, encrypted record backups and opt-in worker-driven in-app notifications are implemented. Email/SMS/push, PDF export and persistent AI reflection history are not implemented. Hindi/Marathi core labels and limited language-aware reflection support are partial; remaining text falls back to English. Independent translation review is pending.

### Screenshots

No genuine project screenshots are available in the supplied records or project artifacts, so none are included. Computer Use previously stopped because it could not confidently verify the Windows browser URL. Browser visual/mobile/accessibility and actual browser-download checks remain outstanding. No mockup is presented as a screenshot.

## Technology and architecture

Python 3.12, cryptography (Fernet/MultiFernet), Streamlit, SQLite, Pandas, NumPy, Plotly, python-dotenv and pytest. Anthropic Messages is the optional runtime provider; the HTTPS adapter uses Python's standard library. Codex was used during development for implementation, test-driven debugging and documentation, with actual user prompts preserved in [PROMPT_LOG.md](PROMPT_LOG.md).

```text
app.py -> configuration + SQLite initialization -> Streamlit UI
                                              -> validated services -> SQLite
                                              -> deterministic analytics -> charts/reports
                                              -> consent + local safety gate -> AI provider
                                                                            -> validation/fallback
```

| Location | Responsibility |
| --- | --- |
| `mindmate/ui/` | Navigation, forms, shared theme, charts, privacy/support and report views |
| `mindmate/services/` | Validated CRUD, transactional report generation, Markdown export and reset |
| `mindmate/database.py` | Four preserved legacy tables plus users, sessions, vault_records and deliveries; schema v4 migrations and connection lifecycle |
| `mindmate/analytics/` | Descriptive evidence; trends.py is the current dashboard/report engine |
| `mindmate/ai/` | Versioned prompts/schemas, provider client, grounded validation and fallback |
| `mindmate/safety/` | Limited local support routing and reviewed static resource links |
| `mindmate/config.py` | Environment parsing, secret-safe settings and project-contained database paths |
| `tests/` | Deterministic synthetic unit/integration/AppTest cases |
| `scripts/seed_demo.py` | Opt-in fictional records in a fixed ignored demo database |

[Architecture](docs/ARCHITECTURE.md) contains historical implementation notes. [AI design](docs/AI_DESIGN.md) describes the current AI boundary.

## Windows setup

Extract/open the project and open PowerShell **in its root folder**. Use Python 3.12; the verified interpreter is 3.12.7. No virtual-environment activation or PowerShell execution-policy change is required.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade "pip>=26.2,<27"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Generate once; save securely outside the repository for subsequent launches.
$env:MINDMATE_ENCRYPTION_KEYS = & .\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open http://127.0.0.1:8501 on that computer. Stop with Ctrl+C. If python points to another version, use your Python 3.12 interpreter for venv creation. Use the project `.venv` interpreter for all later commands; the original shared environment was outdated/conflicting and was not modified.

For the exact tested environment, install `requirements-lock.txt` **instead of** `requirements.txt`. That snapshot includes development/audit tools and pip; it has version pins but no artifact hashes. `requirements-dev.txt` adds audit tooling to runtime ranges. Network/package-index access is needed to install dependencies.

## Configuration

Profile mode requires a valid encryption key ring. The generation command above is for FIRST setup only: do not generate a replacement key on every launch. Save it in a private secret store or ignored `.env`, retain it across restarts, and never share it. Missing keys show setup guidance rather than exposing records. Register a profile and retain its one-use recovery code separately. `.env` must remain private. Process environment variables take precedence over `.env`. Restart the server after changing configuration; do not overwrite an existing `.env` with the example.

| Variable | Default | Meaning |
| --- | --- | --- |
| MINDMATE_ENCRYPTION_KEYS | empty | Required comma-separated Fernet keys; first writes; retain old keys for rotation/backups |
| MINDMATE_LEGACY_LOCAL | false | Explicit unencrypted unauthenticated compatibility mode; never expose publicly |
| MINDMATE_DB_PATH | data/mindmate.sqlite3 | Project-contained local .db, .sqlite or .sqlite3 file |
| MINDMATE_LLM_ENABLED | false | Enables the provider branch, still subject to request consent/safety checks |
| MINDMATE_LLM_API_KEY | empty | Anthropic API key; never put a real key in docs/tests/version control |
| MINDMATE_LLM_MODEL | empty | Account-available model supporting JSON structured outputs |
| MINDMATE_LLM_TIMEOUT_SECONDS | 20 | Integer 1-60; socket-operation timeout, not a whole-request deadline |
| MINDMATE_DEMO_MODE | false | Shows a synthetic-data banner; does not itself seed or switch databases |

The default database is created when an app session initializes. Schema v4 upgrades earlier versions without deleting records. Legacy mood entries without captured time use documented midnight UTC timestamps. Network/device/protected/out-of-project database paths are rejected.

### Optional Anthropic setup

Use your own Anthropic API account with billing/model access. A documentation-based model example is:

```dotenv
MINDMATE_LLM_ENABLED=true
MINDMATE_LLM_API_KEY=your-anthropic-api-key
MINDMATE_LLM_MODEL=claude-sonnet-5-5
MINDMATE_LLM_TIMEOUT_SECONDS=20
```

The adapter targets `https://api.anthropic.com/v1/messages`. Check account availability against [official model IDs](https://platform.claude.com/docs/en/models/overview) and the [structured-output contract](https://platform.claude.com/docs/en/build-with-claude/structured-outputs); access to this example model was not live-tested.

A journal request sends only reviewed/redacted excerpts (up to three, 2,000 characters each), temporary source indexes and allowed activity preferences. The user must request reflection and consent to that payload. Consent is consumed after use. A report narrative sends previewed numeric aggregates, not journals or label text.

No consent, disabled/missing configuration, rate limits, timeouts, service errors or rejected output produce clearly labelled **Rule-based fallback (not an LLM)** results. Matched concerning content instead prioritises local support guidance and pauses routine journal interpretation. No journal text is transmitted merely by opening/saving it. The model cannot change dashboard statistics.

## Synthetic portfolio demo

Run this in a **separate PowerShell session** from the project root:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_demo
$env:MINDMATE_DB_PATH = 'tmp/demo/mindmate-demo.sqlite3'
$env:MINDMATE_DEMO_MODE = 'true'
$env:MINDMATE_LEGACY_LOCAL = 'true'
$env:MINDMATE_LLM_ENABLED = 'false'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

Open http://127.0.0.1:8502. On a fresh demo database, the seeder creates fourteen check-ins over the previous two completed calendar weeks, two fictional journals and seven activity records. All are synthetic; metrics are calculated from saved rows. Existing populated demo databases are kept, not reseeded/reset. Their dates can become old: choose report/filter dates from actual entries, not automatically the latest week. Normal records are not copied or modified.

The demo flag only labels the UI. Pair it with the demo database path above. The demo disables external AI deliberately; valid/failure provider paths can be demonstrated with mocked tests. Close that shell after use, or clear those three variables before starting the normal app. See the [demo checklist](docs/DEMO_CHECKLIST.md).

## Run tests and inspect health

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp=tmp/pytest-assessment
.\.venv\Scripts\python.exe -m pip check
```

Use only a disposable pytest base-temp directory; pytest can clear it. Tests use synthetic fixtures and mocked responses, not private journals or paid calls.

Historical assessment-preparation run on 2026-10-27: **172 passed**, and pip check reported no broken requirements. Tests cover CRUD/persistence, validation, schema migration, analytics/date boundaries, snapshots/concurrency/rollback/export, safety/reset, consent, mocked AI failure/output handling and AppTest journeys. No coverage percentage, user-study result or live-model quality score is claimed. [QA report](docs/QA_REPORT.md) records the earlier UI pass and its corrected regression.

The safety pass previously audited 64 isolated packages with no known vulnerabilities after a project-local pip upgrade. That was a point-in-time advisory check, not a new audit in this documentation pass or a security certification. Runtime requires Streamlit >=1.54 following the [maintainer Windows advisory](https://github.com/streamlit/streamlit/security/advisories/GHSA-7p48-42j8-8846).

With a server running, its `/_stcore/health` endpoint can be checked locally. A health response is not proof of every screen. Ports 8501/8502 are local addresses, not reviewer-accessible publication links.

## Privacy, safety and deployment limits

SQLite itself is **not encrypted**. Profile payloads use Fernet and owner-filtered access; metadata and unassigned legacy tables remain visible. This is not a reviewed public-hosting security boundary. Use a trusted device and localhost binding. Project Streamlit defaults enable CORS/XSRF, disable static serving/usage telemetry, and hide detailed errors. The app does not intentionally log private journal text, keys, complete runtime prompts or content-bearing exception objects; OS/framework/proxy logging is outside complete application control.

Support rules are conservative phrase checks, not clinically validated detection or safety assurance. No match does not mean someone is safe. The app never automatically contacts anyone. Region defaults to unspecified; reviewed India links apply only if India is selected, and other regions are directed to official local resources.

Confirmed deletion/reset removes local database records, not guaranteed forensic remnants, exports, backups, provider copies or other sessions. Old report snapshots survive source edits/deletion unless refreshed/deleted. AI is fallible; narrow English grammar/keywords can misread quotations/negation. No complete injection prevention, clinical validation or security certification is claimed. Read [Safety and Privacy](docs/SAFETY_AND_PRIVACY.md).

### Reviewer access and submission status

**No public deployment, GitHub repository URL, Drive share link or submission has been created.** This workspace is not currently a Git repository. A clean source archive is prepared under `output/submission/`; its contents/hash and current gaps are listed in [submission status](docs/SUBMISSION_STATUS.md). An evaluator can extract it and follow local setup/demo instructions without an API key.

To provide the assessment project-access link, the applicant must upload/share the clean source package or create a repository and verify reviewer access. Do not include .env, personal databases, exports, .venv, caches or private journals. Sharing runnable source is preferable to exposing this unauthenticated app with real data. Any future public demonstration must use isolated synthetic data and separately reviewed hosting/security controls; no hosting provider/runtime has been tested here.

A presentation **script** is provided, not a recorded video. Record and verify a video of at least two minutes before submitting. The applicant must personally review the employer job description/mandatory terms; that eligibility check has not been performed by this documentation task.

## Assessment documents

- [Actual prompt log](PROMPT_LOG.md)
- [AI design](docs/AI_DESIGN.md)
- [Step-by-step user guide](docs/USER_GUIDE.md)
- [Video presentation script](docs/VIDEO_PRESENTATION.md)
- [Demo checklist](docs/DEMO_CHECKLIST.md)
- [Project summary](docs/PROJECT_SUMMARY.md)
- [Submission status](docs/SUBMISSION_STATUS.md)


## Final release audit (2026-10-27)

Historical pre-expansion release: **176 tests passed**, with zero failures/errors/skips, after adding four release-tool regressions. The original 172-test assessment-preparation result above is historical. Dependencies match the lock; pip check passed; the refreshed 64-package advisory audit reported no known findings. No live provider call, public deployment or submission occurred. See [release audit](docs/RELEASE_AUDIT.md), [release checklist](docs/RELEASE_CHECKLIST.md) and [deployment/publication instructions](docs/DEPLOYMENT.md).


## Expanded profile demo

For all new features, use profile mode (`MINDMATE_LEGACY_LOCAL=false`) and a retained encryption key. Register a synthetic account, save a mood and journal, add a lifestyle observation, open Timeline/Calendar, generate a weekly plan, complete/skip a plan item, and generate a weekly report. Download JSON/CSV and an encrypted backup; preview an import before applying. Reminder preferences do not start a worker. In a second configured terminal run:

```powershell
.\.venv\Scripts\python.exe -m scripts.scheduler --once
# Or keep running explicitly:
.\.venv\Scripts\python.exe -m scripts.scheduler --loop
```

[User guide](docs/USER_GUIDE.md), [security](docs/SECURITY_AND_PRIVACY.md), [recovery](docs/DATA_RECOVERY.md), [scheduler runtime](docs/SCHEDULER_DEPLOYMENT.md), [language limitations](docs/AI_AND_MULTILINGUAL.md) and [change log](docs/CHANGELOG.md) describe the expansion. Legacy rows are preserved unassigned, not silently attached to the first account. The old synthetic demo intentionally uses compatibility mode; create synthetic profile records to demonstrate new features.
