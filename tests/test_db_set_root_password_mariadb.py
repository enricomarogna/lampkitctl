from lampkitctl import db_ops


def test_mariadb_sql(monkeypatch):
    captured = {}

    def fake_run(cmd, dry_run=False, input_text=None, **kwargs):
        captured['sql'] = input_text

    monkeypatch.setattr(db_ops, 'run_command', fake_run)
    db_ops.set_root_password('mariadb', 'pw', dry_run=True)
    assert 'IDENTIFIED VIA mysql_native_password' in captured['sql']
    assert 'pw' in captured['sql']
