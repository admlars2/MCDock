# tests/test_rcon_service.py
from types import SimpleNamespace

import pytest

# ── project imports (adjust the package name if needed) ─────────────────────────
from mcdock.services import rcon_service          # module that defines everything
from mcdock.services.rcon_service import (
    _read_rcon_from_props,
    RconService,
)
from mcdock.core.config import settings
# ────────────────────────────────────────────────────────────────────────────────


# ╭─────────────────────────────  HELPER STUBS  ───────────────────────────────╮
class DummyClient:
    """
    Lightweight stand-in for mcipc.rcon.je.Client that records how it is used.
    """

    def __init__(self, host: str, *, port: int, timeout: int):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.login_pwd = None
        self.cmds_run = []

    # Context-manager protocol
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False  # propagate exceptions if any

    # API expected by RconService
    def login(self, password):
        self.login_pwd = password

    def run(self, cmd: str) -> str:
        self.cmds_run.append(cmd)
        return f"OK: {cmd}"
# ╰──────────────────────────────────────────────────────────────────────────────╯


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch):
    """
    Provide predictable defaults and patch RconService.host / settings in isolation.
    """
    monkeypatch.setattr(settings, "RCON_PORT", 25575)
    monkeypatch.setattr(settings, "RCON_PASSWORD", "default_pwd")
    monkeypatch.setattr(settings, "RCON_HOST", "localhost")

    # RconService.host is assigned at class definition time → patch explicitly
    monkeypatch.setattr(RconService, "host", "localhost")


@pytest.fixture(autouse=True)
def _patch_client(monkeypatch):
    """
    Replace the real RCON Client with DummyClient and yield the instance created.
    """
    created = {}

    def _factory(*args, **kwargs):
        client = DummyClient(*args, **kwargs)
        created["client"] = client
        return client

    monkeypatch.setattr(rcon_service, "Client", _factory)
    yield created   # tests can inspect created["client"]


# ───────────────────────────────  UNIT TESTS  ──────────────────────────────────
def test_read_props_custom_values(monkeypatch):
    """
    Properties contain valid rcon.password and rcon.port ⇒ they are returned.
    """
    props = {"rcon.password": "  secret ", "rcon.port": " 25580 "}
    monkeypatch.setattr(
        rcon_service.DockerService,
        "get_properties",
        lambda inst: props,
    )

    pwd, port = _read_rcon_from_props("alpha")
    assert pwd == "secret" and port == 25580


def test_read_props_defaults_on_missing(monkeypatch):
    """
    Missing keys ⇒ fall back to settings defaults.
    """
    monkeypatch.setattr(
        rcon_service.DockerService, "get_properties", lambda inst: {}
    )

    pwd, port = _read_rcon_from_props("beta")
    assert pwd == "default_pwd" and port == 25575


def test_read_props_malformed_port(monkeypatch):
    """
    Non-numeric rcon.port ⇒ fall back to default port.
    """
    monkeypatch.setattr(
        rcon_service.DockerService,
        "get_properties",
        lambda inst: {"rcon.password": "x", "rcon.port": "not_a_number"},
    )
    _, port = _read_rcon_from_props("gamma")
    assert port == 25575


def test_execute_sends_command(monkeypatch, _patch_client):
    """
    RconService.execute should:
      1. read props for pwd/port
      2. instantiate Client with host/port
      3. login with correct password
      4. run the command and return its output
    """
    monkeypatch.setattr(
        rcon_service.DockerService,
        "get_properties",
        lambda inst: {"rcon.password": "mypwd", "rcon.port": "25590"},
    )

    result = RconService.execute("world1", "save-all")
    client = _patch_client["client"]

    assert client.host == "localhost"
    assert client.port == 25590
    assert client.login_pwd == "mypwd"
    assert client.cmds_run == ["save-all"]
    assert result == "OK: save-all"
