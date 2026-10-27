# AI design and evaluation

Current assessment version, 2026-10-27. This describes implemented behaviour, not a clinical model or a benchmarked therapy system.

## Two distinct roles for AI

**Development:** Codex assisted with source implementation, structured task refinement, debugging, tests and documentation. The actual six development user prompts, assessment-preparation prompt, final release audit prompt and attached feature-expansion prompt are preserved in [PROMPT_LOG.md](../PROMPT_LOG.md). No exact underlying Codex model identifier, prior personal experience, unseen experiments or off-thread history is invented.

**Runtime:** the optional Anthropic Messages adapter provides bounded evidence-linked selections for journal reflection and weekly narrative sections. It was selected to support a modular structured-output boundary, not because a comparison established model superiority. No live request, cost/latency benchmark or provider-quality study has been performed. A labelled local implementation keeps the app useful without credentials/network access.

## Code boundaries and flow

```text
Saved journal -> user-reviewed/redacted excerpts and activity preferences
  -> local full-entry/excerpt support checks -> explicit per-request consent
  -> reflection service -> fixed HTTPS adapter -> strict JSON parser
  -> schema + evidence + preference validation -> curated presentation
  -> labelled rule-based fallback on missing consent/configuration or failure
```

The UI checks full primary/additional selected saved journals before a truncated-excerpt request. Concerning language prioritises local support and pauses routine interpretation; writing remains editable/savable. These rules are independent of the LLM and are not clinical risk assessments.

`ai/provider.py` implements AnthropicProvider.generate() and generate_report(); orchestration services own consent/safety decisions. The lower-level adapter is internal, not an independently authenticated public API. It uses `https://api.anthropic.com/v1/messages`, x-api-key, API version 2023-06-01 and output_config.format. HTTPS certificate verification is normal; redirects and automatic retries are disabled. Response reads are bounded to 64 KiB; only a completed end-turn JSON text result is accepted, with thinking blocks discarded. Socket timeout defaults to 20 seconds, configurable 1-60; it is not a whole-request deadline. Strict parsing rejects duplicate keys/nonfinite constants.

