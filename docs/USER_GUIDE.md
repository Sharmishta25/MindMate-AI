# User guide

## Start and sign in

Follow README Windows setup. Retain a valid MINDMATE_ENCRYPTION_KEYS value between launches; never generate a replacement key for existing encrypted data. Leave MINDMATE_LEGACY_LOCAL=false. Open localhost, register a username and password (at least 12 characters), and securely retain the displayed one-use recovery code. Sign in. Log out revokes the current token; inactivity does not extend the fixed 30-minute session expiry. Recover password requires the recovery code and issues a replacement code. It cannot recover lost encryption keys. Choose English/Hindi/Marathi in the sidebar; some text remains English as explained in [language coverage](AI_AND_MULTILINGUAL.md).

## Mood and journal

1. Open Mood tracker, choose UTC date/time, mood 1 (very low) to 5 (very good), stress 0–10, selected emotions and optional triggers/reflection. Save and confirm success. One check-in per date; select a saved entry to edit or acknowledge deletion.
2. Open Journal, enter date, optional title, body and optional owned mood association. Save. Choose a saved journal to view/edit/delete. Empty bodies and oversized fields are rejected. Content is plain text, encrypted in profile payloads, not application logs.
3. For optional reflection, review/redact excerpts and allowed activity preferences. Request local fallback without consent or explicitly consent to the displayed external payload. Saving alone never sends journal text. Results label model/fallback and distinguish supported evidence from uncertainty. Concerning matched language prioritizes support, not a clinical risk score. Get support remains available without a detector match.

## Dashboard and reports

Select Dashboard date range. All counts/means/medians/emotion frequencies and daily/weekly charts derive from saved check-ins. Missing days are missing observations; small samples, incomplete weeks and withheld comparisons are explained. No mood score diagnoses a condition.

Open Weekly reports, choose a current/past Monday and generate/refresh the explicit Monday–Sunday UTC snapshot. View stats, charts, reported emotions/triggers and helpful activities, then download Markdown. Optional aggregate-only AI does not create the numbers. Snapshots remain separate from later source deletion; refresh or delete them explicitly.

## Wellness and plans

Wellness activities provides optional grounding, writing and breathing exercises; stop if uncomfortable. Record completion and optional perceived helpfulness. These are general wellbeing suggestions, not treatment.

Weekly plan lets you save up to five goals, preferred curated activities, minutes per activity and weekly frequency. Select a week. Generate locally by default; optional consent sends only bounded preferences to Anthropic. The model can select approved activities, not invent instructions. Existing-plan replacement requires acknowledgment and resets progress. Expand an activity to edit its date within the week, type, duration and planned/completed/skipped status. Regenerate one activity locally. The progress fraction is completed items / total items; skipped items are separately counted. Completing a plan item does not automatically create a Wellness activity completion record.

## Lifestyle and timeline

Lifestyle records optional sleep hours, exercise minutes, screen hours and social minutes plus up to five named numeric indicators. Blank is missing, not zero. Select a record to edit/delete. Date-filtered plots show actual observations and mood; a same-day Pearson association requires seven paired days and variation. It does not establish causation.

Timeline combines owned mood, journal, activity, lifestyle, report and plan records. Filter date/type/search. Calendar displays day (filtered event count), not mood scores. Expand a record and Open record to navigate to its feature. Search is local to your decrypted records; other profiles are excluded.

## Portability, reminders and privacy

Data portability downloads plaintext JSON/CSV or an encrypted record backup. Upload only a trusted-format bundle, review validation/conflicts, choose merge/replace and type the exact confirmation. No change occurs at upload. Applying logs you out. See [recovery instructions](DATA_RECOVERY.md); backups need retained keys and account name.

Reminders saves explicit opt-in local time/timezone preferences. Only in-app notifications are supported, and a separately running worker is mandatory. Save disabled/withdrawn consent to stop future events. Mark received notifications read. Weekly scheduled reports cover the last completed UTC week. See [runtime details](SCHEDULER_DEPLOYMENT.md).

Privacy & data displays storage limitations, session clearing, acknowledged typed reset and key rotation. Reset deletes only your profile records/delivery history, leaves your account and other profiles intact, and cannot erase downloaded/backed-up/provider copies. Legacy compatibility mode is unauthenticated/plaintext and handles original tables only; use it solely on a trusted local device. No feature automatically contacts anyone.
