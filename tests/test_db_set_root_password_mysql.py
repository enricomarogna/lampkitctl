from lampkitctl import db_ops


def test_mysql_plugin_sql(monkeypatch):
    recorded = {}

    def fake_run(cmd, dry_run=False, input_text=None, **kwargs):
        recorded['cmd'] = cmd
        recorded['sql'] = input_text

    monkeypatch.setattr(db_ops, 'run_command', fake_run)
    db_ops.set_root_password('mysql', 'pw', 'caching_sha2_password', dry_run=True)
    assert 'mysql --protocol=socket -u root' in ' '.join(recorded['cmd'])
    assert 'caching_sha2_password' in recorded['sql']
    assert 'pw' in recorded['sql']