Configuration is in [README](../README.md): enable flag, key, supported account-available model and timeout. The documented model ID is an example, not proof of account access. References: [Messages](https://platform.claude.com/docs/en/api/messages/create), [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [model IDs](https://platform.claude.com/docs/en/models/overview). Model/structured-output documentation was checked during assessment preparation; no credential check was made.

## Journal prompt contract: reflection-v2

`ai/prompts.py` separates a trusted system template, schema and JSON-serialized untrusted user data. The template defines task, input boundaries, output contract, uncertainty and safety. Journals are evidence, never executable instructions. No tools/actions are granted to the model.

| Output | Accepted scope and grounding |
| --- | --- |
| themes | Up to four distinct topics: work, connection, rest, daily routine. Each uses 1-3 exact quotes, up to 240 characters, valid source indexes and topic-keyword support |
| emotions | Up to five supported English emotion words; evidence must explicitly use I feel / I am / I'm plus that word |
| questions | One or two distinct approved optional question IDs |
| suggestions | Zero to two distinct curated activity IDs, allowed by user preferences and linked to a supported theme |

Unknown fields, wrong types/enums, fabricated quotes/source indexes, inferred feelings and disallowed activities reject the whole result. Recurrence appears only with evidence from at least two distinct supplied entries. Multiple quotes from one entry do not establish recurrence. Local semantic/length/count checks supplement provider schema constraints.

The model selects constrained evidence and IDs. Local present() renders neutral topic summaries, explicitly worded feelings, tentative recurrence, optional questions and relevance explanations. It does not show arbitrary model prose or medical recommendations. LLM attribution refers to validated selection, not authorship of every sentence.

Exact quotes and keywords cannot establish truth. Quotation, sarcasm, negation, context and hypothetical language may be misread; much genuine feeling language misses the narrow grammar/taxonomy. The UI warns that AI can be mistaken and does not establish mental state. No diagnosis, clinical sentiment score or health prediction is produced.

## Weekly prompt contract: weekly-evidence-v1

`ai/report_prompts.py` supplies aggregate count/days/coverage, mean/median, sample/ended-period flags, numbers of label/activity types and available section IDs. It excludes journal text, titles, dates, database IDs, emotion/stressor names and activity names.

The only accepted response is focus: one to three distinct available IDs from coverage, mood, emotions, triggers and activities. Extra fields, numbers, unsupported sections or duplicates cause fallback. `ai/report_narrative.py` renders all wording/numbers from unchanged engine evidence. This is explicitly labelled **LLM-selected evidence; wording and numbers rendered locally**, not unconstrained AI-authored analysis. It cannot change charts or invent figures.

Stored report snapshots are deterministic/local. Optional narrative stays in session memory and can be appended to the current Markdown download; it is not stored as an LLM report record. Separate consent and an exact aggregate preview apply.

## Consent, minimization and fallback

Journal transmission requires complete enabled configuration, pressing Request reflection and actual boolean consent for reviewed data. Up to three excerpts of 2,000 characters each plus temporary indexes and activity preferences are sent. Primary/additional history is user-selected; unrelated entries, dates/titles/IDs and mood scores are excluded. Users must redact identifying details; no automatic anonymization is claimed. Consent is consumed after use, changed payloads get new scopes and stale results are hidden.

Without consent, only local rules run. Missing/disabled configuration, rate limits, timeouts, service/network failures, malformed/truncated/refused responses and unsupported conclusions produce **Rule-based fallback (not an LLM)** with non-sensitive reasons. Obvious normalized instruction attacks are also kept local. Support-rule matches prioritise support, not a reassuring fallback assessment. Unexpected page errors are sanitized.

The app does not intentionally log private runtime prompts, journals, keys, response bodies or raw API exceptions. Generic templates and synthetic fixture payloads in the prompt log are development records, not private request logs. Results/preferences/dismissals are session-only. Provider retention follows account terms; local deletion cannot retract a request or erase provider copies. A timeout does not prove non-receipt.

## Actual iterations and evidence

The runtime templates are the first implemented versions, reflection-v2 and weekly-evidence-v1; no live A/B test compared them. User follow-up phases progressively requested grounded schemas, deterministic reporting, stronger support/consent and UI QA. Implementation refinements included malformed-envelope handling, discarded thinking blocks, normalized injection checks, duplicate/nonfinite JSON rejection, support before provider calls and full-content checks beyond excerpt limits. These are tested engineering revisions, not invented model-quality gains.

Historical counts/outcomes remain in the prompt log. The assessment-preparation command `.\.venv\Scripts\python.exe -m pytest --basetemp=tmp/pytest-assessment` passed **172 tests** on 2026-10-27; pip check passed. Fixtures/mock HTTP/providers test valid output; unknown/missing fields; unsupported feelings/topics/quotes; false recurrence; instruction attacks; malformed JSON/envelopes; timeouts/rate limits/failures; missing credentials; boolean/consumed consent; local support; dismiss/clear and UI fallback. Analytics/persistence tests establish numeric correctness separately. Test coverage percentage was not measured.

Not validated: browser visual/download behaviour, multilingual interpretation, live provider quality/privacy practices, clinical effectiveness, detector accuracy or complete injection resistance. [Safety and Privacy](SAFETY_AND_PRIVACY.md) covers storage, emergency resources and deployment limits. Future improvements require new evidence and tests, not retrospective claims.


## Final release audit (2026-10-27)

Historical pre-expansion release: **176 tests passed**, with zero failures/errors/skips, after adding four release-tool regressions. The original 172-test assessment-preparation result above is historical. Dependencies match the lock; pip check passed; the refreshed 64-package advisory audit reported no known findings. No live provider call, public deployment or submission occurred. See [release audit](RELEASE_AUDIT.md), [release checklist](RELEASE_CHECKLIST.md) and [deployment/publication instructions](DEPLOYMENT.md).


## Authenticated expansion

Current suite: 197 tests passed. plan-v1 selects only approved preferred activity IDs; deterministic code assigns dates/time. Journal reflection-v2 adds limited Hindi/Marathi evidence vocabulary; English fallback and partial localization remain visible. Models receive no account identifiers. Consent and owner access are separate gates. See [AI/language boundaries](AI_AND_MULTILINGUAL.md), [security](SECURITY_AND_PRIVACY.md) and [test evidence](TEST_REPORT.md). No live AI request or independent translation-quality evaluation was performed.
