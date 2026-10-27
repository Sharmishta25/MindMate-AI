import pytest
from mindmate.database import initialize_database,connect
from mindmate.security.auth import Accounts,AuthError,password_hash,verify_password


def test_password_hash_and_no_sensitive_logs(tmp_path,caplog):
    path=tmp_path/'accounts.sqlite3'; initialize_database(path)
    accounts=Accounts(path)
    uid,code=accounts.register('Synthetic','synthetic password 123')
    with connect(path) as db:
        row=db.execute('SELECT * FROM users').fetchone()
        assert row['password_hash']!='synthetic password 123'
        assert row['recovery_hash']!=code
    assert verify_password('synthetic password 123',row['password_hash'])
    assert not verify_password('wrong password 123',row['password_hash'])
    token=accounts.login('SYNTHETIC','synthetic password 123')
    assert accounts.current(token)['id']==uid
    assert code not in caplog.text and token not in caplog.text and 'synthetic password' not in caplog.text


def test_expiry_logout_and_recovery(tmp_path):
    path=tmp_path/'accounts.sqlite3'; initialize_database(path)
    now=[1000]; accounts=Accounts(path,ttl=60,clock=lambda:now[0])
    uid,code=accounts.register('person','synthetic password 123')
    token=accounts.login('person','synthetic password 123')
    now[0]+=61
    with pytest.raises(AuthError): accounts.current(token)
    token=accounts.login('person','synthetic password 123')
    replacement=accounts.recover('person',code,'changed password 123')
    with pytest.raises(AuthError): accounts.current(token)
    with pytest.raises(AuthError): accounts.recover('person',code,'another password 123')
    token=accounts.login('person','changed password 123'); accounts.logout(token)
    with pytest.raises(AuthError): accounts.current(token)
    assert replacement!=code


def test_lockout_and_validation(tmp_path):
    path=tmp_path/'accounts.sqlite3'; initialize_database(path)
    now=[1000]; accounts=Accounts(path,clock=lambda:now[0]); accounts.register('person','synthetic password 123')
    for _ in range(5):
        with pytest.raises(AuthError): accounts.login('person','wrong password 123')
    with pytest.raises(AuthError): accounts.login('person','synthetic password 123')
    now[0]+=301
    assert accounts.login('person','synthetic password 123')
    with pytest.raises(ValueError): accounts.register('../invalid','synthetic password 123')
    with pytest.raises(ValueError): accounts.register('valid','short')
