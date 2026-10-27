"""Versioned owner-only portability; untrusted JSON is data, never executable."""
from datetime import datetime,timezone
import csv,hashlib,io,json,math
from mindmate.ai.json_utils import loads
from mindmate.database import connect
from mindmate.security.auth import AuthError
from mindmate.services.core import day,text,integer,EMOTIONS
from mindmate.services.wellbeing import FIELDS,ACTIVITY_GUIDANCE
from mindmate.analytics.trends import analyze
from mindmate.services.reports import week_bounds,QUESTIONS

PORTABLE={'mood','journal','activity','lifestyle','plan','preferences','report'}
UNIQUE={'mood','lifestyle','plan','preferences','report'}
DICTIONARY={'version':'Portable schema version, integer 1','records':'Owned records only; no users/passwords/sessions/consent schedules', 'kind':'mood/journal/activity/lifestyle/plan/preferences/report','date':'ISO UTC record day or Monday for weekly records','data':'Original user data; imported report statistics are recomputed, never trusted','source_id':'Export-local reference used only to remap journal links; never a destination owner ID'}


def export_json(store):
    records=[]
    for r in store.records():
        if r['_kind'] in PORTABLE:
            data={k:v for k,v in r.items() if k not in {'id','created_at','updated_at','_kind','_date','_import_key'}}
            records.append({'kind':r['_kind'],'date':r['_date'],'source_id':r['id'],'data':data})
    return json.dumps({'version':1,'dictionary':DICTIONARY,'records':records},ensure_ascii=False,allow_nan=False).encode('utf-8')


def export_csv(store):
    output=io.StringIO(); writer=csv.writer(output); writer.writerow(['kind','date','record_json'])
    for r in loads(export_json(store))['records']:
        # Prefix spreadsheet formula starters; JSON cell is quoted by CSV and begins '{'.
        writer.writerow([r['kind'],r['date'],json.dumps(r['data'],ensure_ascii=False)])
    return output.getvalue().encode('utf-8-sig')


def _number(value,minimum,maximum):
    return type(value) in (int,float) and math.isfinite(value) and minimum<=value<=maximum


def validate_record(record):
    if not isinstance(record,dict) or set(record)!={'kind','date','source_id','data'}: raise ValueError('Invalid record fields')
    kind,d,data=record['kind'],record['date'],record['data']
    if kind not in PORTABLE or not isinstance(data,dict) or 'user_id' in data: raise ValueError('Invalid kind or owner field')
    day(d); integer(record['source_id'],1,2**63-1,'Source ID')
    if len(json.dumps(data,ensure_ascii=False))>80000: raise ValueError('Imported record too large')
    if kind=='mood':
        integer(data.get('mood_score'),1,5,'Mood')
        if data.get('stress_level') is not None: integer(data['stress_level'],0,10,'Stress')
        emotions=loads(data.get('emotion','[]'))
        if not isinstance(emotions,list) or any(e not in EMOTIONS for e in emotions): raise ValueError('Invalid emotions')
        text(data.get('note',''),'Reflection',2000); text(data.get('triggers',''),'Triggers',500)
        moment=datetime.fromisoformat(data['recorded_at'])
        if moment.tzinfo is None or moment.astimezone(timezone.utc).date().isoformat()!=d: raise ValueError('Invalid UTC timestamp')
        if data.get('entry_date')!=d: raise ValueError('Date mismatch')
    elif kind=='journal':
        text(data.get('content'),'Journal',20000,True); text(data.get('title',''),'Title',150)
        if data.get('entry_date')!=d: raise ValueError('Date mismatch')
        if data.get('mood_entry_id') is not None: integer(data['mood_entry_id'],1,2**63-1,'Linked check-in')
    elif kind=='activity':
        from mindmate.services.activities import ACTIVITIES
        if data.get('activity_type') not in ACTIVITIES or data.get('completed')!=1: raise ValueError('Invalid activity')
        integer(data.get('duration_minutes'),1,180,'Duration')
        if data.get('helpfulness') is not None: integer(data['helpfulness'],1,5,'Helpfulness')
        if data.get('activity_date')!=d: raise ValueError('Date mismatch')
    elif kind=='lifestyle':
        for field,maxvalue in FIELDS.items():
            if data.get(field) is not None and not _number(data[field],0,maxvalue): raise ValueError('Invalid lifestyle value')
        custom=data.get('custom',{})
        if not isinstance(custom,dict) or len(custom)>5: raise ValueError('Invalid indicators')
        for name,value in custom.items():
            text(name,'Indicator',40,True)
            if not _number(value,-1000000,1000000): raise ValueError('Invalid indicator value')
        if data.get('entry_date')!=d: raise ValueError('Date mismatch')
    elif kind=='preferences':
        if d!='1970-01-01' or data.get('language') not in {'en','hi','mr'}: raise ValueError('Invalid preference')
        integer(data.get('minutes'),1,120,'Minutes'); integer(data.get('frequency'),1,7,'Frequency')
        if not isinstance(data.get('goals'),list) or len(data['goals'])>5: raise ValueError('Invalid goals')
        for goal in data['goals']: text(goal,'Goal',200,True)
        if not data.get('activities') or any(a not in ACTIVITY_GUIDANCE for a in data['activities']): raise ValueError('Invalid activity preference')
    elif kind=='plan':
        start,end=week_bounds(d)
        if d!=start or data.get('week_start')!=start or data.get('week_end')!=end: raise ValueError('Invalid week')
        integer(data.get('budget'),1,120,'Budget')
        if not isinstance(data.get('items'),list) or not 1<=len(data['items'])<=7: raise ValueError('Invalid plan items')
        for item in data['items']:
            day(item['date'])
            if not start<=item['date']<=end or item.get('activity') not in ACTIVITY_GUIDANCE or item.get('status') not in {'planned','completed','skipped'}: raise ValueError('Invalid plan item')
            integer(item.get('minutes'),1,data['budget'],'Minutes')
    elif kind=='report':
        if week_bounds(d)[0]!=d: raise ValueError('Reports must start Monday')
    return record


