from lampkitctl.db_introspect import parse_wp_config


WP_SAMPLE = """
<?php
define('DB_NAME', 'mydb');
define('DB_USER', 'myuser');
define('DB_HOST', 'localhost');
$table_prefix = 'wp_';
"""


def test_parse_wp_config(tmp_path):
    cfg_file = tmp_path / "wp-config.php"
    cfg_file.write_text(WP_SAMPLE)
    cfg = parse_wp_config(str(tmp_path))
    assert cfg is not None
    assert cfg.name == "mydb"
    assert cfg.user == "myuser"
    assert cfg.host == "localhost"
    assert cfg.table_prefix == "wp_"
