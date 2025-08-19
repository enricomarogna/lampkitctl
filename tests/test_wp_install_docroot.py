import lampkitctl.wp_ops as wp_ops


def test_install_wordpress_extracts_into_docroot(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, dry_run=False, **kwargs):
        calls.append(cmd)

    monkeypatch.setattr(wp_ops, "run_command", fake_run)
    wp_ops.install_wordpress(str(tmp_path), "db", "user", "pw", dry_run=True)

    wget_cmd, tar_cmd, rm_cmd, chown_cmd, find_dir_cmd, find_file_cmd = calls
    assert "--strip-components=1" in tar_cmd
    assert str(tmp_path) in tar_cmd
    assert rm_cmd[0] == "rm" and rm_cmd[1] == "-f" and rm_cmd[2].startswith("/tmp/wordpress-")
    assert chown_cmd[:3] == ["chown", "-R", "www-data:www-data"]
    assert find_dir_cmd[:3] == ["find", str(tmp_path), "-type"]
    assert find_file_cmd[:3] == ["find", str(tmp_path), "-type"]


def test_install_wordpress_skips_when_config_present(monkeypatch, tmp_path):
    (tmp_path / "wp-config.php").write_text("")
    calls = []
    warns = []

    def fake_run(cmd, dry_run=False, **kwargs):
        calls.append(cmd)

    monkeypatch.setattr(wp_ops, "run_command", fake_run)
    monkeypatch.setattr(wp_ops, "echo_warn", lambda msg: warns.append(msg))
    wp_ops.install_wordpress(str(tmp_path), "db", "user", "pw", dry_run=True)

    # Only permission commands should run
    assert all(cmd[0] != "wget" for cmd in calls)
    assert warns and "WordPress appears to be installed" in warns[0]
    assert len(calls) == 3  # chown + two find commands
