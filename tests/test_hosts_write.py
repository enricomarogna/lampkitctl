from lampkitctl import system_ops


def test_hosts_append_and_remove(tmp_path):
    hosts = tmp_path / "hosts"
    hosts.write_text("127.0.0.1 localhost\n", encoding="utf-8")
    mode = hosts.stat().st_mode

    system_ops.add_host_entry("example.com", hosts_file=str(hosts))
    assert "example.com" in hosts.read_text(encoding="utf-8")
    assert hosts.stat().st_mode == mode

    system_ops.remove_host_entry("example.com", hosts_file=str(hosts))
    assert "example.com" not in hosts.read_text(encoding="utf-8")
    assert hosts.stat().st_mode == mode
