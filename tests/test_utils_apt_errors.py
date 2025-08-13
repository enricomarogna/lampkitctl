import subprocess

from lampkitctl import utils


def test_classify_permission_denied():
    err = subprocess.CalledProcessError(
        100,
        ["apt-get", "install"],
        output="Permission denied",
        stderr="Permission denied",
    )
    msg = utils.classify_apt_error(err)
    assert "APT failed" in msg


def test_classify_lock_issue():
    err = subprocess.CalledProcessError(
        1,
        ["apt-get", "install"],
        output="Could not get lock",
        stderr="",
    )
    msg = utils.classify_apt_error(err)
    assert "lock" in msg.lower()
