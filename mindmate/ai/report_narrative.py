"""The model may choose evidence sections; all prose/numbers are rendered locally."""
from mindmate.ai.provider import AnthropicProvider, ProviderError
from mindmate.ai.reflection import _shape
from mindmate.ai.report_prompts import SCHEMA, VERSION, available


def narrative(evidence, settings, *, consent=False, provider=None):
    if type(consent) is not bool:
        raise ValueError("Consent must be explicitly true or false")
    supported = available(evidence)
    focus = supported[:3]
    source, reason = "Rule-based fallback (not an LLM)", "consent_not_given"
    if consent and settings.llm_ready:
        try:
            response = (provider or AnthropicProvider(settings)).generate_report(evidence)
            _shape(response, SCHEMA)
            proposed = response["focus"]
            if not 1 <= len(proposed) <= 3 or len(set(proposed)) != len(proposed) or any(x not in supported for x in proposed):
                raise ValueError("Unsupported sections")
            focus, source, reason = proposed, "LLM-selected evidence; wording and numbers rendered locally", "validated"
        except ProviderError as error:
            reason = str(error) if str(error) in {"timeout", "rate_limit", "service_failure", "invalid_output", "missing_configuration"} else "service_failure"
        except (ValueError, TypeError, KeyError, IndexError, RecursionError):
            reason = "invalid_output"
    elif consent:
        reason = "missing_configuration"
    statements = {"coverage": f"Recorded check-ins cover {evidence['recorded_days']} of {evidence['days']} calendar days. Unrecorded days cannot tell us how you felt.",
                  "mood": f"The mean of your recorded mood ratings is {evidence['average']:.2f} and the median is {evidence['median']:.2f} on the 1-5 scale." if evidence["count"] else "",
                  "emotions": "Your selected emotion labels describe what you chose to report, not an independent assessment of your feelings.",
                  "triggers": "Stressor labels reflect your own reports. Frequency alone cannot establish what caused a mood change.",
                  "activities": "Some completed activities were personally rated helpful. Those ratings do not establish a treatment effect."}
    text = f"Source: {source}. Prompt: {VERSION}." + (f" Fallback reason: {reason}." if reason != "validated" else "") + "\n\n" + "\n\n".join(statements[x] for x in focus)
    return {"source": source, "reason": reason, "text": text, "focus": focus}
