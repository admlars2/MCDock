# tests/test_instances_router.py
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── module under test ─────────────────────────────────────────────────────────
from mcdock.routers import instances as mod      # file that defines the router
from mcdock.routers.instances import router
# ──────────────────────────────────────────────────────────────────────────────


# ╭────────────────────────── helper fixtures & stubs ─────────────────────────╮
@pytest.fixture
def client(monkeypatch):
    """
    Build a minimal FastAPI app with the router, patching:
      • auth dependency  (require_token → no-op)
      • COMPOSE_TEMPLATE (simple string)
      • DockerService / RconService methods (spies / stubs)
    """
    app = FastAPI()
    app.include_router(router)

    # bypass auth
    app.dependency_overrides[mod.require_token] = lambda: None

    # dummy compose template
    monkeypatch.setattr(mod, "COMPOSE_TEMPLATE", "version: '3'\nservices: {}\n")

    # ---------------- DockerService stubs -----------------
    calls = SimpleNamespace()
    monkeypatch.setattr(mod.DockerService, "create_instance", lambda **kw: calls.__setattr__("create", kw))
    monkeypatch.setattr(mod.DockerService, "update_compose", lambda *a, **kw: calls.__setattr__("update_compose", (a, kw)))
    monkeypatch.setattr(mod.DockerService, "get_compose", lambda name: f"# compose for {name}\n")
    monkeypatch.setattr(mod.DockerService, "get_instance_dir", lambda name: Path(f"/instances/{name}"))
    monkeypatch.setattr(mod.DockerService, "get_instance_dirs", lambda: [Path("/instances/one"), Path("/instances/two")])
    monkeypatch.setattr(mod.DockerService, "get_status", lambda name: "running" if name == "one" else "stopped")
    monkeypatch.setattr(mod.DockerService, "start", lambda name: calls.__setattr__("start", name))
    monkeypatch.setattr(mod.DockerService, "stop", lambda name: calls.__setattr__("stop", name))
    monkeypatch.setattr(mod.DockerService, "restart", lambda name: calls.__setattr__("restart", name))
    monkeypatch.setattr(mod.DockerService, "delete", lambda name: calls.__setattr__("delete", name))
    monkeypatch.setattr(mod.DockerService, "get_properties", lambda name: {"difficulty": "hard"})
    monkeypatch.setattr(mod.DockerService, "update_properties", lambda name, props: calls.__setattr__("update_props", props))

    # ---------------- RconService stub --------------------
    monkeypatch.setattr(mod.RconService, "execute", lambda instance_name, command: f"executed {command}")

    with TestClient(app) as c:
        c._calls = calls        # expose spy storage
        yield c
# ╰──────────────────────────────────────────────────────────────────────────────╯


# ────────────────────────────────── tests ──────────────────────────────────────
def test_template_endpoint(client):
    r = client.get("/instances/template")
    assert r.status_code == 200
    assert r.text.startswith("version: '3'")


def test_create_instance_success(client):
    payload = {
        "name": "alpha",
        "image": "itzg/mc",
        "eula": True,
        "memory": "4G",
        "env": [{"key": "DIFFICULTY", "value": "hard"}],
        "ports": [{"host_port": 25570, "container_port": 25565, "type": "tcp"}],
    }
    r = client.post("/instances/create", json=payload)
    assert r.status_code == 201
    assert client._calls.create["instance_name"] == "alpha"


def test_create_instance_error_from_service(monkeypatch, client):
    def _raise(**_):
        raise ValueError("boom")
    monkeypatch.setattr(mod.DockerService, "create_instance", _raise)
    r = client.post("/instances/create", json={
        "name": "beta", "image": "x", "eula": True, "memory": "1G", "env": [], "ports": []
    })
    assert r.status_code == 500


def test_get_and_update_compose(client):
    r = client.get("/instances/alpha/compose")
    assert r.status_code == 200
    assert "# compose for alpha" in r.text

    r2 = client.put("/instances/alpha/compose", json={"eula": True, "memory": "4G", "env": [], "ports": []})
    assert r2.status_code == 200
    assert client._calls.update_compose[0][0] == "alpha"


def test_properties_get_and_put(client):
    r = client.get("/instances/alpha/properties")
    assert r.status_code == 200
    assert r.json() == {"difficulty": "hard"}

    r2 = client.put("/instances/alpha/properties", json={"max-players": "10"})
    assert r2.status_code == 200
    assert client._calls.update_props == {"max-players": "10"}


def test_list_instances(client):
    r = client.get("/instances/")
    assert r.status_code == 200
    names = {i["name"] for i in r.json()}
    assert names == {"one", "two"}


@pytest.mark.parametrize("action", ["start", "stop", "restart"])
def test_lifecycle_actions(client, action):
    r = client.post(f"/instances/alpha/{action}")
    assert r.status_code == 200
    assert getattr(client._calls, action) == "alpha"


def test_delete_instance(client):
    r = client.delete("/instances/alpha")
    assert r.status_code == 204
    assert client._calls.delete == "alpha"


def test_rcon_command_endpoint(client):
    r = client.post("/instances/alpha/cmd", json={"command": "say hello"})
    assert r.status_code == 200
    assert r.json()["message"] == "executed say hello"
