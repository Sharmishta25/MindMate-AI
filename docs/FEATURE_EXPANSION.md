# Feature expansion implementation plan

The eight-feature request has been implemented incrementally, with partial localization explicitly outstanding. Existing v3 plaintext tables are preserved as unassigned legacy data; first registration never claims them. New authenticated records use user-owned encrypted payloads, with authorization checked on every service operation. Legacy adapters remain for explicitly selected local compatibility mode and regression tests, not as an account-data access path.

1. Audit/baseline, schema v4 and migration tests.
2. Accounts with scrypt password hashes, expiring/revocable opaque sessions, one-use recovery codes and per-user services.
3. Authenticated Fernet encryption, environment-held key ring, rotation and honest legacy/metadata/export limitations.
4. Timeline/calendar/search and optional lifestyle records using the existing descriptive analytics.
5. Editable weekly plans with constrained AI choices and explicit deterministic fallback.
6. Versioned bounded import/export with preview, merge/replace confirmation, authenticated encrypted backup/restore.
7. Central translations for English/Hindi/Marathi and explicit language/safety limitations.
8. Opt-in in-app reminders and weekly report jobs via an explicit persistent worker; idempotent occurrences, timezone/DST policy and retry state.
9. Integration/regression tests, documentation and actual outcome log. No public-hosting or clinical-security certification is implied.

Encryption key configuration is a manual operator prerequisite; no key will be hardcoded, written to the database, or printed into development logs. Lost encryption keys cannot be reconstructed from password recovery codes.


## Verified integration and outstanding acceptance work

All new screens are functional in authenticated mode; services and original compatibility workflows are covered by the aggregate suite. Partial Hindi/Marathi localization is not full acceptance of every multilingual requirement: independent fluent review and translated explanatory/safety/report copy remain pending. Browser visual/accessibility/file-picker review, live provider evaluation and supervised scheduler deployment are also unverified. There are no placeholders advertised as working delivery features. See TEST_REPORT and RELEASE_CHECKLIST for evidence and manual steps.
