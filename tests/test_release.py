"""Historical integrity must survive Git checkout on Windows and Linux."""
import hashlib
import json
from pathlib import Path

import pytest

from tools.check_release import matches_historical_hash


@pytest.mark.parametrize("recorded_crlf", [False, True])
@pytest.mark.parametrize("checkout_crlf", [False, True])
def test_checkout_line_endings(recorded_crlf, checkout_crlf):
    content = b'{"score": 6}\nsecond line\n'
    recorded = content.replace(b"\n", b"\r\n") if recorded_crlf else content
    checkout = content.replace(b"\n", b"\r\n") if checkout_crlf else content
    expected = hashlib.sha256(recorded).hexdigest()
    assert matches_historical_hash(checkout, expected)
    assert not matches_historical_hash(checkout.replace(b"6", b"7"), expected)
    assert not matches_historical_hash(checkout + b" ", expected)
    assert not matches_historical_hash(b"\xef\xbb\xbf" + checkout, expected)


def test_all_historical_artifacts_in_both_checkout_styles():
    root = Path(__file__).parents[1]
    manifest = json.loads((root / "docs/historical/sha256.json").read_text())
    for name, expected in manifest.items():
        lf = (root / name).read_bytes().replace(b"\r\n", b"\n")
        assert matches_historical_hash(lf, expected), name
        assert matches_historical_hash(lf.replace(b"\n", b"\r\n"), expected), name
