import socket
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch, tmp_path):
    # Tests must never read the developer's real .env or inherit provider keys.
    from core import config
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / "absent.env")
    for name in (*config.SETTING_NAMES, *config.KEY_NAMES.values()):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def no_live_network(monkeypatch):
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def guarded(original):
        def connect(sock, address):
            # Windows asyncio creates a loopback socket pair for AppTest.
            if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
                return original(sock, address)
            raise AssertionError("External network forbidden in tests")
        return connect
    monkeypatch.setattr(socket.socket, "connect", guarded(original_connect))
    monkeypatch.setattr(socket.socket, "connect_ex", guarded(original_connect_ex))


@pytest.fixture
def notes():
    return (Path(__file__).parents[1] / "examples/study_notes.txt").read_text(encoding="utf-8")
