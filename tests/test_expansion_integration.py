"""Synthetic authenticated integration and rollback checks."""
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
import pytest
from cryptography.fernet import Fernet
from streamlit.testing.v1 import AppTest
from mindmate.config import PROJECT_ROOT
from mindmate.database import initialize_database,connect
from mindmate.security.auth import Accounts
from mindmate.services.vault import Vault,UserReports
from mindmate.services.portability import export_json,preview_import,apply_import,restore_payload
from mindmate.services.scheduling import configure,run_once
from mindmate.services.wellbeing import save_lifestyle,lifestyle_analysis
from scripts.migrate_legacy import copy_legacy


def profile(tmp_path):
    path=tmp_path/'synthetic.sqlite3'; initialize_database(path)
    auth=Accounts(path); auth.register('synthetic','synthetic password 123')
    key=Fernet.generate_key().decode()
    return Vault(path,auth.login('synthetic','synthetic password 123'),key),key


def test_secure_screens_and_persistence(tmp_path,monkeypatch):
    store,key=profile(tmp_path)
    monkeypatch.setenv('MINDMATE_DB_PATH',str(store.path)); monkeypatch.setenv('MINDMATE_ENCRYPTION_KEYS',key)
    monkeypatch.setenv('MINDMATE_LEGACY_LOCAL','false'); monkeypatch.setenv('MINDMATE_LLM_ENABLED','false')
    app=AppTest.from_file(str(PROJECT_ROOT/'app.py'))
    app.session_state['auth_token']=store.token; app.run(timeout=20)
    for page in ['Timeline','Lifestyle','Weekly plan','Data portability','Reminders','Privacy & data']:
        app.sidebar.radio[0].set_value(page).run(timeout=20)
        assert not app.exception, page
    app.sidebar.radio[0].set_value('Lifestyle').run()
    next(b for b in app.button if b.label=='Save lifestyle entry').click().run()
    assert len(store.records('lifestyle'))==1 and not app.exception
    app.sidebar.radio[0].set_value('Weekly plan').run()
    next(b for b in app.button if b.label=='Generate weekly plan').click().run()
    assert len(store.records('plan'))==1 and not app.exception
    app.sidebar.radio[0].set_value('Timeline').run()
    app.radio[0].set_value('Calendar').run()
    assert not app.exception and len(app.dataframe)==1
    restarted=Vault(store.path,store.token,key)
    assert len(restarted.records('plan'))==1
    app.sidebar.selectbox(key='ui_language').set_value('hi').run()
    assert not app.exception and store.records('preferences')[0]['language']=='hi'
    app.sidebar.selectbox(key='ui_language').set_value('mr').run()
    assert not app.exception and store.records('preferences')[0]['language']=='mr'


def test_import_rollback_rotation_and_atomic_delete(tmp_path):
    store,key=profile(tmp_path)
    mid=store.save_mood('2026-10-20',3,2,['Calm'],recorded_at='2026-10-20T12:00:00Z')
    jid=store.save_journal('2026-10-20','Synthetic','SYNTHETIC journal',mid)
    raw=export_json(store); preview=preview_import(store,raw)
    with patch.object(store.cipher,'encrypt',side_effect=ValueError('synthetic failure')):
        with pytest.raises(ValueError): apply_import(store,raw,'replace','REPLACE MY DATA',preview['fingerprint'])
        with pytest.raises(ValueError): store.delete('mood_entries',mid)
    assert store.get('journal',jid)['mood_entry_id']==mid and store.get('mood',mid)
    new=Fernet.generate_key().decode(); rotating=Vault(store.path,store.token,new+','+key); rotating.rotate()
    assert Vault(store.path,store.token,new).get('journal',jid)['content']=='SYNTHETIC journal'
    with pytest.raises(ValueError): restore_payload(rotating,b'\xff')
    rotating.delete('mood_entries',mid)
    assert rotating.get('journal',jid)['mood_entry_id'] is None


def test_scheduler_failure_retry_report_and_no_duplicates(tmp_path):
    store,key=profile(tmp_path); configure(store,'report','UTC',9,0,0,True,True)
    now=datetime(2026,10,26,10,tzinfo=timezone.utc)
    with patch.object(UserReports,'generate',side_effect=RuntimeError('synthetic failure')):
        assert run_once(store.path,key,now)==0
    assert run_once(store.path,key,now+timedelta(seconds=30))==0
    assert run_once(store.path,key,now+timedelta(seconds=61))==1
    assert run_once(store.path,key,now+timedelta(seconds=400))==0
    assert len(store.records('report'))==1 and store.records('report')[0]['_date']=='2026-10-19'
    with connect(store.path) as db:
        row=db.execute('SELECT status,attempts FROM deliveries').fetchone()
        assert tuple(row)==('done',2)


def test_paired_lifestyle_and_legacy_assignment(tmp_path):
    store,key=profile(tmp_path)
    for i in range(7):
        d=f'2026-10-{10+i}'
        store.save_mood(d,i%5+1,2,[],recorded_at=d+'T12:00:00Z')
        save_lifestyle(store,d,{'sleep_hours':float(i+1)})
    rows,stats=lifestyle_analysis(store,'2026-10-10','2026-10-16')
    assert stats['sleep_hours']['paired_days']==7 and stats['sleep_hours']['correlation'] is not None
    with pytest.raises(ValueError): copy_legacy(store,'wrong')
    from mindmate.services.core import Store
    legacy=Store(store.path)
    legacy.save_journal('2026-10-20','Synthetic legacy','SYNTHETIC preserved source')
    assert copy_legacy(store,'ASSIGN ALL LEGACY DATA TO THIS ACCOUNT')==1
    assert copy_legacy(store,'ASSIGN ALL LEGACY DATA TO THIS ACCOUNT')==0
    assert legacy.list('journal_entries')[0]['content']=='SYNTHETIC preserved source'
    assert store.records('journal')[0]['content']=='SYNTHETIC preserved source'
