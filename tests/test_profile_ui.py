from streamlit.testing.v1 import AppTest
from cryptography.fernet import Fernet
from mindmate.config import PROJECT_ROOT
from mindmate.database import initialize_database
from mindmate.security.auth import Accounts
from mindmate.services.vault import Vault


def test_secure_default_and_account_workflow(tmp_path,monkeypatch):
    path=tmp_path/'profile.sqlite3'; initialize_database(path)
    key=Fernet.generate_key().decode()
    monkeypatch.setenv('MINDMATE_DB_PATH',str(path)); monkeypatch.setenv('MINDMATE_ENCRYPTION_KEYS',key)
    monkeypatch.setenv('MINDMATE_LEGACY_LOCAL','false'); monkeypatch.setenv('MINDMATE_LLM_ENABLED','false')
    Accounts(path).register('synthetic','synthetic password 123')
    app=AppTest.from_file(str(PROJECT_ROOT/'app.py')).run(timeout=20)
    assert app.title[0].value=='Your private reflection space'
    app.text_input(key='account_username').set_value('synthetic')
    app.text_input(key='account_password').set_value('synthetic password 123')
    app.button[0].click().run(timeout=20)
    assert not app.exception and app.title[0].value=='Make space for how you feel.'
    app.sidebar.radio[0].set_value('Journal').run(timeout=20)
    app.text_area[0].set_value('SYNTHETIC encrypted reflection')
    app.button[0].click().run(timeout=20)
    assert not app.exception
    store=Vault(path,app.session_state['auth_token'],key)
    assert store.list('journal_entries')[0]['content']=='SYNTHETIC encrypted reflection'
    app.sidebar.button(key='account_logout').click().run(timeout=20)
    assert app.title[0].value=='Your private reflection space'
