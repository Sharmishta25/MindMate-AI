# Video presentation script

**Deliverable status: script only; no video has been recorded.** The assessment requires a video of at least two minutes. Aim for 2:30-2:55 including brief clicks; the 2-3 minute estimate is a rehearsal target, not a measured recording. Speak naturally and time the actual take. Do not claim previous experience that has not been supplied in the records.

Use only the labelled synthetic demo. Keep API keys, terminals containing secrets, personal records and unrelated browser tabs out of the recording. This script uses the genuine local fallback; a successful live LLM result must not be staged or claimed. Show mocked integration evidence separately as test evidence.

## Screen sequence (not spoken)

1. Welcome, synthetic banner, Start a check-in; save a fictional check-in on an unused UTC date.
2. Dashboard, date range containing saved entries, charts/tables and missing-data notes.
3. A saved fictional journal: review excerpt, select an activity preference, leave consent unchecked and Request reflection. Show Rule-based fallback (not an LLM).
4. Weekly reports: choose a week containing fictional records, generate and show download control. If discussing a downloaded file, actually download/open it first.
5. Show the passing test output and then Get support or Privacy & data. Keep short pauses and avoid silently waiting on a live API.

## Spoken script

<!-- SCRIPT_START -->
Hi, this is MindMate AI, a mental wellbeing application for daily self-reflection. It brings mood check-ins, journaling, activities and weekly patterns into one place. It is intended for individuals using a trusted device, and it does not diagnose or treat mental health conditions.

I used Codex as a development assistant to turn staged requirements into code, tests and documentation. The application uses Python and Streamlit, SQLite for local persistence, Pandas and NumPy for analytics, and Plotly for charts. This keeps the interface and calculations in a small, inspectable Python project.

Here, I am using clearly labelled fictional data. I can save a mood check-in with stress, emotions and an optional reflection, then edit the saved entry. The dashboard calculates averages, medians and trends from those records. Missing days are gaps, and small samples and incomplete weeks are identified rather than treated as reliable conclusions.

The optional Anthropic integration uses structured JSON. My prompts define the task, treat journal text as untrusted data, require evidence, and restrict the output. The application validates exact quotes and allowed choices, then distinguishes explicitly stated feelings from tentative topics. This is bounded reflection, not an open-ended therapist chatbot.

For this demonstration, I leave external-sharing consent unchecked. The result is explicitly labelled rule-based fallback. Valid provider responses, missing credentials, timeouts and malformed output were verified with mocked tests; I have not performed a live model-quality evaluation.

Development progressed from the foundation to local workflows, grounded AI, reports, safety and interface refinement. Tests caught a report-view syntax error, which was corrected. Another refinement opens a newly saved journal in edit mode, avoiding unintended duplicate entries from repeated saves.

Here is the weekly report generated from stored evidence, with an explicit period and Markdown export. AI cannot invent its numbers, and optional scheduling needs a separate worker.

The latest full suite passed 197 tests. Consent is required for external text sharing, local support guidance is always accessible, and nothing automatically contacts anyone. New profiles use login and encrypted payloads. Metadata and legacy data remain visible. Lifestyle, plans, portability and in-app reminders work; language coverage is partial. This remains a local prototype.
<!-- SCRIPT_END -->

The spoken draft contains **345 words**. At an assumed 130 words/minute it takes about 2:39 before click pauses; this is an estimate, not a recorded duration. Rehearse and trim pauses as needed to stay near three minutes while exceeding the required two-minute minimum.

## Rehearsal checks

- Follow [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) before recording. Ensure every narrated action actually occurs.
- Show one coherent workflow, not every feature. Use the visible date ranges rather than hardcoded claims about current sample counts.
- The brief asks whether prior experience influenced decisions. No personal history is available here; if relevant, add one truthful sentence about your own experience and recheck duration.
- Do not call fallback an LLM response or claim user research, clinical validation, complete injection prevention, model superiority, a published website, or a submitted application.
- After recording, verify audio, visibility, actual duration >=2 minutes and that any shared link is accessible to reviewers. The script does not establish that a recording exists.
