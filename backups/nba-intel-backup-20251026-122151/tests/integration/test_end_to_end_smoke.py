import pathlib
def test_artifacts_dir():
    assert pathlib.Path("artifacts").exists()
