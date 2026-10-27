# Scheduler deployment and limitations

Implemented delivery is persisted IN-APP notifications only. No email, SMS or browser push exists. No worker starts merely by enabling preferences or running Streamlit. Core features work when no worker is running.

Sign in, open Reminders, choose reminder/report, an IANA timezone and local time (report also chooses weekday), enable and explicitly consent. Save. To revoke, disable or withdraw consent and save. The worker rereads consent after claiming a job; a notification already written before revocation remains. Reset/import replace removes consent and delivery history.

In a separate terminal, use the SAME configured local database and encryption key ring:

```powershell
.\.venv\Scripts\python.exe -m scripts.scheduler --once
.\.venv\Scripts\python.exe -m scripts.scheduler --loop
```

Loop polls every 60 seconds and requires a continuously running process and awake computer. For Windows Task Scheduler use the project .venv Python executable, arguments `-m scripts.scheduler --once`, and Start in the project root; repeat every minute under a restricted trusted account with securely supplied environment. Configure task overlap prevention and review history. This OS task has NOT been installed or tested here. Linux services/containers likewise need persistent disk, a single trusted worker, secrets and supervision; no hosted deployment is verified.

Due state is persisted by owner/occurrence. Reminders deduplicate by local date; report notifications by reporting-week Monday. Weekly reports always cover the previous completed Monday-Sunday UTC week, independent of display timezone. A missed occurrence catches up only within 24 hours; older events are skipped rather than flooded. DST spring gaps advance to first valid minute within two hours; repeated times use the first occurrence (fold=0). Unusual larger timezone gaps fail safely and require operator review. A claimed pending job has a 300-second lease. Failed jobs retry after 60 * attempts seconds, maximum three attempts per occurrence. A later poll/process can resume persisted state; a crash after notification but before completion is deduplicated by occurrence. Exhausted occurrences are not automatically rearmed; generate a report manually or wait for the next occurrence. No guaranteed delivery SLA is claimed.

Notifications do not include journal text. The operator worker can access all encrypted profiles because it holds the key; temporary sessions expire after five minutes and are revoked on completion. Protect the runtime and never share key-bearing logs/environment. Unit tests cover consent, DST gap/fold, late polling, repeated invocation, failed report retry and report-period deduplication. No real external delivery or OS scheduler integration has been tested.
