import goose_mail


def test_version():
    assert goose_mail.__version__ == "0.1.0"


def test_import():
    assert hasattr(goose_mail, "__version__")
