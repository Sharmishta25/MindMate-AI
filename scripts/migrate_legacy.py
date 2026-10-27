"""Operator-only copy of explicitly assigned legacy data; never deletes source rows."""
import argparse,getpass,json
from mindmate.config import load_settings
from mindmate.database import initialize_database,connect
from mindmate.security.auth import Accounts
from mindmate.services.vault import Vault
from mindmate.services.portability import DICTIONARY,preview_import,apply_import


def copy_legacy(store,confirmation):
    if confirmation!='ASSIGN ALL LEGACY DATA TO THIS ACCOUNT':
        raise ValueError('Explicit ownership assignment required')
    records=[]
    with connect(store.path) as db:
        for table,kind,field in [('mood_entries','mood','entry_date'),('journal_entries','journal','entry_date'),('wellness_activities','activity','activity_date')]:
            for row in db.execute('SELECT * FROM '+table).fetchall():
                data=dict(row); sid=data.pop('id')
                data.pop('created_at',None); data.pop('updated_at',None)
                records.append({'kind':kind,'date':data[field],'source_id':sid,'data':data})
    raw=json.dumps({'version':1,'dictionary':DICTIONARY,'records':records}).encode('utf-8')
    preview=preview_import(store,raw)
    return apply_import(store,raw,'merge','IMPORT MY DATA',preview['fingerprint'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username',required=True)
    args=parser.parse_args(); settings=load_settings(); initialize_database(settings.database_path)
    auth=Accounts(settings.database_path)
    token=auth.login(args.username,getpass.getpass('Account password: '))
    try:
        store=Vault(settings.database_path,token,settings.encryption_keys)
        phrase=input('Type ASSIGN ALL LEGACY DATA TO THIS ACCOUNT only if all legacy records belong to this account: ')
        print('Copied owned records:',copy_legacy(store,phrase))
        print('Legacy source remains plaintext. Historical reports were not copied; regenerate from evidence.')
    finally: auth.logout(token)

if __name__=='__main__': main()
