> Historical pre-expansion record. Current authenticated v4 behavior supersedes earlier no-login/plaintext-only feature descriptions. Follow README, SECURITY_AND_PRIVACY, DATA_RECOVERY, SCHEDULER_DEPLOYMENT and TEST_REPORT for current setup and verification. Legacy demo commands additionally require MINDMATE_LEGACY_LOCAL=true.

# Safety, privacy and security

## Purpose and scope

MindMate AI is a general wellbeing and self-reflection prototype. It is not clinically validated, suitable for diagnosis/treatment, a substitute for qualified care, a crisis monitoring service, or security certified. Mood/stress ratings are self-reports. Descriptive averages and selected emotion labels are not clinical assessments, and associations do not establish causes. AI interpretation is constrained, fallible and uncertain. These limitations appear throughout the UI; no condition or self-harm probability is diagnosed or scored.

## Support pathway

`mindmate/safety/support.py` implements local, deterministic phrase-based routing, independent of AI credentials and provider availability. Unicode normalization, removal of invisible formatting characters, and whitespace normalization improve a narrow set of matches. Immediate-danger/action language prioritises conditional urgent guidance. Other concerning phrases offer support with an emergency option. The route contains only display booleans, not a risk score, probability, diagnosis or a claim that someone is safe. A non-match does not establish safety.

Checks run on mood triggers/reflections and journal title/content when opening or submitting the corresponding form. Form text is received by Streamlit on submission, not on every keystroke. Submitted matches leave a non-sensitive support notice in session state so it remains visible after saving. The selected saved journal and any explicitly selected additional context entries are also checked in full before optional AI: a concerning phrase beyond the 2,000-character excerpt boundary still pauses routine interpretation. The service itself checks all supplied excerpts before any provider call and returns support guidance without routine questions or activity suggestions. Writing can still be saved, viewed, edited or deleted; support routing is not a gate to keeping a journal.

**Get support** is always available from navigation, without any text or detector trigger. A user can explicitly request urgent guidance. Guidance prioritises local emergency services or an emergency department for immediate danger, reaching a trusted person who can stay with them or help them reach care, and a qualified professional/crisis-support service. It does not delay help while waiting for AI. The app never automatically calls, messages, locates, notifies family, or contacts professionals/emergency services. Clicking a phone or website link is a separate user action.

The local rules primarily cover selected English phrases. They can miss slang, coded wording, many languages, and indirect distress; they can over-trigger on negation, quotations, fiction or historical events. The UI acknowledges those possibilities and avoids asserting a person's current state. This has not been evaluated as a medical crisis detector, and no sensitivity/specificity or clinical effectiveness is claimed. No mood threshold is used to route someone to crisis support. A reassuring chart or an absent notice is never presented as evidence of safety.

## Regional resources and verification

The default resource region is **Other / not specified**, not an inferred location. Users may select India explicitly; selection lasts only for the session. There is no IP/geolocation lookup.

India resources were reviewed on **2026-10-27**. Emergency assistance uses the Government of India's ERSS information: [Ministry of Home Affairs](https://www.mha.gov.in/nirbhayaerss-section). Tele MANAS information was retrieved using the dedicated local helpline lookup tool; its returned phone and website links are preserved in `mindmate/safety/resources.py`. These are static resource details, not a guarantee that a call will connect. Availability may change. This implementation does not independently contact a service to test it.

Other regional crisis-service details were not verified. The app explicitly directs users to official local government/health-service resources, local emergency services or the nearest emergency department, rather than guessing a number. Deployment owners must verify appropriate resources, language coverage, availability and accessibility for their intended region and recheck them regularly. No background resource refresh or monitoring exists.

## Data flows

