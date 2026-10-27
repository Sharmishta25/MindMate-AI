from mindmate.i18n import t
"""Functional authenticated-profile screens; legacy mode never reads user vaults."""
from datetime import datetime,timezone,date,time,timedelta
import calendar,json
import pandas as pd
import plotly.express as px
import streamlit as st
from zoneinfo import available_timezones
from mindmate.services.wellbeing import *
from mindmate.services.portability import export_json,export_csv,backup,restore_payload,preview_import,apply_import
from mindmate.services.scheduling import configure
from mindmate.ui.theme import navigate,chart_style


def open_record(record):
    kind=record['_kind']
    if kind=='mood': st.session_state['mood_select_pending']=record['id']; page='Mood tracker'
    elif kind=='journal': st.session_state['journal_select_pending']=record['id']; page='Journal'
    elif kind=='report': st.session_state['report_selected']=record['id']; page='Weekly reports'
    elif kind=='lifestyle': st.session_state['lifestyle_selected']=record['id']; page='Lifestyle'
    elif kind=='plan': st.session_state['plan_week']=date.fromisoformat(record['_date']); page='Weekly plan'
    else: page='Wellness activities'
    navigate(page)


def timeline_view(store,settings):
    st.header(t('Reflection timeline'))
    records=store.records(); today=datetime.now(timezone.utc).date()
    earliest=min((date.fromisoformat(r['_date']) for r in records if r['_kind'] not in {'preferences','schedule','notification'}),default=today)
    a,b=st.columns(2); start=a.date_input(t('Timeline from'),value=earliest); end=b.date_input(t('Timeline to'),value=today)
    kinds=st.multiselect(t('Event types'),['mood','journal','activity','lifestyle','report','plan'],default=['mood','journal','activity','lifestyle','report','plan'])
    query=st.text_input(t('Search your records'),max_chars=200)
    rows=timeline(store,start,end,kinds,query)
    mode=st.radio(t('View'),['Timeline','Calendar'],horizontal=True)
    if mode=='Calendar':
        selected=st.date_input(t('Month to display'),value=end)
        grid=[]
        for week in calendar.Calendar(firstweekday=0).monthdayscalendar(selected.year,selected.month):
            grid.append([f'{n} ({sum(r["_date"]==date(selected.year,selected.month,n).isoformat() for r in rows)})' if n else '' for n in week])
        st.dataframe(pd.DataFrame(grid,columns=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']),hide_index=True,width='stretch')
        st.caption(t('Cells show day (filtered event count). Zero means no matching record, not a mood score.'))
        rows=[r for r in rows if r['_date'].startswith(f'{selected.year:04d}-{selected.month:02d}')]
    if not rows: st.info(t('No records match these filters. Try another date, event type or search.')); return
    for record in rows:
        with st.expander(f"{record['_date']} | {record['_kind']} | #{record['id']}"):
            st.text(json.dumps({k:v for k,v in record.items() if not k.startswith('_')},ensure_ascii=False,indent=2))
            st.button(t('Open record'),key=f"timeline_open_{record['id']}",on_click=open_record,args=(record,))


def lifestyle_view(store,settings):
    st.header(t('Lifestyle'))
    st.caption(t('Optional self-reported observations. Missing values remain missing; associations do not establish causation or a health condition.'))
    choices={r['id']:r for r in store.records('lifestyle')}
    selected=st.selectbox(t('Lifestyle entry'),[None]+list(choices),key='lifestyle_selected',format_func=lambda x:'New entry' if x is None else choices[x]['_date'])
    row=choices.get(selected,{})
    with st.form(f'lifestyle_{selected}'):
        d=st.date_input(t('Lifestyle date (UTC)'),value=date.fromisoformat(row['_date']) if row else datetime.now(timezone.utc).date())
        values={}
        for field,maximum in FIELDS.items():
            old=row.get(field)
            values[field]=st.number_input(field.replace('_',' ').capitalize(),min_value=0.0,max_value=float(maximum),value=float(old) if old is not None else None)
        custom=st.text_area(t('Custom indicators JSON (optional, up to five named numeric values)'),value=json.dumps(row.get('custom',{}),ensure_ascii=False))
        save=st.form_submit_button(t('Save lifestyle entry'),type='primary')
    if save:
        from mindmate.ai.json_utils import loads
        values['custom']=loads(custom or '{}'); save_lifestyle(store,d.isoformat(),values,selected); st.success(t('Lifestyle entry saved.'))
    if selected is not None:
        confirm=st.checkbox(t('Confirm lifestyle deletion'))
        if st.button(t('Delete lifestyle entry'),disabled=not confirm): store.remove('lifestyle',selected); st.session_state.pop('lifestyle_selected',None); st.rerun()
    a,b=st.columns(2); start=a.date_input(t('Lifestyle trend from'),value=datetime.now(timezone.utc).date()-timedelta(days=30)); end=b.date_input(t('Lifestyle trend to'),value=datetime.now(timezone.utc).date())
    rows,associations=lifestyle_analysis(store,start,end)
    if not rows: st.info(t('No lifestyle observations in this range.')); return
    frame=pd.DataFrame(rows).sort_values('entry_date')
    field=st.selectbox(t('Lifestyle indicator'),list(FIELDS))
    st.plotly_chart(chart_style(px.line(frame,x='entry_date',y=field,markers=True,title=field.replace('_',' ').capitalize())),width='stretch')
    moods=store.list('mood_entries')
    if moods:
        moodframe=pd.DataFrame([r for r in moods if str(start)<=r['entry_date']<=str(end)])
        if not moodframe.empty: st.plotly_chart(chart_style(px.line(moodframe.sort_values('entry_date'),x='entry_date',y='mood_score',markers=True,title='Recorded mood (1-5)')),width='stretch')
    st.json(associations[field])


def plans_view(store,settings):
    st.header(t('Weekly wellbeing plan'))
    st.info(t('Optional general wellbeing, not treatment. Edit or skip anything that does not suit you.'))
    pref=preferences(store)
    with st.form('wellbeing_preferences'):
        goals=st.text_area(t('Personal goals (one per line, up to five)'),value='\n'.join(pref['goals']))
        activities=st.multiselect(t('Preferred plan activities'),list(ACTIVITY_GUIDANCE),default=pref['activities'])
        minutes=st.number_input(t('Available minutes per activity'),1,120,pref['minutes'])
        frequency=st.slider(t('Activities per week'),1,7,pref['frequency'])
        save=st.form_submit_button(t('Save plan preferences'))
    if save:
        preferences(store,[x.strip() for x in goals.splitlines() if x.strip()],activities,minutes,frequency,pref['language']); st.success(t('Plan preferences saved.'))
    anchor=st.date_input(t('Plan week'),value=datetime.now(timezone.utc).date(),key='plan_week')
    start,end=week_bounds(anchor); st.caption(f'Week: {start} to {end}')
    st.caption(t('Only goals, chosen activities, time/frequency and language may be sent to Anthropic; never journals. Without consent, generation uses local rules.'))
    consent=st.checkbox(t('For this request, I consent to sending plan preferences to Anthropic.'),key='plan_consent')
    existing=next((r for r in store.records('plan') if r['_date']==start),None)
    confirm=st.checkbox(t('Replace the existing weekly plan and its progress')) if existing else True
    if st.button(t('Generate weekly plan'),type='primary',disabled=not confirm):
        generate_plan(store,start,settings,consent)
        st.session_state['plan_consumed']=True; st.rerun()
    record=next((r for r in store.records('plan') if r['_date']==start),None)
    if not record: st.info(t('Save preferences, then generate this week.')); return
    st.caption(record['source']+' | '+record['reason']); progress=plan_progress(record)
    st.progress(progress['fraction'],text=f"{progress['completed']} / {progress['total']} completed; {progress['skipped']} skipped")
    for index,item in enumerate(record['items']):
        with st.expander(f"{item['date']} | {item['activity']} | {item['status']}"):
            st.write(ACTIVITY_GUIDANCE[item['activity']])
            with st.form(f'plan_item_{record["id"]}_{index}'):
                d=st.date_input(t('Activity date'),value=date.fromisoformat(item['date']))
                activity=st.selectbox(t('Activity'),list(ACTIVITY_GUIDANCE),index=list(ACTIVITY_GUIDANCE).index(item['activity']))
                duration=st.number_input(t('Minutes'),1,record['budget'],item['minutes'])
                status=st.selectbox(t('Status'),['planned','completed','skipped'],index=['planned','completed','skipped'].index(item['status']))
                edit=st.form_submit_button(t('Save activity changes'))
            if edit: update_plan_item(store,record['id'],index,activity,duration,status,d.isoformat()); st.rerun()
            if st.button(t('Regenerate this activity locally'),key=f'plan_regen_{index}'):
                update_plan_item(store,record['id'],index,activity,duration,'planned',regenerate=True); st.rerun()


def portability_view(store,settings):
    st.header(t('Data portability and recovery'))
    st.warning(t('JSON/CSV downloads are plaintext and may include sensitive content. Encrypted backups need the original key ring and matching account name. No executable file is imported; reminders/consent are not portable.'))
    st.download_button(t('Download owned JSON'),export_json(store),'mindmate-owned.json','application/json')
    st.download_button(t('Download owned CSV'),export_csv(store),'mindmate-owned.csv','text/csv')
    st.download_button(t('Download encrypted record backup'),backup(store),'mindmate-records.mmbackup','application/octet-stream')
    uploaded=st.file_uploader(t('Import JSON or encrypted backup'),type=['json','mmbackup'])
    if uploaded is None: st.info(t('Choose a file to validate and preview. No change occurs on upload.')); return
    raw=uploaded.getvalue()
    if uploaded.name.endswith('.mmbackup'): raw=restore_payload(store,raw)
    preview=preview_import(store,raw); st.json(preview)
    strategy=st.selectbox(t('Import strategy'),['merge','replace'])
    st.caption(t('Merge keeps existing conflicting daily/weekly records. Identical journal/activity payloads are deduplicated. Replace removes only your records, including reminder consent; account credentials remain. Export a backup before replacing. Reports are recomputed from imported/retained evidence.'))
    confirmation=st.text_input(t('Type IMPORT MY DATA or REPLACE MY DATA, matching the strategy'))
    if st.button(t('Apply previewed import')):
        count=apply_import(store,raw,strategy,confirmation,preview['fingerprint']); st.session_state.clear(); st.session_state['notice']=f'Imported {count} owned records. Sign in again; external copies remain.'; st.rerun()


def reminders_view(store,settings):
    st.header(t('Reminders and scheduled reports'))
    st.info(t('In-app notifications only. No email/SMS/browser push is sent. Jobs run only while the separate scheduler worker is running; this page does not start one.'))
    schedule=next(iter(store.records('schedule')),{'jobs':{}})
    kind=st.selectbox(t('Schedule type'),['reminder','report']); old=schedule['jobs'].get(kind,{})
    zones=sorted(available_timezones()); selected=old.get('timezone','Asia/Kolkata')
    with st.form('reminder_settings_'+kind):
        tz=st.selectbox(t('Timezone'),zones,index=zones.index(selected))
        clock=st.time_input(t('Preferred local time'),value=time(old.get('hour',9),old.get('minute',0)))
        weekday=st.selectbox(t('Report weekday (Monday=0)'),list(range(7)),index=old.get('weekday') or 0) if kind=='report' else None
        enabled=st.checkbox(t('Enable this schedule'),value=old.get('enabled',False))
        consent=st.checkbox(t('I consent to these persisted in-app notifications.'),value=old.get('consent',False))
        save=st.form_submit_button(t('Save notification preferences'))
    if save: configure(store,kind,tz,clock.hour,clock.minute,weekday,enabled,consent); st.success(t('Notification preferences saved. A worker is still required.'))
    st.code('.\\.venv\\Scripts\\python.exe -m scripts.scheduler --loop',language='powershell')
    st.caption(t('Missed jobs catch up only within 24 hours. DST gaps advance to the first valid minute; repeated times use the first occurrence. Weekly report periods remain UTC Monday-Sunday. Failed jobs retry up to three times with backoff; see scheduler deployment documentation.'))
    notices=store.records('notification')
    if not notices: st.info(t('No in-app notifications yet.'))
    for notice in notices:
        with st.container(border=True):
            st.write(notice['message']); st.caption(notice['_date']+' | '+('read' if notice['read'] else 'unread'))
            if st.button(t('Mark notification read'),key=f'notice_{notice["id"]}'):
                notice['read']=True; store.put('notification',notice['_date'],notice,notice['id']); st.rerun()


def render_expansion(store,settings,page):
    if not getattr(store,'secure',False):
        st.info(t('This feature requires authenticated encrypted-profile mode. Legacy local mode preserves the old tools only. Disable MINDMATE_LEGACY_LOCAL, configure the key ring and sign in.')); return
    if st.session_state.pop('plan_consumed',False): st.session_state['plan_consent']=False
    {'Timeline':timeline_view,'Lifestyle':lifestyle_view,'Weekly plan':plans_view,'Data portability':portability_view,'Reminders':reminders_view}[page](store,settings)