def validate_bundle(raw):
    if not isinstance(raw,bytes) or len(raw)>10485760: raise ValueError('Import limit is 10 MiB')
    try:
        bundle=loads(raw)
        if not isinstance(bundle,dict) or set(bundle)!={'version','dictionary','records'} or type(bundle['version']) is not int or bundle['version']!=1: raise ValueError()
        if not isinstance(bundle['dictionary'],dict) or not isinstance(bundle['records'],list) or len(bundle['records'])>1000: raise ValueError()
        seen=set()
        for record in bundle['records']:
            validate_record(record)
            key=(record['kind'],record['source_id'])
            if key in seen: raise ValueError()
            seen.add(key)
        return bundle
    except (ValueError,TypeError,KeyError,UnicodeError,RecursionError,OverflowError):
        raise ValueError('Invalid portable file: check version, field types, dates and record limits') from None


def _fingerprint(kind,d,data):
    copy={k:v for k,v in data.items() if k not in {'id','created_at','updated_at','_kind','_date','_import_key','mood_entry_id'}}
    return hashlib.sha256(json.dumps([kind,d,copy],sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def preview_import(store,raw):
    bundle=validate_bundle(raw); existing=store.records(); conflicts=0
    for r in bundle['records']:
        if any(x['_kind']==r['kind'] and (x['_date']==r['date'] if r['kind'] in UNIQUE else _fingerprint(x['_kind'],x['_date'],x)==_fingerprint(r['kind'],r['date'],r['data'])) for x in existing): conflicts+=1
    return {'records':len(bundle['records']),'conflicts':conflicts,'fingerprint':hashlib.sha256(raw).hexdigest(),'strategy':'Merge keeps existing conflicts. Replace deletes only the authenticated account records; reminders/consent are revoked.'}


def apply_import(store,raw,strategy,confirmation,preview_hash):
    bundle=validate_bundle(raw)
    if strategy not in {'merge','replace'} or confirmation!=('IMPORT MY DATA' if strategy=='merge' else 'REPLACE MY DATA'): raise ValueError('Explicit import confirmation required')
    if preview_hash!=hashlib.sha256(raw).hexdigest(): raise ValueError('File changed; preview again')
    uid=store.owner(); count=0; mapping={}
    with connect(store.path) as db:
        db.execute('BEGIN IMMEDIATE')
        if strategy=='replace':
            db.execute('DELETE FROM vault_records WHERE user_id=?',(uid,)); db.execute('DELETE FROM deliveries WHERE user_id=?',(uid,))
        existing=[dict(store._decode(r),_kind=r['kind'],_date=r['event_date']) for r in db.execute('SELECT * FROM vault_records WHERE user_id=?',(uid,)).fetchall()]
        incoming=sorted(bundle['records'],key=lambda r:{'mood':0,'journal':2,'report':3}.get(r['kind'],1))
        for record in incoming:
            kind,d,data=record['kind'],record['date'],dict(record['data'])
            conflict=next((x for x in existing if x['_kind']==kind and (x['_date']==d if kind in UNIQUE else _fingerprint(kind,d,data)==_fingerprint(kind,d,x))),None)
            if conflict:
                mapping[(kind,record['source_id'])]=conflict['id']; continue
            if kind=='plan':
                data['source']='Imported plan (not AI verified)'; data['reason']='validated portable file'
            if kind=='journal':
                data['mood_entry_id']=mapping.get(('mood',data.get('mood_entry_id')))
            if kind=='report':
                start,end=week_bounds(d)
                moods=[x for x in existing if x['_kind']=='mood']; activities=[x for x in existing if x['_kind']=='activity']
                data={'version':1,'scheduling_available':True,'evidence':analyze(moods,activities,start,end),'questions':QUESTIONS,'next_steps':['Consider a small optional reflection.']}
            rid=db.execute('INSERT INTO vault_records(user_id,kind,event_date,ciphertext) VALUES (?,?,?,?)',(uid,kind,d,'pending')).lastrowid
            ciphertext=store.cipher.encrypt({'binding':[uid,kind,d,rid],'data':data})
            db.execute('UPDATE vault_records SET ciphertext=? WHERE id=? AND user_id=?',(ciphertext,rid,uid))
            mapping[(kind,record['source_id'])]=rid
            existing.append(dict(data,id=rid,_kind=kind,_date=d)); count+=1
    return count


def backup(store):
    return store.cipher.encrypt({'format':'mindmate-backup-v1','owner':store.accounts.current(store.token)['username'],'bundle':loads(export_json(store))},limit=10485760).encode('ascii')


def restore_payload(store,encrypted):
    if not isinstance(encrypted,bytes) or len(encrypted)>14000000: raise ValueError('Backup too large')
    try:
        data=store.cipher.decrypt(encrypted.decode('ascii'))
    except (UnicodeError,TypeError): raise ValueError('Invalid encrypted backup encoding') from None
    if not isinstance(data,dict) or 'bundle' not in data: raise ValueError('Invalid encrypted backup envelope')
    if data.get('format')!='mindmate-backup-v1' or data.get('owner')!=store.accounts.current(store.token)['username']: raise AuthError('Backup belongs to a different account or format')
    raw=json.dumps(data['bundle'],ensure_ascii=False).encode('utf-8'); validate_bundle(raw); return raw
