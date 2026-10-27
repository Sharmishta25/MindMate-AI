# Feature-expansion test report

Verified on Windows, Python 3.12.7, project .venv, 2026-10-27. Synthetic fixtures only. No journal text, passwords, encryption keys or live provider credentials are included in this report.

## Commands and observed evidence

- Baseline before expansion: 176 tests passed.
- Full first integration: 193 passed, no failures/skips (tmp/expansion-tests.xml).
- ` .\.venv\Scripts\python.exe -m pytest tests/test_expansion_integration.py -q --basetemp=tmp/pytest-expanded-journey`: 4 passed.
- ` .\.venv\Scripts\python.exe -m pytest tests/test_wellbeing.py tests/test_expansion_migration.py -q --basetemp=tmp/pytest-expansion-followup`: 3 passed.
- ` .\.venv\Scripts\python.exe -m pytest --basetemp=tmp/pytest-expansion-verified --junitxml=tmp/expansion-verified.xml -q`: **197 tests, zero failures/errors/skips, 38.270 seconds**. A subsequent final verification is recorded below if the evidence changed.
- ` .\.venv\Scripts\python.exe -m pip check`: No broken requirements found. Lock refreshed from the actual installed environment including cryptography 50.0.2.
- ` .\.venv\Scripts\python.exe -m pip_audit --local --cache-dir tmp/pip-audit-cache -f json -o tmp/expansion-audit.json`: No known vulnerabilities found. This is an advisory snapshot, not security certification. Initial invocation hit an out-of-project default cache permission error; a second used unsupported --no-deps options; corrected supported invocation above succeeded with authorized advisory access and a project-local cache.
- ` .\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8503 --browser.gatherUsageStats false`: server started; local /_stcore/health returned ok. This is process startup evidence, not a browser journey.
- ` .\.venv\Scripts\python.exe -m scripts.check_assessment_docs --expected-tests 197`: no issues before expanding its required-document list; final output recorded below.

## Coverage boundaries

Original unit/integration/AppTest tests are retained. Original UI regression modules explicitly select legacy compatibility mode so old single-user behavior remains tested. New authenticated AppTests verify login, encrypted journal save, logout, all expansion screens, lifestyle save, plan generation, calendar display and service-reopened persistence. Service tests cover owner isolation/read/update/delete/reset, token expiry/recovery/lockout, wrong keys/corruption/context swap/rotation, Unicode, missing lifestyle observations, seven-day paired statistics, plan progress/skip/regeneration, consent and mocked model choices/invalid output/timeouts, import preview/conflicts/rollback/link remapping/backup ownership, DST gap/fold/missed window, report retry and duplicate suppression. Test counts are not coverage percentages.

Tests exposed and fixed an accidental migration-test assertion edit, an import-module string syntax error and a changed legacy reset confirmation. The last failing full run had one reset-message assertion failure; mode-specific wording fixed it before the passing full run. No known failing test is hidden.

## Unverified / partial

No live Anthropic request, independently reviewed Hindi/Marathi translation, full localization, measured model quality, penetration test, production-hosting test, real OS task installation, external delivery or fresh network install from the lock was performed. Browser automation previously stopped because it could not confidently verify the Windows URL; no screenshots or manual browser/mobile/accessibility/download results are claimed. Streamlit AppTest is the UI evidence, not visual browser certification. Worker scheduling is tested with injected clock/service failures; no continuously supervised deployment is claimed. Key configuration, retained key backups and operator runtime remain manual prerequisites.

## Final confirmation

` .\.venv\Scripts\python.exe -m pytest --basetemp=tmp/pytest-expansion-final-confirmed --junitxml=tmp/expansion-final-confirmed.xml -q`: 197 tests, 0 failures, 0 errors, 0 skipped, 30.868 seconds. Includes actual Hindi-to-Marathi selector persistence and non-destructive legacy-copy tests. A newly added switch test found mutable navigation formatting; binding language per render fixed it. A legacy Markdown scheduling assertion was preserved with accurate mode-specific export wording.
