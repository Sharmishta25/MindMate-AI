# Current expansion release checklist

- [x] Additive v4 migration preserves unassigned legacy records.
- [x] Accounts, encrypted owner-filtered services and original core are integrated and tested.
- [x] Lifestyle, plans, timeline, portability and worker interfaces work with synthetic fixtures.
- [x] JSON/CSV and encrypted record backup scopes are disclosed.
- [x] Secrets/DBs/backups excluded from source archive; no publication performed.
- [ ] Operator creates and securely retains encryption key ring and recovery codes.
- [ ] Independent fluent-speaker review and full localization of explanatory/safety/report text.
- [ ] Browser/mobile/accessibility and actual download/import file-picker verification.
- [ ] Optional live provider evaluation with synthetic consented input and correct account model access.
- [ ] If reminders are needed, configure and verify a persistent supervised worker/OS schedule.
- [ ] Complete security/privacy review before any real-data public/shared hosting.
- [ ] Record >=2-minute video, publish/share only reviewed source, verify recipient access, and submit personally.

## Historical earlier release checklist

> Historical pre-expansion record. Current authenticated v4 behavior supersedes earlier no-login/plaintext-only feature descriptions. Follow README, SECURITY_AND_PRIVACY, DATA_RECOVERY, SCHEDULER_DEPLOYMENT and TEST_REPORT for current setup and verification. Legacy demo commands additionally require MINDMATE_LEGACY_LOCAL=true.

# MindMate AI release-readiness checklist

Audit date: 2026-10-27. Checked items are supported by this local audit; unchecked items remain manual/unverified. A checked test is not clinical validation or production certification.

## A. Repository and package

- [x] Inspected release source/configuration/docs and categorized runtime/generated folders.
- [x] Parsed Python sources and imported all 33 project modules without broken imports.
- [x] Verified root has no Git repository or published remote.
- [x] Checked every installed pin against requirements-lock.txt and runtime version ranges.
- [x] Verified .env.example defaults and all six environment names against documentation.
- [x] Tested .gitignore with real Git in an ignored fixture: 14 private/runtime paths ignored; four required source/config paths included.
- [x] Known-pattern scan found no hardcoded credential matches in reviewed release files; .env is absent. This is not an exhaustive secret audit.
- [x] Kept real/runtime databases, caches, demo state and .venv out of the source release; no actual private database content was opened for documentation.
- [x] Tightened packaging to reviewed document names, text/AST validation and source alias rejection.
- [x] Added regression checks for package exclusions, missing reviewed docs, disguised binary source and alias guard.
- [ ] Applicant reviews the final archive/manifest once more before uploading or publishing.

## B. Reproducibility and automated verification

- [x] Python 3.12.7/project .venv validated; pip check passed.
- [x] Complete release suite: 176 passed; zero failures/errors/skips in JUnit output.
- [x] Tested synthetic mood/journal/activity/dashboard/report create/edit/delete/reset workflows through services and AppTest.
- [x] Verified missing credentials and configured synthetic credentials with valid/malformed/failing mocked provider responses; no live call.
- [x] Refreshed dependency audit: 64 packages, zero known advisory entries at audit time.
- [x] Fresh localhost server launch on port 8503; health returned 200, ok. Normal/demo endpoints also healthy.
- [x] Ran available AST/import checks; no configured Ruff/Mypy/linter pipeline exists, so none is claimed.
- [x] Ran final document checks and regenerated the source-only archive, manifest and SHA-256.
- [ ] Reviewer reproduces dependency installation on another Windows machine/account. The audit validated existing installed pins, not a second fresh installation.
- [ ] Human/browser review: actual layout, narrow-screen/keyboard/screen-reader behaviour and browser Markdown download.
- [ ] Optional synthetic live-provider smoke test if desired, with the user's own credentials and explicit request consent; do not call mocks live AI.

## C. Security and safety

- [x] Reviewed actual-boolean/per-request consent, consumed consent, payload minimization and support-before-AI routing.
- [x] Existing tests verify sensitive strings do not appear in tested logs/error paths; raw private exception bodies are not intentionally logged.
- [x] Reviewed parameterized SQL/allowlists, input bounds, transactions, reset rollback and session clearing.
- [x] Verified static developer HTML only; untrusted journal/evidence uses plain text and exports escape user labels.
- [x] Strict model JSON rejects duplicate keys/nonfinite values; schemas/grounding reject unsupported content.
- [x] Purpose/limits say no diagnosis/treatment, no clinical validation, no automated safety guarantee and no automatic contacts.
- [x] Disclosed unencrypted/unauthenticated local storage and limits of deletion, snapshots, backups, provider retention and other sessions.
- [ ] Reverify intended-region support resources before a later external deployment; current static review date remains 2026-10-27. No emergency calls should be made for software QA.
- [ ] Production security/access-control/privacy review before any real-data public/multi-user hosting. Not implemented in this release.

## D. Local demonstration and publication (user-operated)

- [x] Prepared exact pinned Windows setup and secure environment guidance in DEPLOYMENT.md.
- [x] Prepared separate labelled synthetic seeder/demo and step-by-step workflow.
- [ ] Applicant rehearses the synthetic demo against the actual sample dates; populated demo data is not automatically reseeded.
- [ ] Applicant records and verifies at least a two-minute video (script is ready; recording is not).
- [ ] Applicant personally reviews employer job description/mandatory terms and any truthful experience commentary.
- [ ] Applicant creates a clean repository or uploads source archive only after reviewing files/permissions.
- [ ] Applicant verifies the actual project link in the recipient's access context; localhost is not a project share link.
- [ ] Applicant verifies video/prompt document access, assembles all three assessment deliverables, and chooses whether to submit.
- [ ] Update the recorded publication/submission status only after real confirmation. No publication, deployment, upload, invitations or email was performed by this audit.

## Mandatory assessment deliverables

| Deliverable | Status at audit |
| --- | --- |
| Video script and practical sequence | Prepared: 345-word script and demo checklist; actual >=2-minute recording pending |
| Genuine prompt documentation | Prepared/reviewed: eight recorded task prompts including this audit, purposes/revisions and observed evidence; no off-thread history invented |
| Accessible project link | Pending user publication/sharing and recipient-access verification; clean runnable source package prepared |

Read [RELEASE_AUDIT.md](RELEASE_AUDIT.md) for commands/results/limitations and [DEPLOYMENT.md](DEPLOYMENT.md) for exact user-operated publication steps.
