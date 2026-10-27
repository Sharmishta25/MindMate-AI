"""Anthropic Messages adapter. Fixed HTTPS destination; no content logging/retries."""
import json
import socket
import http.client
import urllib.request
import urllib.error
from mindmate.config import Settings
from mindmate.ai.json_utils import loads
from mindmate.ai.prompts import SYSTEM, SCHEMA, user_payload


class ProviderError(Exception):
    """Only non-sensitive, stable error codes may cross this boundary."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError("service_failure")


class AnthropicProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, excerpts, preferences, language="en"):
        if not self.settings.llm_ready:
            raise ProviderError("missing_configuration")
        return self._request(SYSTEM, user_payload(excerpts, preferences, language), SCHEMA)

    def generate_report(self, evidence):
        from mindmate.ai import report_prompts
        if not self.settings.llm_ready:
            raise ProviderError("missing_configuration")
        return self._request(report_prompts.SYSTEM, json.dumps(report_prompts.payload(evidence)), report_prompts.SCHEMA)

    def _request(self, system, user, schema):
        body = {"model": self.settings.llm_model, "max_tokens": 1800,
                "system": system, "messages": [{"role": "user", "content": user}],
                "output_config": {"format": {"type": "json_schema", "schema": schema}}}
        request = urllib.request.Request("https://api.anthropic.com/v1/messages",
            data=json.dumps(body).encode("utf-8"), method="POST",
            headers={"content-type": "application/json", "x-api-key": self.settings.llm_api_key,
                     "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=self.settings.llm_timeout_seconds) as response:
                raw = response.read(65537)
            if len(raw) > 65536:
                raise ProviderError("invalid_output")
            envelope = loads(raw)
            if envelope.get("stop_reason") != "end_turn":
                raise ProviderError("invalid_output")
            blocks = envelope["content"]
            if not isinstance(blocks, list) or any(not isinstance(block, dict) for block in blocks):
                raise ProviderError("invalid_output")
            texts = [block["text"] for block in blocks if block.get("type") == "text"]
            if len(texts) != 1:
                raise ProviderError("invalid_output")
            return loads(texts[0])
        except urllib.error.HTTPError as error:
            raise ProviderError("rate_limit" if error.code == 429 else "service_failure") from None
        except (TimeoutError, socket.timeout):
            raise ProviderError("timeout") from None
        except urllib.error.URLError as error:
            raise ProviderError("timeout" if isinstance(error.reason, TimeoutError) else "service_failure") from None
        except (ValueError, KeyError, TypeError, AttributeError, UnicodeError, RecursionError):
            raise ProviderError("invalid_output") from None
        except (OSError, http.client.HTTPException):
            raise ProviderError("service_failure") from None


def availability_message(settings: Settings) -> str:
    if settings.llm_ready:
        return "AI configured | External requests require explicit consent"
    return "Local mode | No AI API key required"
