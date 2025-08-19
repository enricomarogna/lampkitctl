from lampkitctl import auth_cache


def test_auth_cache_roundtrip():
    auth_cache.clear()
    assert auth_cache.get_db_root_password() is None
    assert auth_cache.get_sudo_password() is None
    auth_cache.set_db_root_password("db")
    auth_cache.set_sudo_password("su")
    assert auth_cache.get_db_root_password() == "db"
    assert auth_cache.get_sudo_password() == "su"
    auth_cache.clear()
    assert auth_cache.get_db_root_password() is None
    assert auth_cache.get_sudo_password() is None
