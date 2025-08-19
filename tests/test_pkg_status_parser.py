import subprocess

from lampkitctl.packages import detect_pkg_status


def test_pkg_status_parser(monkeypatch):
    outputs = {
        "apache2": "Installed: (none)\nCandidate: 2\n",
        "php": "Installed: 1\nCandidate: 1\n",
        "libapache2-mod-php": "Installed: 1\nCandidate: 2\n",
    }

    def fake_check_output(cmd, text=True, stderr=None):
        return outputs[cmd[-1]]

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    status = detect_pkg_status(["apache2", "php", "libapache2-mod-php"])
    assert status.missing == ["apache2"]
    assert status.upgradable == ["libapache2-mod-php"]
    assert status.uptodate == ["php"]
