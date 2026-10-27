# Security and privacy: authenticated expansion

This is a local assessment prototype, not security-certified, clinically validated or approved for medical use. General wellbeing tools cannot diagnose or determine that someone is safe.

## Accounts and authorization

Usernames are casefolded ASCII identifiers. Passwords are salted scrypt hashes (N=32768, r=8, p=1); plaintext passwords are never stored. Login uses random opaque tokens; SQLite stores SHA-256 token hashes, fixed 30-minute expiries and revocation. Each Vault public operation revalidates its session and filters by owner. Record IDs alone confer no access. Five failed passwords lock an account for five minutes. Registration reveals whether an identifier exists; this is not a hardened public identity system. Recovery uses a high-entropy one-use code, rotates it and revokes existing sessions. There is no email recovery or automatic contact. Retain recovery codes privately; losing both password and code prevents ordinary account recovery.

## Encryption scope and key handling

New authenticated payloads, including journal/mood/lifestyle text, preferences, plans, schedules, notifications and reports, use cryptography Fernet authenticated encryption. An encrypted binding includes owner, kind, date and ID to reject ciphertext swaps. This is application field encryption, NOT an encrypted SQLite database. Usernames/password hashes, owner IDs, dates/types/timestamps/counts, session/delivery metadata and Fernet token timestamps remain visible. Original legacy tables remain plaintext. Plaintext exists in process memory/UI and JSON/CSV downloads. An operator possessing the database and key ring can decrypt every profile; this is not end-to-end encryption or separate per-user keys.

MINDMATE_ENCRYPTION_KEYS is a comma-separated environment key ring; first key writes, all decrypt. Never commit keys or store them in SQLite. Restrict database, environment and backup access; use OS disk encryption independently if required. A password recovery code cannot recover lost encryption keys. See [recovery](DATA_RECOVERY.md) for rotation and backup limitations. Cryptography references: [Fernet/MultiFernet](https://cryptography.io/en/latest/fernet/) and [scrypt](https://docs.python.org/3/library/hashlib.html#hashlib.scrypt).

## Data flow and safety

Journal AI requires an explicit request and consumed per-request consent. Only reviewed excerpts and allowed preferences are sent; never full history, usernames or credentials. Report AI gets validated aggregates. Plan AI gets bounded preferences only and can select from approved activities; dates, duration and progress remain local. Missing credentials/errors produce labelled local fallback. Fixed-name authentication audit events omit usernames, tokens and text. UI catches errors using generic messages. SQL values are parameterized; search is in-memory. User text is rendered as text, not raw HTML. Prompt instructions inside journals are untrusted; strict validation reduces harm but cannot guarantee injection prevention.

Local phrase matching and manual Get support guidance are independent of the model. Matching content pauses routine interpretation; lack of a match is not proof of safety. Limited language coverage can miss concerning content. No risk score, diagnosis or automatic emergency contact is made. Region-specific official guidance must be reviewed before a new deployment.

## Deletion, portability and deployment

Reset requires acknowledgment and a typed phrase, deletes only the authenticated profile's records and delivery history, and leaves credentials/other users/legacy data intact. Individual mood deletion unlinks owned journals in the same transaction. Snapshots/downloads/provider records are separate copies; logical deletion is not forensic erasure. Import replace also revokes schedules. File uploads are bounded JSON or encrypted record bundles, never executable pickle. The trusted scheduler necessarily has cross-profile database/key access, but writes through short-lived authorized Vault sessions.

Explicit MINDMATE_LEGACY_LOCAL=true disables accounts for old single-user tables only: never expose it to a network. Default profile mode is still intended for a trusted local environment: no MFA, remote abuse protection, TLS termination, managed secret rotation, independent penetration test or production operational controls are provided. Browser caches and other active sessions may retain decrypted content. No public deployment or publication has occurred.
