import pytest
from src.common.validators import require_keys, RealDataGuard

def test_fail_fast(monkeypatch):
    monkeypatch.setenv("REQUIRE_REAL_DATA","true")
    with pytest.raises(RealDataGuard):
        require_keys(["MISSING_KEY"])
