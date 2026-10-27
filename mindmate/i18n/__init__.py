"""Code-owned UI resources; missing translations explicitly fall back to English."""
from functools import lru_cache
from pathlib import Path
import json
import streamlit as st

LANGUAGES={'en':'English','hi':'हिन्दी','mr':'मराठी'}

@lru_cache(maxsize=3)
def resource(language):
    code=language if language in LANGUAGES else 'en'
    return json.loads((Path(__file__).parent/(code+'.json')).read_text(encoding='utf-8'))


def t(key,language=None):
    code=language or st.session_state.get('ui_language','en')
    return resource(code).get(key,resource('en').get(key,key))


def language_picker(settings):
    from mindmate.ui.accounts import user_store
    from mindmate.services.wellbeing import preferences
    token=st.session_state.get('auth_token')
    if token and not settings.legacy_local:
        store=user_store(settings); uid=store.owner()
        if st.session_state.get('language_owner')!=uid:
            st.session_state['ui_language']=preferences(store)['language']; st.session_state['language_owner']=uid
    selected=st.sidebar.selectbox('Language',list(LANGUAGES),format_func=lambda code:LANGUAGES[code],key='ui_language')
    if token and not settings.legacy_local:
        store=user_store(settings); pref=preferences(store)
        if selected!=pref['language']: preferences(store,pref['goals'],pref['activities'],pref['minutes'],pref['frequency'],selected)
    if selected!='en':
        st.sidebar.caption('Hindi/Marathi navigation and core labels are available. Some explanatory/safety copy remains canonical English. Translations have not received independent fluent/clinical review.')
