from lampkitctl import utils


def test_list_sites_table(capsys):
    sites = [
        ("test2.com", "/var/www/test2.com"),
        (
            "test3-supercalifragilistichespiralidoso.com",
            "/var/www/test3-supercalifragilistichespiralidoso.com",
        ),
    ]
    utils.render_sites_table(sites)
    out = capsys.readouterr().out
    lines = out.splitlines()

    domain_w = max(len("DOMAIN"), max(len(d) for d, _ in sites))
    path_w = max(len("PATH"), max(len(p) for _, p in sites))

    expected_header = f"{'DOMAIN'.ljust(domain_w)} | {'PATH'.ljust(path_w)}"
    expected_sep = f"{'-' * domain_w}-+-{'-' * path_w}"
    expected_rows = [f"{d.ljust(domain_w)} | {p}" for d, p in sites]

    assert lines[0] == ""
    assert lines[1] == expected_header
    assert lines[2] == expected_sep
    assert lines[3:-1] == expected_rows
    assert lines[-1] == ""
    assert "->" not in out
