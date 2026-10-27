from mindmate.database import initialize_database,connect,SCHEMA


def test_v3_records_preserved_without_automatic_owner(tmp_path):
    path=tmp_path/'legacy.sqlite3'
    initialize_database(path)
    with connect(path) as db:
        for table in ['deliveries','vault_records','sessions','users']: db.execute('DROP TABLE '+table)
        db.execute('PRAGMA user_version=3')
    with connect(path) as db:
        db.execute("INSERT INTO journal_entries(entry_date,content) VALUES (?,?)",('2026-10-27','SYNTHETIC legacy reflection'))
    initialize_database(path)
    with connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==4
        assert db.execute('SELECT content FROM journal_entries').fetchone()[0]=='SYNTHETIC legacy reflection'
        assert db.execute('SELECT COUNT(*) FROM vault_records').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM users').fetchone()[0]==0
