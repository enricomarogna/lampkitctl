from lampkitctl import utils


def test_format_site_choices_all_entries_have_value():
    sites = [("a.com", "/var/www/a"), ("b.net", "/var/www/b")]
    choices = utils.format_site_choices(sites)
    assert all("name" in c and "value" in c for c in choices)