| Data | Local use/persistence | External transmission |
| --- | --- | --- |
| Mood, stress, emotions, triggers, reflections | SQLite; deterministic analytics; support routing of free text | No automatic transmission |
| Journal title/body | SQLite; locally rendered plain text; local support checks | Only reviewed excerpts after explicit request and consent |
| Journal AI request | Up to three redacted/reviewed excerpts, 2,000 characters each; temporary indexes and selected activity preferences | Anthropic fixed HTTPS Messages endpoint, only after consent |
| Weekly report | Deterministic snapshot in SQLite, including user-reported label counts; Markdown export on user click | No automatic upload |
| Optional report AI | Previewed aggregate numbers/counts, no journal/title/date/ID or emotion/stressor/activity names | Anthropic only after separate per-request consent |
| AI result/preferences/dismissals | Current Streamlit session memory, not SQLite | Result comes from provider only when a request was made |
| Support route/region | Current session; booleans and selected region only, no stored risk profile | No support service is contacted |
| Dependency audit | Package inventory and advisory output in ignored temporary storage | Package names/versions queried against public PyPI advisory data during manual development audit |

Consent must be an actual boolean in the orchestration services; strings or truthy integers are rejected. UI consent is scoped to the current payload and consumed after a request. Merely opening, editing or saving a journal does not authorize transmission. Configuration alone does not authorize it. If consent is absent or service/output validation fails, the application labels local fallback explicitly. Concerning journal content prioritises local support rather than external interpretation, even if consent is checked. Unsaved form content is not automatically included in a saved-entry reflection request.

No automatic anonymization is claimed. Users must review/redact excerpts. A provider may process/retain content according to account terms; local deletion cannot retract an already-sent request or delete provider records. A timeout does not prove the provider did not receive data. Socket timeouts are not guaranteed whole-request wall-clock deadlines.

## Secrets, logs and error handling

Secrets are loaded from environment variables or ignored `.env`; settings hide API keys from representations. `.env*`, SQLite databases/sidecars, `data/`, `private/`, `exports/`, logs, `.venv/`, temporary artifacts and `.streamlit/secrets.toml` are ignored. Generic system templates and synthetic examples in the assessment prompt log are not private runtime prompts. Full runtime prompts, journal text, response bodies, keys and sensitive exceptions are not deliberately logged by this application.

Provider/database failures use constant non-sensitive messages or whitelisted reason codes. Streamlit error detail display is disabled. A top-level page exception boundary shows a generic error without logging the exception object because dependencies can embed content/headers in exceptions. This sacrifices detailed production diagnostics: reproduce with synthetic input rather than enabling content-bearing logs. A partial page may already have rendered local content and a save may have completed before a later UI error; users are told to check existing records before retrying. Framework/OS/proxy crash reporting is outside this code's complete control. Do not enable request-body tracing, local-variable traceback capture or third-party session replay for private content.

## Injection, rendering and file boundaries

SQL values are parameterized. Table interpolation is restricted to code-owned allowlists. Service boundaries validate IDs, dates, ratings, lengths, Unicode, null bytes, record types and activity choices. Duplicate daily check-ins fail without overwriting records. Transactions roll back failed writes.

Untrusted journal text is JSON data in a separate message, not system instructions. Local instruction-boundary heuristics include normalized invisible-character checks. Provider JSON uses a bounded read and rejects duplicate keys/nonfinite constants. Schemas reject unknown fields, invented evidence, unsupported emotions/topics, medical conclusions and disallowed suggestions. Model-generated free prose is not rendered; constrained local templates render approved choices and engine values. API redirection is disabled, the destination is fixed HTTPS with normal certificate verification, and no tools or automatic retries are granted. These layers reduce consequences but do not completely prevent prompt injection, semantic misinterpretation or provider compromise. A schema-valid, keyword-supported interpretation can still be wrong.

Saved journals/evidence are displayed with plain text APIs. User labels use dataframe cells; Markdown exports escape user label markup/HTML. The only `unsafe_allow_html` calls use static developer-authored CSS/labels and never interpolate user content. No file uploads, arbitrary file browser, public static serving, or user-controlled external API endpoint is implemented. Export filenames are derived from validated report dates.

Database paths must stay within the project and use `.db`, `.sqlite` or `.sqlite3`. Network/UNC/device paths are rejected before filesystem resolution; reserved names, alternate stream syntax, protected project directories and ambiguous Windows filename forms are rejected. These controls are not an OS filesystem sandbox: an attacker with local filesystem access can alter databases, replace code or race a path check. Use trusted directories and restrictive OS permissions.

