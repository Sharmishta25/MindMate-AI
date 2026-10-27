import pytest
from unittest.mock import Mock
from mindmate.i18n import t,resource
from mindmate.ai.reflection import reflect
from mindmate.config import load_settings
from mindmate.ai.provider import ProviderError
from mindmate.safety.support import support_route


def test_resources_switch_unicode_and_missing_key():
    assert t('Journal','hi')=='दैनंदिनी' and t('Journal','mr')=='दैनंदिनी'
    assert t('missing key','hi')=='missing key'
    assert t('Journal','unknown')=='Journal'
    assert len(resource('en'))>200


@pytest.mark.parametrize('language,entry',[('hi','मैं शांत हूँ। आज काम के बाद आराम किया।'),('mr','मला शांत वाटते. कामानंतर विश्रांती घेतली.')])
def test_multilingual_fallback_and_failure(language,entry):
    result=reflect([entry],[],load_settings({}),language=language)
    assert any(x['emotion']=='calm' for x in result.data['emotions'])
    assert any(x['evidence']['quote'] in entry for x in result.data['emotions'])
    provider=Mock(); provider.generate.side_effect=ProviderError('timeout')
    config=load_settings({'MINDMATE_LLM_ENABLED':'true','MINDMATE_LLM_API_KEY':'synthetic','MINDMATE_LLM_MODEL':'synthetic'})
    failed=reflect([entry],[],config,consent=True,provider=provider,language=language)
    assert failed.reason=='timeout' and failed.source.startswith('Rule-based')


def test_limited_multilingual_support_not_safety_certification():
    assert support_route('मुझे आत्महत्या के विचार आते हैं').show_support
    assert support_route('मला स्वतःला इजा करावीशी वाटते').show_support
