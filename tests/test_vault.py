import pytest
from cryptography.fernet import Fernet
from mindmate.database import initialize_database,connect
from mindmate.security.auth import Accounts,AuthError
from mindmate.security.crypto import Cipher
from mindmate.services.vault import Vault,UserReports
from mindmate.services.core import DataError


def setup(tmp_path):
    path=tmp_path/'vault.sqlite3'; initialize_database(path); accounts=Accounts(path)
    accounts.register('alice','synthetic password 123'); accounts.register('bob','synthetic password 123')
    key=Fernet.generate_key().decode()
    return path,key,Vault(path,accounts.login('alice','synthetic password 123'),key),Vault(path,accounts.login('bob','synthetic password 123'),key)


def test_cross_user_read_write_export_delete_and_reset(tmp_path):
    path,key,a,b=setup(tmp_path)
    jid=a.save_journal('2026-10-27','Synthetic','SYNTHETIC private Unicode नमस्ते')
    assert not b.records()
    for operation in [lambda:b.get('journal',jid),lambda:b.save_journal('2026-10-27','x','Changed',entry_id=jid),lambda:b.remove('journal',jid)]:
        with pytest.raises(AuthError): operation()
    b.reset('DELETE ALL MY DATA')
    assert a.get('journal',jid)['content'].endswith('नमस्ते')
    with connect(path) as db:
        raw=db.execute('SELECT ciphertext FROM vault_records').fetchone()[0]
        assert 'SYNTHETIC private' not in raw
    reopened=Vault(path,a.token,key)
    assert reopened.get('journal',jid)['content']==a.get('journal',jid)['content']
    with pytest.raises(AuthError): Vault(path,None,key)


def test_crypto_wrong_key_corruption_and_rotation(tmp_path):
    old=Fernet.generate_key().decode(); new=Fernet.generate_key().decode(); cipher=Cipher(old)
    token=cipher.encrypt({'value':'SYNTHETIC'}); assert cipher.decrypt(token)['value']=='SYNTHETIC'
    with pytest.raises(DataError): Cipher('invalid')
    with pytest.raises(DataError): Cipher(new).decrypt(token)
    with pytest.raises(DataError): cipher.decrypt(token[:-3]+'bad')
    rotated=Cipher(new+','+old).rotate(token)
    assert Cipher(new).decrypt(rotated)['value']=='SYNTHETIC'


def test_ciphertext_context_swap_is_rejected(tmp_path):
    path,key,a,b=setup(tmp_path)
    one=a.save_journal('2026-10-27','S','SYNTHETIC Alice')
    two=b.save_journal('2026-10-27','S','SYNTHETIC Bob')
    with connect(path) as db:
        value=db.execute('SELECT ciphertext FROM vault_records WHERE id=?',(one,)).fetchone()[0]
        db.execute('UPDATE vault_records SET ciphertext=? WHERE id=?',(value,two))
    with pytest.raises(DataError): b.get('journal',two)
