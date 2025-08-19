from lampkitctl import utils


def test_list_sites_empty_state(capsys):
    utils.render_sites_list([])
    out = capsys.readouterr().out
    assert "No sites found" in out


def test_list_sites_framed_output(capsys):
    utils.render_sites_list([("test2.com", "/var/www/test2.com")])
    out = capsys.readouterr().out
    assert out.count(utils.FRAME) == 2
    assert "test2.com  ->  /var/www/test2.com" in out
