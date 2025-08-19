import os
from lampkitctl import apache_vhosts


def write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


def test_list_vhosts_deduplicates_and_detects_ssl(tmp_path):
    conf1 = tmp_path / "1-example.conf"
    write(
        conf1,
        """
<VirtualHost *:80>
ServerName example.com
DocumentRoot /var/www/example
</VirtualHost>
""",
    )
    conf_dup = tmp_path / "2-example-le-ssl.conf"
    write(
        conf_dup,
        """
<VirtualHost *:443>
ServerName example.com
DocumentRoot /var/www/example-ssl
RewriteEngine on
RewriteRule ^ https://example.com/ [R=301,L]
</VirtualHost>
""",
    )
    conf2 = tmp_path / "3-secure.conf"
    write(
        conf2,
        """
<VirtualHost *:80>
ServerName secure.com
DocumentRoot /var/www/secure
RewriteRule ^ https://secure.com/ [R=301,L]
</VirtualHost>
""",
    )
    vhosts = apache_vhosts.list_vhosts(str(tmp_path))
    vhosts.sort(key=lambda v: v.domain)
    assert len(vhosts) == 2
    assert vhosts[0].domain == "example.com"
    assert vhosts[0].docroot == "/var/www/example"
    assert vhosts[0].conf_path == str(conf1)
    assert vhosts[0].ssl is False
    assert vhosts[1].domain == "secure.com"
    assert vhosts[1].docroot == "/var/www/secure"
    assert vhosts[1].conf_path == str(conf2)
    assert vhosts[1].ssl is True
