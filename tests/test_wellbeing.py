import pytest
from cryptography.fernet import Fernet
from mindmate.database import initialize_database
from mindmate.security.auth import Accounts
from mindmate.services.vault import Vault
from mindmate.services.wellbeing import *
from mindmate.config import load_settings


def owner(tmp_path):
    path=tmp_path/'wellbeing.sqlite3'; initialize_database(path); a=Accounts(path); a.register('synthetic','synthetic password 123')
    return Vault(path,a.login('synthetic','synthetic password 123'),Fernet.generate_key().decode())


def test_lifestyle_missing_and_timeline_search(tmp_path):
    store=owner(tmp_path)
    lid=save_lifestyle(store,'2026-10-20',{'sleep_hours':None,'screen_hours':2})
    store.save_journal('2026-10-20','Synthetic','SYNTHETIC Unicode नमस्ते')
    rows,stats=lifestyle_analysis(store,'2026-10-01','2026-10-31')
    assert stats['sleep_hours']['paired_days']==0 and stats['screen_hours']['correlation'] is None
    assert len(timeline(store,'2026-10-01','2026-10-31',['journal'],'नमस्ते'))==1
    assert not timeline(store,'2026-10-01','2026-10-31',query='absent')
    save_lifestyle(store,'2026-10-20',{'sleep_hours':8},lid)
    with pytest.raises(ValueError): save_lifestyle(store,'2026-10-21',{'sleep_hours':25})
    with pytest.raises(ValueError): save_lifestyle(store,'2026-10-21',{'custom':{'x':float('nan')}})


def test_plan_edit_skip_regenerate_and_progress(tmp_path):
    store=owner(tmp_path); preferences(store,['SYNTHETIC pause'],['writing','grounding'],5,3)
    pid=generate_plan(store,'2026-10-20',load_settings({}))
    record=store.get('plan',pid)
    assert len(record['items'])==3 and all(x['minutes']<=5 for x in record['items'])
    assert record['source'].startswith('Rule-based')
    update_plan_item(store,pid,0,'writing',4,'completed')
    update_plan_item(store,pid,1,'grounding',3,'skipped')
    progress=plan_progress(store.get('plan',pid)); assert progress['completed']==1 and progress['skipped']==1 and progress['fraction']==1/3
    update_plan_item(store,pid,1,'grounding',3,'planned',regenerate=True)
    with pytest.raises(ValueError): update_plan_item(store,pid,0,'writing',99,'planned')

    from unittest.mock import Mock
    configured=load_settings({'MINDMATE_LLM_ENABLED':'true','MINDMATE_LLM_API_KEY':'synthetic-test-key','MINDMATE_LLM_MODEL':'synthetic-model'})
    provider=Mock(); provider._request.return_value={'activities':['writing','grounding','writing']}
    generate_plan(store,'2026-10-20',configured,False,provider)
    provider._request.assert_not_called()
    pid=generate_plan(store,'2026-10-20',configured,True,provider)
    assert store.get('plan',pid)['source'].startswith('LLM-selected')
    provider._request.return_value={'activities':['unsafe unsupported activity']}
    pid=generate_plan(store,'2026-10-20',configured,True,provider)
    assert store.get('plan',pid)['reason']=='unavailable_or_invalid'
    provider._request.side_effect=ProviderError('timeout')
    pid=generate_plan(store,'2026-10-20',configured,True,provider)
    assert store.get('plan',pid)['source'].startswith('Rule-based')
