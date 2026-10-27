"""Consent gate, grounded validation and explicitly local fallback; no persistence/logs."""
from dataclasses import dataclass
import re
from mindmate.ai.prompts import THEMES, EMOTIONS, QUESTIONS, SUGGESTIONS, SCHEMA, VERSION
from mindmate.ai.provider import AnthropicProvider, ProviderError
from mindmate.safety.support import support_route, normalize
from mindmate.ai.languages import topic_words, explicit_feeling

MAX_EXCERPT = 2000
MAX_ENTRIES = 3
INJECTION = re.compile(r"ignore.{0,40}(instructions|rules|previous)|system\s*:|developer\s*:|<\s*/?\s*(system|assistant)|reveal.{0,30}(prompt|secret|key)|diagnos|you (have|are suffering from)|medication|suicid|self.harm|kill myself", re.I | re.S)


@dataclass(frozen=True)
class ReflectionResult:
    source: str
    reason: str
    data: dict
    prompt_version: str = VERSION
    support_urgent: bool = False


def _shape(value, schema):
    kind = schema["type"]
    if kind == "object":
        if not isinstance(value, dict) or set(value) != set(schema["properties"]):
            raise ValueError("Invalid fields")
        for key, sub in schema["properties"].items():
            _shape(value[key], sub)
    elif kind == "array":
        if not isinstance(value, list) or len(value) > 12:
            raise ValueError("Invalid array")
        for item in value:
            _shape(item, schema["items"])
    elif kind == "integer":
        if type(value) is not int:
            raise ValueError("Invalid integer")
    elif kind == "string":
        if not isinstance(value, str) or not value.strip() or len(value) > 240:
            raise ValueError("Invalid string")
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError("Invalid choice")


def _keyword(text, words):
    return bool(re.search(r"\b(?:" + "|".join(map(re.escape, words)) + r")\b", text, re.I))


def _emotion(text, emotion, language="en"):
    return explicit_feeling(text,emotion,language) or bool(re.search(r"\b(?:I feel|I am|I'm)\s+" + re.escape(emotion) + r"\b", text, re.I))


def validate(data, excerpts, preferences, language="en"):
    _shape(data, SCHEMA)
    if len(data["themes"]) > 4 or len(data["emotions"]) > 5 or not 1 <= len(data["questions"]) <= 2 or len(data["suggestions"]) > 2:
        raise ValueError("Invalid counts")

    def evidence(item):
        index, quote = item["entry"], item["quote"]
        if not 0 <= index < len(excerpts) or quote not in excerpts[index] or INJECTION.search(normalize(quote)):
            raise ValueError("Unsupported evidence")
        return quote

    seen = set()
    for item in data["themes"]:
        theme = item["theme"]
        if theme in seen or not 1 <= len(item["evidence"]) <= 3:
            raise ValueError("Invalid theme")
        seen.add(theme)
        ids = set()
        for citation in item["evidence"]:
            if citation["entry"] in ids or not _keyword(evidence(citation), topic_words(theme,language,THEMES[theme])):
                raise ValueError("Unsupported theme")
            ids.add(citation["entry"])
    emotions = set()
    for item in data["emotions"]:
        if item["emotion"] in emotions or not _emotion(evidence(item["evidence"]), item["emotion"],language):
            raise ValueError("Emotion must be explicitly stated")
        emotions.add(item["emotion"])
    if len(set(data["questions"])) != len(data["questions"]):
        raise ValueError("Duplicate questions")
    activities = set()
    for item in data["suggestions"]:
        if item["activity"] not in preferences or item["theme"] not in seen or item["activity"] in activities:
            raise ValueError("Unsupported suggestion")
        activities.add(item["activity"])
    return data


