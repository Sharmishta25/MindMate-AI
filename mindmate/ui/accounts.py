from mindmate.i18n import t
"""Account gate. Tokens stay in server session memory, not URLs or browser storage."""
import streamlit as st
from mindmate.security.auth import Accounts,AuthError
from mindmate.services.core import DataError
from mindmate.security.crypto import Cipher


def account_gate(settings):
    if settings.legacy_local:
        st.warning(t('LEGACY LOCAL MODE: no account isolation/encryption for legacy records. Never expose this compatibility mode publicly.'))
        return True
    try: Cipher(settings.encryption_keys)
    except DataError:
        st.header(t('Encrypted profile setup required'))
        st.write(t('Set MINDMATE_ENCRYPTION_KEYS in the server environment to a securely backed-up Fernet key. Do not paste keys into journals, URLs or logs. Lost keys cannot be recovered from account passwords.'))
        st.code('$env:MINDMATE_ENCRYPTION_KEYS = & .\\.venv\\Scripts\\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"',language='powershell')
        st.caption(t('This command captures a new key into the current shell environment without printing it. Securely back it up outside this project before storing data; reuse it after restarting. Do not generate a replacement key for existing encrypted records.'))
        return False
    accounts=Accounts(settings.database_path)
    token=st.session_state.get('auth_token')
    if token:
        try:
            user=accounts.current(token)
            st.sidebar.caption('Signed in as '+user['username'])
            if st.sidebar.button(t('Log out'),key='account_logout'):
                accounts.logout(token); st.session_state.clear(); st.rerun()
            return True
        except AuthError:
            st.session_state.clear()
            st.warning(t('Session expired or revoked. Sign in again.'))
    st.title(t('Your private reflection space'))
    st.info(t('General wellbeing, not diagnosis or treatment. Profiles require sign-in. New record payloads are encrypted; this is not full-database encryption or public-hosting certification.'))
    mode=st.radio(t('Account action'),['Sign in','Register','Recover account'],key='account_mode',horizontal=True,format_func=t)
    with st.form('account_form'):
        username=st.text_input(t('Username'),max_chars=40,key='account_username')
        password=st.text_input('Password' if mode!='Recover account' else 'New password',type='password',max_chars=256,key='account_password')
        recovery=st.text_input(t('One-use recovery code'),type='password',key='account_recovery') if mode=='Recover account' else ''
        submitted=st.form_submit_button(mode,type='primary')
    if submitted:
        try:
            if mode=='Register':
                _,code=accounts.register(username,password)
                st.success(t('Account created. Save the recovery code securely now, then sign in. It is displayed only for this response.'))
                st.code(code,language=None)
            elif mode=='Recover account':
                code=accounts.recover(username,recovery,password)
                st.success(t('Password changed; all prior sessions revoked. Save this replacement recovery code, then sign in.'))
                st.code(code,language=None)
            else:
                st.session_state['auth_token']=accounts.login(username,password)
                # Remove password field values before the next UI render.
                st.session_state['account_clear']=True
                st.rerun()
        except (ValueError,DataError) as error: st.error(str(error))
    return False


def user_store(settings):
    if settings.legacy_local:
        from mindmate.services.core import Store
        return Store(settings.database_path)
    from mindmate.services.vault import Vault
    return Vault(settings.database_path,st.session_state.get('auth_token'),settings.encryption_keys)
