from pathlib import Path
import pytest
from mindmate.config import PROJECT_ROOT, load_settings


def test_defaults_work_without_api_key():
    settings = load_settings({})
    assert settings.database_path == PROJECT_ROOT / "data/mindmate.sqlite3"
    assert not settings.llm_ready


def test_optional_ai_requires_opt_in_and_complete_configuration():
    values = {"MINDMATE_LLM_API_KEY": "test-secret", "MINDMATE_LLM_MODEL": "test-model"}
    assert not load_settings(values).llm_ready
    settings = load_settings({**values, "MINDMATE_LLM_ENABLED": "true"})
    assert settings.llm_ready
    assert "test-secret" not in repr(settings)
    assert not load_settings({"MINDMATE_LLM_ENABLED": "true"}).llm_ready


@pytest.mark.parametrize("values", [
    {"MINDMATE_DB_PATH": "../outside.sqlite3"},
    {"MINDMATE_DB_PATH": ""},
    {"MINDMATE_LLM_ENABLED": "yes"},
])
def test_invalid_configuration_rejected(values):
    with pytest.raises(ValueError):
        load_settings(values)
