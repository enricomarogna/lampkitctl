from lampkitctl import utils


def test_list_sites_framed_block(capsys):
    sites = [
        ("test2.com", "/var/www/test2.com"),
        (
            "test3-supercalifragilistichespiralidoso.com",
            "/var/www/test3-supercalifragilistichespiralidoso.com",
        ),
    ]
    utils.render_sites_list(sites, color=False)
    out = capsys.readouterr().out
    longest = max(len(f"{d}  ->  {r}") for d, r in sites)
    frame = "-" * longest
    lines = out.splitlines()
    # Expect leading and trailing blank lines
    assert lines[0] == ""
    assert lines[-1] == ""
    # Top and bottom frame once
    assert lines[1] == frame
    assert lines[-2] == frame
    # Ensure site lines appear once each
    expected_lines = [f"{d}  ->  {r}" for d, r in sites]
    assert lines[2:2+len(sites)] == expected_lines