def fallback(excerpts, preferences, language="en"):
    data = {"themes": [], "emotions": [], "questions": ["needs", "small_step"], "suggestions": []}
    # Refuse to extract from directive/clinical/high-risk passages. No crisis classification is claimed.
    sentences = [[s.strip() for s in re.split(r"[.!?\n]", value) if 0 < len(s.strip()) <= 240 and not INJECTION.search(normalize(s))] for value in excerpts]
    for theme, keywords in THEMES.items():
        citations = []
        for index, parts in enumerate(sentences):
            match = next((s for s in parts if _keyword(s, topic_words(theme,language,keywords))), None)
            if match:
                citations.append({"entry": index, "quote": match})
        if citations:
            data["themes"].append({"theme": theme, "evidence": citations})
    for emotion in EMOTIONS:
        match = next(((i, s) for i, parts in enumerate(sentences) for s in parts if _emotion(s, emotion,language)), None)
        if match and len(data["emotions"]) < 5:
            data["emotions"].append({"emotion": emotion, "evidence": {"entry": match[0], "quote": match[1]}})
    for activity in preferences[:2]:
        if data["themes"]:
            data["suggestions"].append({"activity": activity, "theme": data["themes"][0]["theme"]})
    return validate(data, excerpts, preferences,language)


def reflect(excerpts, preferences, settings, *, consent=False, provider=None, language="en"):
    if language not in {"en","hi","mr"}:
        raise ValueError("Unsupported reflection language")
    if not isinstance(excerpts, list) or not 1 <= len(excerpts) <= MAX_ENTRIES or any(not isinstance(x, str) or not x.strip() or len(x) > MAX_EXCERPT for x in excerpts):
        raise ValueError("Select 1-3 nonempty excerpts of at most 2,000 characters each")
    if not isinstance(preferences, list) or len(preferences) > 3 or any(p not in SUGGESTIONS for p in preferences) or len(set(preferences)) != len(preferences):
        raise ValueError("Select valid activity preferences")
    if type(consent) is not bool:
        raise ValueError("Consent must be explicitly true or false")
    route = support_route(*excerpts)
    if route.show_support:
        return ReflectionResult("Local support guidance (not an assessment)", "support_pathway",
                                {"themes": [], "emotions": [], "questions": [], "suggestions": []},
                                support_urgent=route.urgent)
    reason = "consent_not_given"
    if consent and settings.llm_ready:
        if any(INJECTION.search(normalize(x)) for x in excerpts):
            reason = "input_boundary"
        else:
            try:
                client = provider or AnthropicProvider(settings)
                data = client.generate(excerpts,preferences) if language=="en" else client.generate(excerpts,preferences,language=language)
                return ReflectionResult("LLM", "validated", validate(data, excerpts, preferences,language))
            except ProviderError as error:
                reason = str(error) if str(error) in {"missing_configuration", "timeout", "rate_limit", "invalid_output", "service_failure"} else "service_failure"
            except (ValueError, TypeError, KeyError, IndexError, RecursionError):
                reason = "invalid_output"
    elif consent:
        reason = "missing_configuration"
    return ReflectionResult("Rule-based fallback (not an LLM)", reason, fallback(excerpts, preferences,language))


def present(result):
    """Only curated labels and verified evidence enter narrative output."""
    data = result.data
    names = [x["theme"].replace("_", " ") for x in data["themes"]]
    summary = "Possible topics in the supplied excerpts: " + ", ".join(names) + "." if names else "No supported topics were identified within this limited reflection vocabulary."
    recurring = [x["theme"].replace("_", " ") for x in data["themes"] if len({e["entry"] for e in x["evidence"]}) >= 2]
    suggestions = []
    for item in data["suggestions"]:
        title, instruction = SUGGESTIONS[item["activity"]]
        theme = item["theme"].replace("_", " ")
        suggestions.append({"id": item["activity"], "title": title, "instruction": instruction,
                            "why": f"You allowed this activity and your excerpts mention {theme}. It may offer a space to pause and reflect; it may not suit you."})
    return {"summary": summary, "stated_emotions": [x["emotion"] for x in data["emotions"]],
            "recurring": recurring, "questions": [QUESTIONS[x] for x in data["questions"]], "suggestions": suggestions}
