from lampkitctl import menu, apache_vhosts


def make_vhost(domain, docroot, ssl=False):
    return apache_vhosts.VHost(domain, docroot, f"/etc/apache2/sites-available/{domain}.conf", ssl)


def test_menu_site_picker_table_preview(monkeypatch, capsys):
    vhosts = [make_vhost("a.com", "/var/www/a"), make_vhost("b.net", "/var/www/b")]
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: vhosts)
    monkeypatch.setattr(menu, "inquirer", None)
    inputs = iter(["1"])
    monkeypatch.setattr(menu, "input", lambda _: next(inputs), raising=False)

    sel = menu._choose_site()
    out = capsys.readouterr().out

    domain_w = max(len("DOMAIN"), max(len(v.domain) for v in vhosts))
    path_w = max(len("PATH"), max(len(v.docroot) for v in vhosts))
    header = f"{'DOMAIN'.ljust(domain_w)} | {'PATH'.ljust(path_w)}"
    sep = f"{'-' * domain_w}-+-{'-' * path_w}"

    lines = out.splitlines()
    header_idx = lines.index(header)
    sep_idx = lines.index(sep)
    prompt_idx = lines.index("Select a site")
    assert header_idx < prompt_idx
    assert sep_idx < prompt_idx

    name1 = f"{vhosts[0].domain.ljust(domain_w)} | {vhosts[0].docroot}"
    name2 = f"{vhosts[1].domain.ljust(domain_w)} | {vhosts[1].docroot}"
    assert f"1) {name1}" in out
    assert f"2) {name2}" in out
    assert sel == vhosts[0]
