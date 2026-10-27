"""Local account authentication. No email delivery or public-hosting assurance."""
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from mindmate.database import connect
from mindmate.services.core import DataError


class AuthError(DataError):
    pass


def _digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _password(value):
    if not isinstance(value,str) or not 12 <= len(value) <= 256:
        raise ValueError("Use a password of 12-256 characters")
    try:
        return value.encode('utf-8')
    except UnicodeError:
        raise ValueError("Password must contain valid Unicode") from None


def password_hash(password):
    salt=secrets.token_bytes(16)
    result=hashlib.scrypt(_password(password),salt=salt,n=32768,r=8,p=1,dklen=32,maxmem=67108864)
    return 'scrypt$32768$8$1$'+salt.hex()+'$'+result.hex()


def verify_password(password,encoded):
    try:
        _,n,r,p,salt,digest=encoded.split('$')
        if (int(n),int(r),int(p)) != (32768,8,1):
            return False
        actual=hashlib.scrypt(_password(password),salt=bytes.fromhex(salt),n=32768,r=8,p=1,dklen=32,maxmem=67108864)
        return hmac.compare_digest(actual,bytes.fromhex(digest))
    except (ValueError,TypeError,UnicodeError):
        return False


def _username(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{3,40}',value):
        raise ValueError("Username: 3-40 letters, numbers, dots, underscores or hyphens")
    return value.casefold()


def event(name):
    # Fixed event names only; no username, token, password, key or entry payload.
    if name not in {'registered','login_failed','login_ok','logout','password_reset'}:
        raise ValueError('Unknown audit event')
    logging.getLogger('mindmate.audit').info(json.dumps({'event':name}))


class Accounts:
    def __init__(self,path,ttl=1800,clock=time.time):
        self.path,self.ttl,self.clock=path,ttl,clock

    def register(self,username,password):
        username=_username(username)
        encoded=password_hash(password)
        recovery=secrets.token_urlsafe(32)
        try:
            with connect(self.path) as db:
                uid=db.execute('INSERT INTO users(username,password_hash,recovery_hash) VALUES (?,?,?)',(username,encoded,_digest(recovery))).lastrowid
        except Exception as error:
            import sqlite3
            if isinstance(error,sqlite3.Error):
                raise AuthError('Unable to create account; choose another username or check storage') from None
            raise
        event('registered')
        return uid,recovery

    def login(self,username,password):
        username=_username(username)
        now=self.clock()
        with connect(self.path) as db:
            row=db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
            accepted=row is not None and row['locked_until']<=now and verify_password(password,row['password_hash'])
            if not accepted:
                if row:
                    failures=row['failures']+1
                    db.execute('UPDATE users SET failures=?,locked_until=? WHERE id=?',(failures,now+300 if failures>=5 else row['locked_until'],row['id']))
                else:
                    hashlib.scrypt(b'dummy-password',salt=b'constant-dummy-1',n=32768,r=8,p=1,dklen=32,maxmem=67108864)
            else:
                token=secrets.token_urlsafe(32)
                db.execute('UPDATE users SET failures=0,locked_until=0 WHERE id=?',(row['id'],))
                db.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES (?,?,?)',(_digest(token),row['id'],now+self.ttl))
        if not accepted:
            event('login_failed')
            raise AuthError('Login failed or temporarily locked. Check credentials or retry later.')
        event('login_ok')
        return token

    def current(self,token):
        if not isinstance(token,str) or not 20<=len(token)<=200:
            raise AuthError('Sign in to continue')
        with connect(self.path) as db:
            row=db.execute('SELECT users.id,users.username,sessions.expires_at FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=?',(_digest(token),)).fetchone()
        if row is None or row['expires_at']<=self.clock():
            raise AuthError('Session expired or revoked. Sign in again.')
        return {'id':row['id'],'username':row['username']}

    def logout(self,token):
        if isinstance(token,str):
            with connect(self.path) as db:
                db.execute('DELETE FROM sessions WHERE token_hash=?',(_digest(token),))
        event('logout')

    def recover(self,username,recovery,new_password):
        username=_username(username)
        if not isinstance(recovery,str) or not 20<=len(recovery)<=200:
            raise AuthError('Recovery failed')
        encoded=password_hash(new_password)
        replacement=secrets.token_urlsafe(32)
        with connect(self.path) as db:
            row=db.execute('SELECT id,recovery_hash FROM users WHERE username=?',(username,)).fetchone()
            if row is None or not hmac.compare_digest(row['recovery_hash'],_digest(recovery)):
                raise AuthError('Recovery failed')
            db.execute('UPDATE users SET password_hash=?,recovery_hash=?,failures=0,locked_until=0 WHERE id=?',(encoded,_digest(replacement),row['id']))
            db.execute('DELETE FROM sessions WHERE user_id=?',(row['id'],))
        event('password_reset')
        return replacement
