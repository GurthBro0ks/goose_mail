import subprocess
import sys

import goose_mail


def test_version():
    assert goose_mail.__version__ == "0.1.0"


def test_import():
    assert hasattr(goose_mail, "__version__")


def test_main_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "goose_mail"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout
