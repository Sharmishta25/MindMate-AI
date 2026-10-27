"""Every data operation reauthorizes an opaque session; ciphertext is owner/ID-bound."""
from datetime import datetime,timezone
import json
import sqlite3
from mindmate.database import connect
from mindmate.security.auth import Accounts,AuthError
from mindmate.security.crypto import Cipher
from mindmate.services.core import DataError,integer,text,day,identifier,EMOTIONS
from mindmate.services.activities import ACTIVITIES

KINDS={'mood','journal','activity','report','lifestyle','plan','preferences','schedule','notification'}
TABLE_KIND={'mood_entries':'mood','journal_entries':'journal','wellness_activities':'activity'}


class Vault:
    secure=True
    def __init__(self,path,token,keys,ttl=1800):
        self.path,self.token=path,token
        self.accounts=Accounts(path,ttl)
        self.cipher=Cipher(keys)
        self.accounts.current(token)

    def owner(self): return self.accounts.current(self.token)['id']

    def _decode(self,row):
        value=self.cipher.decrypt(row['ciphertext'])
        expected=[row['user_id'],row['kind'],row['event_date'],row['id']]
        if not isinstance(value,dict) or value.get('binding')!=expected or not isinstance(value.get('data'),dict):
            raise DataError('Encrypted record context does not match; restore a verified backup')
        return dict(value['data'],id=row['id'],created_at=row['created_at'],updated_at=row['updated_at'])

    def records(self,kind=None):
        uid=self.owner()
        if kind is not None and kind not in KINDS: raise ValueError('Unknown record kind')
        with connect(self.path) as db:
            rows=db.execute('SELECT * FROM vault_records WHERE user_id=?'+(' AND kind=?' if kind else '')+' ORDER BY event_date DESC,id DESC',(uid,kind) if kind else (uid,)).fetchall()
        return [dict(self._decode(row),_kind=row['kind'],_date=row['event_date']) for row in rows]

    def get(self,kind,entry_id):
        uid=self.owner(); identifier(entry_id)
        if kind not in KINDS: raise ValueError('Unknown record kind')
        with connect(self.path) as db:
            row=db.execute('SELECT * FROM vault_records WHERE id=? AND user_id=? AND kind=?',(entry_id,uid,kind)).fetchone()
        if row is None: raise AuthError('Entry unavailable or not owned by this account')
        return self._decode(row)

    def put(self,kind,event_date,data,entry_id=None):
        uid=self.owner(); day(event_date)
        if kind not in KINDS or not isinstance(data,dict): raise ValueError('Invalid record')
        if entry_id is not None: self.get(kind,entry_id)
        cleaned={k:v for k,v in data.items() if k not in {'id','created_at','updated_at','_kind','_date','user_id'}}
        try:
            with connect(self.path) as db:
                db.execute('BEGIN IMMEDIATE')
                if entry_id is None:
                    entry_id=db.execute('INSERT INTO vault_records(user_id,kind,event_date,ciphertext) VALUES (?,?,?,?)',(uid,kind,event_date,'pending')).lastrowid
                payload=self.cipher.encrypt({'binding':[uid,kind,event_date,entry_id],'data':cleaned})
                cursor=db.execute('UPDATE vault_records SET event_date=?,ciphertext=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=? AND kind=?',(event_date,payload,entry_id,uid,kind))
                if cursor.rowcount!=1: raise AuthError('Entry unavailable')
            return entry_id
        except sqlite3.IntegrityError:
            raise DataError('A record already exists for that date. Edit the existing record.') from None
        except sqlite3.Error:
            raise DataError('Storage unavailable; the change was rolled back') from None

    def remove(self,kind,entry_id):
        uid=self.owner(); self.get(kind,entry_id)
        with connect(self.path) as db:
            db.execute('DELETE FROM vault_records WHERE id=? AND user_id=? AND kind=?',(entry_id,uid,kind))

    def list(self,table):
        if table not in TABLE_KIND: raise ValueError('Unknown record type')
        return self.records(TABLE_KIND[table])

    def delete(self,table,entry_id):
        if table not in TABLE_KIND: raise ValueError('Unknown record type')
        uid=self.owner(); self.get(TABLE_KIND[table],entry_id)
        with connect(self.path) as db:
            db.execute('BEGIN IMMEDIATE')
            if table=='mood_entries':
                for row in db.execute("SELECT * FROM vault_records WHERE user_id=? AND kind='journal'",(uid,)).fetchall():
                    record=self._decode(row)
                    if record.get('mood_entry_id')==entry_id:
                        record={k:v for k,v in record.items() if k not in {'id','created_at','updated_at'}}
                        record['mood_entry_id']=None
                        payload=self.cipher.encrypt({'binding':[uid,'journal',row['event_date'],row['id']],'data':record})
                        db.execute('UPDATE vault_records SET ciphertext=? WHERE id=? AND user_id=?',(payload,row['id'],uid))
            db.execute('DELETE FROM vault_records WHERE id=? AND user_id=? AND kind=?',(entry_id,uid,TABLE_KIND[table]))

    def save_mood(self,entry_date,score,stress,emotions,triggers='',reflection='',recorded_at=None,entry_id=None):
        day(entry_date); integer(score,1,5,'Mood'); integer(stress,0,10,'Stress')
        if not isinstance(emotions,(list,tuple)) or any(e not in EMOTIONS for e in emotions): raise ValueError('Choose supplied emotions')
        try:
            moment=datetime.fromisoformat(recorded_at) if recorded_at else datetime.now(timezone.utc)
            if moment.tzinfo is None: raise ValueError()
            moment=moment.astimezone(timezone.utc)
            if moment.date().isoformat()!=entry_date: raise ValueError()
        except (TypeError,ValueError,OverflowError): raise ValueError('Timestamp must match the selected UTC date') from None
        return self.put('mood',entry_date,{'entry_date':entry_date,'mood_score':score,'stress_level':stress,'emotion':json.dumps(list(dict.fromkeys(emotions))), 'triggers':text(triggers,'Triggers',500),'note':text(reflection,'Reflection',2000),'recorded_at':moment.isoformat()},entry_id)

    def save_journal(self,entry_date,title,content,mood_entry_id=None,entry_id=None):
        day(entry_date)
        if mood_entry_id is not None: self.get('mood',mood_entry_id)
        return self.put('journal',entry_date,{'entry_date':entry_date,'title':text(title,'Title',150),'content':text(content,'Journal',20000,True),'mood_entry_id':mood_entry_id},entry_id)

    def complete_activity(self,activity_date,activity_type,duration,helpfulness=None):
        day(activity_date)
        if not isinstance(activity_type,str) or activity_type not in ACTIVITIES: raise ValueError('Choose a supplied activity')
        integer(duration,1,180,'Duration')
        if helpfulness is not None: integer(helpfulness,1,5,'Helpfulness')
        return self.put('activity',activity_date,{'activity_date':activity_date,'activity_type':activity_type,'duration_minutes':duration,'completed':1,'helpfulness':helpfulness})

    def reset(self,confirmation):
        if confirmation!='DELETE ALL MY DATA': raise ValueError('Type DELETE ALL MY DATA exactly')
        uid=self.owner()
        with connect(self.path) as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM vault_records WHERE user_id=?',(uid,))
            db.execute('DELETE FROM deliveries WHERE user_id=?',(uid,))

    def rotate(self):
        uid=self.owner()
        with connect(self.path) as db:
            db.execute('BEGIN IMMEDIATE')
            for row in db.execute('SELECT * FROM vault_records WHERE user_id=?',(uid,)).fetchall():
                self._decode(row)
                db.execute('UPDATE vault_records SET ciphertext=? WHERE id=? AND user_id=?',(self.cipher.rotate(row['ciphertext']),row['id'],uid))


class UserReports:
    def __init__(self,store): self.store=store; self.path=store.path
    def generate(self,period_start,*,today=None):
        from datetime import date
        from mindmate.services.reports import week_bounds,QUESTIONS
        from mindmate.analytics.trends import analyze
        start,end=week_bounds(period_start)
        now=today or datetime.now(timezone.utc).date()
        if start!=str(period_start) or date.fromisoformat(start)>now: raise ValueError('Select a current/past Monday')
        evidence=analyze(self.store.list('mood_entries'),self.store.list('wellness_activities'),start,end,today=now)
        data={'version':1,'scheduling_available':True,'evidence':evidence,'questions':QUESTIONS,'next_steps':['Consider a small optional activity that suits you.']}
        existing=next((r for r in self.store.records('report') if r['_date']==start),None)
        return self.store.put('report',start,data,existing['id'] if existing else None)
    def list(self):
        return [{'id':r['id'],'period_start':r['evidence']['period_start'],'period_end':r['evidence']['period_end'],'created_at':r['created_at'],'updated_at':r['updated_at']} for r in self.store.records('report')]
    def get(self,entry_id): return self.store.get('report',entry_id)
    def delete(self,entry_id): self.store.remove('report',entry_id)
