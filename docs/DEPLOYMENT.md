> Historical pre-expansion record. Current authenticated v4 behavior supersedes earlier no-login/plaintext-only feature descriptions. Follow README, SECURITY_AND_PRIVACY, DATA_RECOVERY, SCHEDULER_DEPLOYMENT and TEST_REPORT for current setup and verification. Legacy demo commands additionally require MINDMATE_LEGACY_LOCAL=true.

# Windows deployment and publication handoff

Release audit: 2026-10-27. **No repository was published, no cloud app was deployed, and no assessment was submitted.** These are applicant-operated instructions, not evidence that the actions occurred.

## Supported review platform

The verified runtime is Windows, Python 3.12.7, using the project .venv and pinned requirements-lock.txt. This release supports local single-user review. It has no authentication, encryption or tenant isolation; do not expose a private-data instance publicly or open inbound firewall/router ports for it. CORS/XSRF are not authentication. Linux/cloud deployment has not been tested and is not represented as a completed deployment.

## Reproduce the audited environment

Extract the clean source archive into a new folder and open PowerShell in the extracted MindMate-AI root. Do not copy private .env/database files into the source package.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade "pip>=26.2,<27"
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest --basetemp=tmp/pytest-release
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open http://127.0.0.1:8501 locally; stop with Ctrl+C. These commands avoid activation/execution-policy changes. The audit validated installed versions against every lock entry and ran tests; it did not perform another clean download/install. Exact pins are reproducible version selections, not artifact hashes or a cross-platform guarantee. requirements.txt remains the compatible-range alternative, but may resolve different versions.

## Secure configuration

Use .env.example for names only. Keep your real .env ignored, restrict access to the trusted device/account, and never put keys in code, screenshots, video, git URLs, commits or report exports. All local tools work with MINDMATE_LLM_ENABLED=false. For an intentional external test, privately configure your Anthropic key/model, enable the flag and restart. The account/model must support structured JSON and billing/access; no live credential was tested in this release.

Per-request consent is still required; configuration is not consent. Only reviewed excerpts/preferences leave for journal AI; report AI sends previewed numeric aggregates. Provider retention follows account terms. Use fictional data for any live demonstration and do not disclose a key while configuring it. Reset deletes local records but does not revoke keys/provider copies. Close a demo shell or clear process overrides before normal use, since process variables override .env.

## Reproducible synthetic demonstration

Use a separate PowerShell session in the same root:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_demo
$env:MINDMATE_DB_PATH = 'tmp/demo/mindmate-demo.sqlite3'
$env:MINDMATE_DEMO_MODE = 'true'
$env:MINDMATE_LLM_ENABLED = 'false'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

Open http://127.0.0.1:8502 and confirm the synthetic banner/database. Existing demo data is preserved, so use its actual dates or record an unused date. Follow [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md). The normal app stays separate. Valid/failure AI branches are demonstrated by the included mocked tests; the UI has no mock-provider switch. No background worker/scheduled delivery exists.

## Publish source to GitHub (manual; not executed)

Prefer the newly verified source archive rather than the working folder containing runtime data. [GitHub's import instructions](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github) and [new repository guidance](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository) were checked for this handoff.

1. Review SOURCE_MANIFEST.txt and SHA256SUMS.txt beside output/submission/MindMate-AI-source.zip; extract to a clean folder. Inspect files before sharing. The package excludes .env, databases, caches and .venv.
2. Sign in to GitHub yourself. Create an empty repository named MindMate-AI, choose visibility deliberately, and do not pre-initialize README/.gitignore/license because the project supplies its own files. No license file is supplied; choose appropriate terms yourself before claiming open-source licensing.
3. Open PowerShell in the clean extracted root. Configure your own Git identity/authentication if required; never put tokens/passwords into the remote URL. Run:

```powershell
git init
git branch -M main
git add -- .gitignore .env.example .streamlit/config.toml README.md PROMPT_LOG.md app.py pytest.ini requirements.txt requirements-dev.txt requirements-lock.txt mindmate scripts tests docs
git status --short --untracked-files=all
git diff --cached --name-only
git diff --cached --check
```

4. Review staged contents with git diff --cached on your own device. Confirm no keys, private journals, database/sidecar files, exports, .venv or tmp artifacts are staged. Stop and fix the staging list if they are. .gitignore does not untrack an already committed secret.
5. Only after review, commit locally, paste the exact repository HTTPS URL that GitHub provides (not a guessed placeholder), and push:

```powershell
git commit -m "Prepare MindMate AI assessment prototype"
$mindmateRemote = Read-Host 'Paste the exact HTTPS URL of your new GitHub repository'
git remote add origin $mindmateRemote
git remote -v
git push -u origin main
```

6. Verify the actual remote repository contains README, code, tests and the assessment docs. Opening localhost is not repository-access verification. Do not claim successful publication until the push and remote view are confirmed.

These commands are instructions only; no root Git repository, commit, remote or push was created during this audit. The only Git initialization used for testing was an ignored temporary fixture for .gitignore validation.

## Share reviewer access

For a public source repository, open its exact real URL in a logged-out/private browser and verify readable files, then share that URL plus video/prompt documentation. For a private personal repository, ask the reviewer which account should receive access, then use repository Settings -> Collaborators -> Add people and verify invitation acceptance. Personal collaborator permissions are broader than a dedicated read-only file share; choose an appropriate access model rather than granting unnecessary permissions. See [GitHub collaborator documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

Alternatively, upload the clean archive through your chosen approved file-sharing service, grant the intended reviewer access, and test recipient access yourself. No upload or permission change has been made here. Local ports 8501/8502/8503 are not externally shareable project links.

## Optional future hosted demo

No hosting configuration/provider has been selected or tested. For this assessment, runnable source plus a recorded synthetic demonstration is the verified route. Do not weaken localhost/security defaults or attach real SQLite data merely to obtain a public URL. A future hosted demo needs separately reviewed synthetic-only storage, reset/retention behaviour, runtime/storage persistence, HTTPS, access control and secret provisioning. Real personal multi-user deployment requires authentication/authorization, per-user isolation and a broader security/privacy review. This release is not production-ready because local tests pass.

## Final handoff

Record a video of at least two minutes using the prepared script, check its actual duration/audio/visibility, verify the real project/video link access, and personally review employer requirements. Update submission status only after those actions actually occur. Sending an assessment, publishing source or deploying the app is a separate user decision; this audit performs none of them.
