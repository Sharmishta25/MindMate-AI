# Data portability, migration and recovery

Use Data portability after signing in. JSON/CSV downloads contain plaintext owned data; keep them private. CSV is for reading, not import. JSON schema version 1 includes an embedded dictionary and records with kind, ISO date, source_id and data. Kinds: mood, journal, activity, lifestyle, plan, preferences, report. Source IDs remap journal links; they never select a destination owner. Authentication data, notification consent/schedules and delivery history are excluded. Unicode is retained.

## Preview and import

1. Download a backup before changing data. Select a JSON or .mmbackup file (10 MiB UI upload limit; service JSON limit 10 MiB, maximum 1,000 records).
2. Preview validates schema version, required fields, dates, finite bounded numbers, text sizes, activities, moods, plan items and duplicate source references. It shows record/conflict counts and a file digest. Upload alone makes no changes.
3. Merge retains existing same-day mood/lifestyle/preferences and same-week plan/report records; identical journal/activity payloads collapse. This may collapse intentionally identical records. Replace removes only your profile records, including schedules/consent; account credentials remain. Neither changes other users or original legacy tables.
4. Type IMPORT MY DATA or REPLACE MY DATA to match the chosen strategy and apply the previewed digest. Writes occur in a single transaction; failure rolls back replacement too. Journal links remap to owned moods or become empty if unavailable. Reports are recomputed from imported/retained evidence; imported plan provenance is explicitly unverified. Sign in again afterward.

## Encrypted record backup

Download encrypted backup creates a Fernet record bundle, not a full SQLite/system backup. Restore requires a key that encrypted it and the same account name. After recreating that account on the same/replacement installation with the original key ring, upload, preview and explicitly merge/replace. Password hashes, sessions and recovery codes are not restored. Account matching is a local guard, not proof of a person's identity. Wrong key, corrupt ciphertext, invalid envelope or foreign account is rejected. Keep a separately secured offline copy of keys; a password reset cannot recover lost keys. No recovery is possible when all usable encryption keys and decrypted backups are lost.

## Rotation

1. Securely back up records/database and the current key ring. Stop app and worker before an operator database backup; include SQLite sidecars or use SQLite's supported backup mechanism. Never commit the backup.
2. Generate a new Fernet key, prepend it to MINDMATE_ENCRYPTION_KEYS, retain old keys, and restart app/worker. Never paste keys into prompts/logs.
3. Each user opens Privacy & data, acknowledges backup and selects Rotate my encrypted records. This transaction re-encrypts only their records with the first key. Other users still require old keys until separately rotated. Test reading each profile afterward.
4. Do not remove old keys until every profile and every retained backup has been accounted for. Previously downloaded backups still require their old key; rotation does not rewrite them.

## Preserved legacy data

Schema v4 preserves all v3 rows unassigned and plaintext. No first-login ownership assumption is made. An operator who has verified that ALL original records belong to a specific existing account may run:

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate_legacy --username your-local-account
```

The script prompts privately for the password and requires ASSIGN ALL LEGACY DATA TO THIS ACCOUNT. It validates a merge into that account, remaps journal links and retains source rows unchanged. Historical report metadata is not copied; regenerate reports from evidence. If ownership is mixed or uncertain, do not run this script. There is no automated source erasure or forensic cleanup. Legacy compatibility mode remains a separate, explicitly unsafe-for-sharing local tool.
