from lampkitctl import utils


def test_list_sites_empty_state(capsys):
    utils.render_sites_table([])
    out = capsys.readouterr().out
    assert out.strip() == "No sites found"
