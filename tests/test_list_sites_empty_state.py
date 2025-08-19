from lampkitctl import utils


def test_list_sites_empty_state(capsys):
    utils.render_sites_list([], color=False)
    out = capsys.readouterr().out
    assert out.strip() == "No sites found"
