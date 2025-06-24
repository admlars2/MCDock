# test_docker_service.py
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

# ---- project imports (edit as needed) -----------------------
from mcdock.services import docker_service  # module that defines DockerService
from mcdock.services.docker_service import DockerService
from mcdock.core.models import ConnectionType, EnvVar, PortBinding
from mcdock.core.config import settings
# -------------------------------------------------------------

# -------------------------------------------------------------------
# Helpers / fixtures
# -------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _isolate_fs(tmp_path, monkeypatch):
    """
    Every test gets its own temporary MC_ROOT.
    """
    monkeypatch.setattr(settings, "MC_ROOT", tmp_path)
    # let the class pick up the new path
    monkeypatch.setattr(DockerService, "root", Path(settings.MC_ROOT))


@pytest.fixture(autouse=True)
def _patch_template(monkeypatch):
    class DummyTemplate:
        def render(self, **kw):
            env_block = {
                "EULA": "TRUE" if kw["eula"] else "FALSE",
                "MEMORY": kw["memory"],
            }
            for ev in kw["env"]:
                k, v = (ev["key"], ev["value"]) if isinstance(ev, dict) else (ev.key, ev.value)
                env_block[k] = v

            def _port_str(p):
                if isinstance(p, dict):
                    host, cont, proto_raw = p["host_port"], p["container_port"], p["type"]
                else:
                    host, cont, proto_raw = p.host_port, p.container_port, p.type
                proto = proto_raw.value if hasattr(proto_raw, "value") else str(proto_raw)
                return f"{host}:{cont}/{proto.lower()}"

            service = {
                "image": kw["image"],
                "environment": env_block,
                "ports": [_port_str(p) for p in kw["ports"]],
            }
            return yaml.safe_dump({"version": "3", "services": {"mc-server": service}}, sort_keys=False)

    monkeypatch.setattr(docker_service, "COMPOSE_TEMPLATE", DummyTemplate())




def _fake_completed(stdout: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


# -------------------------------------------------------------------
# Unit-tests
# -------------------------------------------------------------------
def test_check_ports_rejects_duplicate_in_request():
    ports = [
        PortBinding(host_port=25565, container_port=25565, type=ConnectionType.TCP),
        PortBinding(host_port=25565, container_port=25566, type=ConnectionType.TCP),
    ]
    with pytest.raises(ValueError, match="Duplicate port"):
        DockerService._check_ports(ports)


def test_check_ports_rejects_collision_with_other_instance(tmp_path):
    # ---- create an existing instance with port 25565 ----------
    inst_dir = tmp_path / "world1"
    inst_dir.mkdir()
    compose = {
        "services": {
            "mc-server": {
                "image": "test",
                "ports": ["25565:25565/tcp"],
            }
        }
    }
    (inst_dir / "docker-compose.yml").write_text(
        yaml.safe_dump(compose, sort_keys=False)
    )

    # ---- new request tries to use the same host port ----------
    ports = [PortBinding(host_port=25565, container_port=25565, type=ConnectionType.TCP)]
    with pytest.raises(ValueError, match="already in use"):
        DockerService._check_ports(ports)


def test_create_instance_writes_compose(tmp_path):
    ports = [PortBinding(host_port=25570, container_port=25565, type=ConnectionType.TCP)]
    DockerService.create_instance(
        instance_name="alpha",
        image="itzg/minecraft-server:latest",
        eula=True,
        memory="4G",
        env=[EnvVar(key="DIFFICULTY", value="hard")],
        ports=ports,
    )
    compose_file = tmp_path / "alpha" / "docker-compose.yml"
    assert compose_file.exists()
    data = yaml.safe_load(compose_file.read_text())
    assert data["services"]["mc-server"]["ports"] == ["25570:25565/tcp"]


def test_get_status_running(monkeypatch):
    # fake subprocess so `stdout` looks like docker returned a container ID
    monkeypatch.setattr(
        docker_service,
        "subprocess",
        SimpleNamespace(
            run=lambda *a, **kw: _fake_completed(stdout="deadbeef\n"),
            CalledProcessError=subprocess.CalledProcessError,
        ),
    )

    # Create dummy instance dir so _get_instance_dir does not barf
    (Path(settings.MC_ROOT) / "alpha").mkdir()

    status = DockerService.get_status("alpha")
    assert status == "running"


def test_update_properties_overwrites_file(tmp_path):
    inst = tmp_path / "beta" / "data"
    inst.mkdir(parents=True)
    prop_path = inst / "server.properties"
    prop_path.write_text("foo=bar\n")

    DockerService.update_properties("beta", {"max-players": "20", "pvp": "true"})
    content = prop_path.read_text().splitlines()
    assert "max-players=20" in content and "pvp=true" in content and "foo=bar" not in content


def test_start_and_stop_call_docker(monkeypatch, tmp_path):
    """
    Ensure DockerService.start/stop invoke docker compose with the right cwd.
    """
    (tmp_path / "gamma").mkdir()

    calls = []

    def _fake_run(cmd, cwd=None, **kw):
        calls.append((cmd, cwd))
        return _fake_completed()

    mp = SimpleNamespace(run=_fake_run)
    monkeypatch.setattr(docker_service, "subprocess", mp)

    DockerService.start("gamma")
    DockerService.stop("gamma")

    assert calls[0][0][:3] == ["docker", "compose", "up"]
    assert calls[1][0][:3] == ["docker", "compose", "down"]
    assert all(call[1] == Path(settings.MC_ROOT) / "gamma" for call in calls)
