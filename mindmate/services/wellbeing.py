"""User-owned lifestyle, timeline and editable weekly plans. No medical inference."""
from datetime import date,timedelta
import json,math
import numpy as np
from mindmate.services.core import day,text,integer
from mindmate.services.reports import week_bounds
from mindmate.safety.support import support_route
from mindmate.ai.provider import AnthropicProvider,ProviderError

ACTIVITY_GUIDANCE={
 'writing':'Optionally write about one moment from your day.',
 'grounding':'Notice a few sights and sounds, if comfortable.',
 'movement':'Choose gentle movement comfortable for you; stop if uncomfortable.',
 'relaxation':'Take a quiet pause in a comfortable place.',
 'connection':'If wanted, reach out to a trusted person for ordinary conversation.',
}
FIELDS={'sleep_hours':24,'exercise_minutes':1440,'screen_hours':24,'social_minutes':1440}


def save_lifestyle(store,entry_date,values,entry_id=None):
    day(entry_date)
    if not isinstance(values,dict) or set(values)-set(FIELDS)-{'custom'}: raise ValueError('Unknown lifestyle fields')
    cleaned={}
    for field,maximum in FIELDS.items():
        value=values.get(field)
        if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=maximum):
            raise ValueError(f'{field} must be blank or between 0 and {maximum}')
        cleaned[field]=value
    custom=values.get('custom',{})
    if not isinstance(custom,dict) or len(custom)>5: raise ValueError('At most five custom indicators')
    for label,value in custom.items():
        text(label,'Indicator name',40,True)
        if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1000000: raise ValueError('Invalid custom indicator')
    cleaned['custom']=custom
    return store.put('lifestyle',entry_date,dict(cleaned,entry_date=entry_date),entry_id)


def lifestyle_analysis(store,start,end):
    day(str(start)); day(str(end))
    if str(start)>str(end): raise ValueError('Start date must precede end date')
    rows=[r for r in store.records('lifestyle') if str(start)<=r['_date']<=str(end)]
    moods={r['entry_date']:r['mood_score'] for r in store.list('mood_entries')}
    associations={}
    for field in FIELDS:
        pairs=[(r[field],moods[r['_date']]) for r in rows if r.get(field) is not None and r['_date'] in moods]
        enough=len(pairs)>=7 and len({p[0] for p in pairs})>1 and len({p[1] for p in pairs})>1
        associations[field]={'paired_days':len(pairs),'correlation':float(np.corrcoef(np.array(pairs).T)[0,1]) if enough else None,
                             'note':'Same-day Pearson association, not causation or clinical evidence.' if enough else 'Withheld: need seven paired days and variation in both values.'}
    return rows,associations


def timeline(store,start,end,kinds=None,query=''):
    day(str(start)); day(str(end)); text(query,'Search',200)
    allowed={'mood','journal','activity','report','lifestyle','plan'}
    kinds=set(kinds) if kinds is not None else allowed
    if not kinds<=allowed or str(start)>str(end): raise ValueError('Invalid timeline filter')
    return sorted([r for r in store.records() if r['_kind'] in kinds and str(start)<=r['_date']<=str(end) and query.casefold() in json.dumps(r,ensure_ascii=False).casefold()],key=lambda r:(r['_date'],r['created_at'],r['id']),reverse=True)


def preferences(store,goals=None,activities=None,minutes=10,frequency=3,language='en'):
    current=next(iter(store.records('preferences')),None)
    if goals is None: return current or {'goals':[],'activities':['writing','grounding'],'minutes':10,'frequency':3,'language':'en'}
    if not isinstance(goals,list) or len(goals)>5: raise ValueError('At most five goals')
    goals=[text(g,'Goal',200,True) for g in goals]
    if not isinstance(activities,list) or not activities or any(a not in ACTIVITY_GUIDANCE for a in activities): raise ValueError('Choose allowed activities')
    integer(minutes,1,120,'Minutes'); integer(frequency,1,7,'Frequency')
    if language not in {'en','hi','mr'}: raise ValueError('Unsupported language')
    data={'goals':goals,'activities':list(dict.fromkeys(activities)),'minutes':minutes,'frequency':frequency,'language':language}
    store.put('preferences','1970-01-01',data,current['id'] if current else None)
    return data


def generate_plan(store,anchor,settings,consent=False,provider=None):
    if type(consent) is not bool: raise ValueError('Consent must be explicit')
    start,end=week_bounds(anchor); pref=preferences(store)
    if support_route(*pref['goals']).show_support: raise ValueError('Routine plan generation paused: open Get support for guidance')
    choices=[pref['activities'][i%len(pref['activities'])] for i in range(pref['frequency'])]
    source='Rule-based fallback (not an LLM)'; reason='consent_not_given'
    if consent and settings.llm_ready:
        from mindmate.ai.plan_prompts import SYSTEM,SCHEMA
        try:
            result=(provider or AnthropicProvider(settings))._request(SYSTEM,json.dumps(pref,ensure_ascii=False),SCHEMA)
            if set(result)!={'activities'} or not isinstance(result['activities'],list) or len(result['activities'])!=pref['frequency'] or any(x not in pref['activities'] for x in result['activities']): raise ValueError()
            choices=result['activities']; source='LLM-selected activities; dates/durations validated locally'; reason='validated'
        except (ProviderError,ValueError,TypeError,KeyError): reason='unavailable_or_invalid'
    elif consent: reason='missing_configuration'
    items=[]
    for i,activity in enumerate(choices):
        offset=round(i*6/(len(choices)-1)) if len(choices)>1 else 0
        items.append({'date':(date.fromisoformat(start)+timedelta(days=offset)).isoformat(),'activity':activity,'minutes':min(10,pref['minutes']),'status':'planned'})
    existing=next((r for r in store.records('plan') if r['_date']==start),None)
    return store.put('plan',start,{'week_start':start,'week_end':end,'items':items,'budget':pref['minutes'],'source':source,'reason':reason},existing['id'] if existing else None)


def update_plan_item(store,plan_id,index,activity,minutes,status,entry_date=None,regenerate=False):
    record=store.get('plan',plan_id)
    integer(index,0,len(record['items'])-1,'Item index'); integer(minutes,1,record['budget'],'Minutes')
    if activity not in ACTIVITY_GUIDANCE or status not in {'planned','completed','skipped'}: raise ValueError('Invalid activity/status')
    entry_date=entry_date or record['items'][index]['date']; day(entry_date)
    if not record['week_start']<=entry_date<=record['week_end']: raise ValueError('Date must remain in this week')
    if regenerate:
        allowed=preferences(store)['activities']; old=record['items'][index]['activity']
        activity=allowed[(allowed.index(old)+1)%len(allowed)] if old in allowed else allowed[0]
        status='planned'
    record['items'][index]={'date':entry_date,'activity':activity,'minutes':minutes,'status':status}
    store.put('plan',record['week_start'],record,plan_id)
    return plan_progress(record)


def plan_progress(record):
    total=len(record['items']); complete=sum(x['status']=='completed' for x in record['items'])
    return {'total':total,'completed':complete,'skipped':sum(x['status']=='skipped' for x in record['items']),'fraction':complete/total if total else 0}
