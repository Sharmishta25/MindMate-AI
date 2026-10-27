from datetime import datetime,timezone
from cryptography.fernet import Fernet
import pytest
from mindmate.database import initialize_database
from mindmate.security.auth import Accounts
from mindmate.services.vault import Vault
from mindmate.services.scheduling import *


def test_timezone_dst_and_missed_window():
    job={'timezone':'America/New_York','hour':2,'minute':30,'weekday':None}
    due=due_time(job,datetime(2026,3,8,8,tzinfo=timezone.utc))
    assert due.hour==7 and due.minute==0
    job.update(hour=1,minute=30)
    due=due_time(job,datetime(2026,11,1,7,tzinfo=timezone.utc))
    assert due.hour==5
    job.update(weekday=0)
    assert due_time(job,datetime(2026,11,5,7,tzinfo=timezone.utc)) is None


def test_worker_consent_restart_and_duplicates(tmp_path):
    path=tmp_path/'scheduler.sqlite3'; initialize_database(path); auth=Accounts(path); auth.register('synthetic','synthetic password 123')
    key=Fernet.generate_key().decode(); store=Vault(path,auth.login('synthetic','synthetic password 123'),key)
    with pytest.raises(ValueError): configure(store,'reminder','Asia/Kolkata',9,0,None,True,False)
    configure(store,'reminder','Asia/Kolkata',9,0,None,True,True)
    now=datetime(2026,10,27,5,tzinfo=timezone.utc)
    assert run_once(path,key,now)==1 and run_once(path,key,now)==0
    assert len(store.records('notification'))==1
    configure(store,'reminder','Asia/Kolkata',9,0,None,False,False)
    assert run_once(path,key,datetime(2026,10,28,5,tzinfo=timezone.utc))==0
