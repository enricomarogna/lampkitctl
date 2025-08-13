import subprocess, sys

def test_module_help():
    proc = subprocess.run([sys.executable, "-m", "lampkitctl", "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Usage" in proc.stdout or "--help" in proc.stdout
