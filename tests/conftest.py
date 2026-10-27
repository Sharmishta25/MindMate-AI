"""Existing local-mode UI regressions remain explicit compatibility-mode tests.
New authenticated-profile suites do not enable this operator-only mode.
"""
import pytest

LEGACY_MODULES={'test_app','test_core_ui','test_ai_ui','test_reports_ui','test_safety_privacy_ui','test_ui_quality'}

@pytest.fixture(autouse=True)
def explicit_legacy_compatibility_for_existing_ui(request,monkeypatch):
    if request.module.__name__.split('.')[-1] in LEGACY_MODULES:
        monkeypatch.setenv('MINDMATE_LEGACY_LOCAL','true')
