"""Persisted in-app jobs. An explicitly running worker is required; no external delivery."""
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
import secrets
from mindmate.database import connect
from mindmate.security.auth import _digest,Accounts
from mindmate.services.vault import Vault,UserReports
from mindmate.services.core import integer
from mindmate.services.reports import week_bounds


def configure(store,kind,tz,hour,minute,weekday,enabled,consent):
    if kind not in {'reminder','report'} or type(enabled) is not bool or type(consent) is not bool: raise ValueError('Invalid schedule choices')
    try: ZoneInfo(tz)
    except (ZoneInfoNotFoundError,TypeError,ValueError): raise ValueError('Select a valid IANA timezone') from None
    integer(hour,0,23,'Hour'); integer(minute,0,59,'Minute')
    if kind=='report': integer(weekday,0,6,'Weekday')
    if enabled and not consent: raise ValueError('Explicit notification consent is required')
    old=next(iter(store.records('schedule')),None); data={'jobs':dict(old.get('jobs',{})) if old else {}}
    data['jobs'][kind]={'enabled':enabled,'consent':consent,'timezone':tz,'hour':hour,'minute':minute,'weekday':weekday if kind=='report' else None}
    return store.put('schedule','1970-01-01',data,old['id'] if old else None)


def due_time(job,now):
    zone=ZoneInfo(job['timezone']); local=now.astimezone(zone)
    selected=local.date()
    if job.get('weekday') is not None: selected-=timedelta(days=(selected.weekday()-job['weekday'])%7)
    naive=datetime.combine(selected,datetime.min.time()).replace(hour=job['hour'],minute=job['minute'])
    def resolve(value):
        # Ambiguous local times use first occurrence (fold=0). Nonexistent times
        # advance to the first real minute, with a bounded two-hour gap policy.
        for offset in range(121):
            candidate=(value+timedelta(minutes=offset)).replace(tzinfo=zone,fold=0)
            utc=candidate.astimezone(timezone.utc)
            if utc.astimezone(zone).replace(tzinfo=None)==candidate.replace(tzinfo=None): return utc
        raise ValueError('Timezone gap exceeds supported policy')
    due=resolve(naive)
    if due>now: due=resolve(naive-timedelta(days=7 if job.get('weekday') is not None else 1))
    return due if timedelta(0)<=now-due<=timedelta(hours=24) else None


def run_once(path,keys,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('Worker time must be timezone-aware')
    delivered=0
    with connect(path) as db:
        owners=[r[0] for r in db.execute("SELECT DISTINCT user_id FROM vault_records WHERE kind='schedule'")]
    for uid in owners:
        token=secrets.token_urlsafe(32)
        with connect(path) as db:
            db.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES (?,?,?)',(_digest(token),uid,datetime.now(timezone.utc).timestamp()+300))
        try:
            store=Vault(path,token,keys)
            schedule=next(iter(store.records('schedule')),{'jobs':{}})
            for kind,job in schedule['jobs'].items():
                if not job['enabled'] or not job['consent']: continue
                due=due_time(job,now)
                if due is None: continue
                period=week_bounds(now.date()-timedelta(days=7))[0]
                occurrence=kind+':'+(period if kind=='report' else due.astimezone(ZoneInfo(job['timezone'])).date().isoformat())
                with connect(path) as db:
                    db.execute('BEGIN IMMEDIATE')
                    old=db.execute('SELECT * FROM deliveries WHERE user_id=? AND occurrence=?',(uid,occurrence)).fetchone()
                    if old and (old['status']=='done' or old['attempts']>=3 or now.timestamp()-old['updated_at']<(300 if old['status']=='pending' else 60*old['attempts'])): continue
                    attempts=old['attempts']+1 if old else 1
                    db.execute("INSERT INTO deliveries(user_id,occurrence,status,attempts,updated_at) VALUES (?,?,'pending',?,?) ON CONFLICT(user_id,occurrence) DO UPDATE SET status='pending',attempts=excluded.attempts,updated_at=excluded.updated_at",(uid,occurrence,attempts,now.timestamp()))
                try:
                    # Consent is read again after claiming, so revocation is not cached.
                    current=next(iter(store.records('schedule')),{'jobs':{}})['jobs'].get(kind,{})
                    if not current.get('enabled') or not current.get('consent'):
                        status='cancelled'
                    else:
                        if kind=='report': UserReports(store).generate(period,today=now.date())
                        existing=next((r for r in store.records('notification') if r.get('occurrence')==occurrence),None)
                        if existing is None:
                            store.put('notification',now.date().isoformat(),{'occurrence':occurrence,'message':'Your weekly report is available.' if kind=='report' else 'An optional moment to check in, when it suits you.','read':False})
                        delivered+=1; status='done'
                except Exception:
                    # No exception payload is logged; next poll retries under the lease/backoff.
                    status='failed'
                with connect(path) as db:
                    db.execute('UPDATE deliveries SET status=?,updated_at=? WHERE user_id=? AND occurrence=?',(status,now.timestamp(),uid,occurrence))
        finally:
            Accounts(path).logout(token)
    return delivered
