import pytest
from cryptography.fernet import Fernet
from mindmate.database import initialize_database
from mindmate.security.auth import Accounts,AuthError
from mindmate.services.vault import Vault
from mindmate.services.portability import *


def test_export_preview_merge_replace_and_backup(tmp_path):
    path=tmp_path/'portable.sqlite3'; initialize_database(path); auth=Accounts(path); key=Fernet.generate_key().decode()
    auth.register('alice','synthetic password 123'); auth.register('bob','synthetic password 123')
    a=Vault(path,auth.login('alice','synthetic password 123'),key); b=Vault(path,auth.login('bob','synthetic password 123'),key)
    mid=a.save_mood('2026-10-20',3,2,['Calm'],recorded_at='2026-10-20T12:00:00Z')
    a.save_journal('2026-10-20','Synthetic','SYNTHETIC Unicode नमस्ते',mid)
    raw=export_json(a); p=preview_import(a,raw)
    assert p['records']==2 and p['conflicts']==2
    assert apply_import(a,raw,'merge','IMPORT MY DATA',p['fingerprint'])==0
    assert apply_import(a,raw,'replace','REPLACE MY DATA',p['fingerprint'])==2
    assert a.records('journal')[0]['mood_entry_id']==a.records('mood')[0]['id']
    assert not b.records()
    encrypted=backup(a); assert b'SYNTHETIC Unicode' not in encrypted
    assert validate_bundle(restore_payload(a,encrypted))['version']==1
    with pytest.raises(AuthError): restore_payload(b,encrypted)
    with pytest.raises(ValueError): apply_import(a,raw,'replace','wrong',p['fingerprint'])
    with pytest.raises(ValueError): apply_import(a,raw,'merge','IMPORT MY DATA','wrong-hash')
    with pytest.raises(ValueError): validate_bundle(b'{"version":99}')
    assert export_csv(a).startswith(b'\xef\xbb\xbf')
