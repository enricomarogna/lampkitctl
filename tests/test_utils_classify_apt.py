import subprocess

from lampkitctl import utils


def test_classify_package_not_found():
    err = subprocess.CalledProcessError(
        100,
        ["apt-get", "install"],
        output="Unable to locate package lampkit",
        stderr="",
    )
    msg = utils.classify_apt_error(err)
    assert "package not found" in msg.lower()


def test_classify_lock_issue():
    err = subprocess.CalledProcessError(
        1,
        ["apt-get", "install"],
        output="Could not get lock /var/lib/dpkg/lock",
        stderr="",
    )
    msg = utils.classify_apt_error(err)
    assert "locked" in msg.lower()


def test_classify_network_issue():
    err = subprocess.CalledProcessError(
        1,
        ["apt-get", "update"],
        output="Temporary failure resolving 'archive.ubuntu.com'",
        stderr="",
    )
    msg = utils.classify_apt_error(err)
    assert "network" in msg.lower()


def test_classify_permission_denied():
    err = subprocess.CalledProcessError(
        100,
        ["apt-get", "install"],
        output="Permission denied",
        stderr="Permission denied",
    )
    msg = utils.classify_apt_error(err)
    assert "permissions" in msg.lower()


def test_classify_fallback_snippet():
    err = subprocess.CalledProcessError(
        1,
        ["apt-get", "install"],
        output="Some other error",
        stderr="line1\nline2",
    )
    msg = utils.classify_apt_error(err)
    assert "line2" in msg