## Storage, deletion and reset

The default location is `data/mindmate.sqlite3` inside MindMate-AI; **Privacy & data** shows the actual configured local path. SQLite is **not encrypted** and there is no authentication or tenant isolation. Records persist across restarts. AI excerpts/results/widget values can remain in session memory until cleared or the session ends.

Individual entry/report deletion requires confirmation. Entry/report deletion clears the current app session to reduce retained excerpts/results. Deleting mood entries preserves linked journals with the association cleared. Deleting a source entry does not delete historical report snapshots or exports; this is disclosed. Report deletion removes only that snapshot. **Clear this app session** clears current session state without deleting saved records.

**Reset all saved data** requires a separate acknowledgement and typing `DELETE ALL MY DATA` exactly. The service atomically deletes journals, moods, activities and all report metadata/snapshots. The schema and `.env`/API configuration remain. If any deletion fails, the transaction rolls back. The current session is cleared after success. Other open sessions can retain already-loaded content or resave it; close them first. Reset does not delete arbitrary files or backups.

`PRAGMA secure_delete=ON` overwrites deleted SQLite cells where supported, reducing some remnant data. It is not guaranteed forensic erasure and does not encrypt the database, securely wipe SSD blocks, eliminate every sidecar/cache, revoke provider copies, remove backups/downloads, or clear other processes' memory. Retained files/cloud sync and OS crash dumps require separate user controls. No secure-erasure certification is claimed.

## Dependencies and deployment

`.streamlit/config.toml` binds localhost, enables CORS/XSRF protection, disables static serving/usage telemetry and hides detailed errors. CLI/environment overrides can change these defaults. This is a local single-user prototype; do not expose it publicly with private data. Shared hosting requires real authentication/authorization, TLS, per-user isolation, tested access controls, threat modelling, operational monitoring without sensitive payload logging, and appropriate professional/legal review. This pass does not implement those production capabilities.

The original shared Python environment contained Streamlit 1.37.1 and conflicting package requirements. The [maintainer's Windows SSRF advisory](https://github.com/streamlit/streamlit/security/advisories/GHSA-7p48-42j8-8846) identifies versions before 1.54.0 as affected; `requirements.txt` now requires at least 1.54. A project-local `.venv` was created and installed with Streamlit 1.66.1. The shared system Python was not modified. Its outdated/conflicting packages must not be used to launch this app.

The isolated dependency audit initially reported advisory entries for bundled pip 24.2. Project-local pip was upgraded to 26.2.2. The repeat `pip-audit --local --strict` audit examined 64 packages and reported no known vulnerabilities; `pip check` reported no broken requirements. These are point-in-time checks against known advisory data, not proof of complete security. The tested dependency snapshot is `requirements-lock.txt` (includes development/audit tools and pip; no artifact hashes). `requirements-dev.txt` supports audit tooling; runtime requirements remain separate. Reaudit after updates and before deployment. This is not a full supply-chain audit or security certification.

## Evaluation and remaining risks

Tests use synthetic phrases/content and mocked providers. They verify support routing/normalization, explicit manual support, persistence of guidance after saves, full-entry checks beyond excerpt limits, clinical-score avoidance, real-boolean consent, provider suppression, unsafe input/path rejection, SQL/JSON boundaries, deletion/reset confirmation and atomic rollback, session clearing, plain-text rendering and sanitized exception handling. Existing CRUD, analytics, report, provider failure and consent tests remain. Results and exact commands are recorded in PROMPT_LOG.md.

Not verified: clinical usefulness or detector accuracy; all languages/cultures; real emergency/helpline calls; complete injection resistance; live provider quality/privacy practices; forensic erasure; penetration testing; multi-user access controls; browser visual/accessibility review; arbitrary OS/proxy logging. Automated support can over-trigger or miss danger. Users can always open Get support and must never wait for this application to authorize seeking help.
