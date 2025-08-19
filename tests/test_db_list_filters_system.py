from lampkitctl import db_introspect


def test_filters_system(monkeypatch):
    def fake_check_output(cmd, env=None, text=None, stderr=None):
        return "mysql\ninformation_schema\ncustom1\nperformance_schema\nsys\nmydb\n"

    monkeypatch.setattr(db_introspect.subprocess, "check_output", fake_check_output)
    dblist = db_introspect.list_databases()
    assert dblist == ["custom1", "mydb"]
