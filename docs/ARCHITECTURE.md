# Architecture: schema v4 expansion

Streamlit app.py loads validated environment configuration, initializes additive SQLite migrations and routes UI. Default mode requires a valid Fernet key ring and account login. Explicit legacy compatibility mode retains the original single-user services for unassigned plaintext data. Neither mode silently converts ownership.

Components:
- ui/: account gate, language picker, core forms/charts, reports, privacy and expansion screens.
- security/auth.py: scrypt, opaque expiring/revocable sessions, recovery and fixed-name audit events.
- security/crypto.py: JSON Fernet/MultiFernet envelopes and rotation.
- services/vault.py: owner reauthorization, encrypted CRUD, atomic linked deletion, reset and deterministic report snapshots.
- services/wellbeing.py: lifestyle validation/paired statistics, timeline/search, preferences and bounded editable weekly plans.
- services/portability.py: versioned owner-only JSON/CSV, validation, preview digest, transactional merge/replace and encrypted backup.
- services/scheduling.py + scripts/scheduler.py: consented in-app notifications, persistent occurrence claims, timezone/DST resolution and retries.
- analytics/trends.py: descriptive numbers, missingness and guarded comparisons, independent of model output.
- ai/: provider adapter, versioned reflection/report/plan prompts, strict JSON/evidence validation and labelled fallbacks.
- safety/: conservative nonclinical support routing plus always-available guidance.
- i18n/: English canonical resources with partial Hindi/Marathi translations and visible English fallback.

SQLite preserves mood_entries, journal_entries, wellness_activities and report_metadata unchanged. New users store credential hashes and recovery hashes. Sessions store token digests/expiry. vault_records stores owner, kind, event_date and authenticated encrypted payload; deliveries stores owner/occurrence/status/attempts/time. Foreign keys link account records. Parameterized queries filter owner. Ciphertext binds owner/type/date/ID. Mood, lifestyle, report, preferences and schedule have per-owner/date uniqueness; plans are replaced at the service level for a selected week (simultaneous plan regeneration is not guaranteed conflict-free).

Dates are ISO, check-ins/timestamps and report weeks are UTC. Schedule times are explicitly IANA-local; worker report periods stay UTC. Lifestyle omissions are None, not zero. Same-day Pearson correlation is withheld unless at least seven paired days and variation in both values; it is descriptive, never causal.

Schema migration is additive and repeatable; original rows stay unassigned/plaintext. Explicit operator migration can copy a verified single owner's legacy records through bounded import without deleting originals. Encrypted profile data needs both authenticated account access and the operator key ring. Password reset does not recover encryption keys. JSON/CSV is plaintext; encrypted backup is a record bundle, not an account/database backup.

This is a local modular prototype, not a production multi-tenant security boundary. Key-bearing operators can access all profiles. No background process, public repository or deployment is implicit in starting Streamlit. See security, recovery and scheduler documents for exact limits.
