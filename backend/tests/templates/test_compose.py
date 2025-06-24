import pytest
from jinja2 import Template
from textwrap import dedent

from mcdock.templates.compose import COMPOSE_TEMPLATE  # adjust the import path accordingly
from mcdock.core.models import EnvVar, ConnectionType, PortBinding


def test_compose_template_render():
    context = {
        "image": "itzg/minecraft-server:latest",
        "name": "test-server",
        "eula": True,
        "memory": "6G",
        "env": [
            EnvVar(key="TYPE", value="FABRIC"),
            EnvVar(key="VERSION", value="1.21.6"),
            EnvVar(key="PACKWIZ_URL", value="https://raw.githubusercontent.com/admlars2/proximity-optimized-vanilla/main/pack.toml"),
            EnvVar(key="MODRINTH_DOWNLOAD_DEPENDENCIES", value="required"),
            EnvVar(key="DIFFICULTY", value="hard"),
            EnvVar(key="SEED", value="awesomeseed"),
            EnvVar(key="ENABLE_WHITELIST", value="TRUE"),
            EnvVar(key="WHITELIST", value="Username"),
            EnvVar(key="SPAWN_PROTECTION", value="0"),
            EnvVar(key="SIMULATION_DISTANCE", value="6"),
            EnvVar(key="VIEW_DISTANCE", value="10") 
        ],
        "ports": [
            PortBinding(host_port=25565, container_port=25565, type=ConnectionType.TCP),
            PortBinding(host_port=25575, container_port=25575, type=ConnectionType.TCP),
            PortBinding(host_port=24454, container_port=24454, type=ConnectionType.UDP)
        ]
    }

    rendered = COMPOSE_TEMPLATE.render(**context)

    print(rendered)

    expected = dedent("""\
services:
  mc-server:
    image: itzg/minecraft-server:latest
    container_name: test-server
    restart: unless-stopped
    environment:
      EULA: "TRUE"
      MEMORY: "6G"
      TYPE: "FABRIC"
      VERSION: "1.21.6"
      PACKWIZ_URL: "https://raw.githubusercontent.com/admlars2/proximity-optimized-vanilla/main/pack.toml"
      MODRINTH_DOWNLOAD_DEPENDENCIES: "required"
      DIFFICULTY: "hard"
      SEED: "awesomeseed"
      ENABLE_WHITELIST: "TRUE"
      WHITELIST: "Username"
      SPAWN_PROTECTION: "0"
      SIMULATION_DISTANCE: "6"
      VIEW_DISTANCE: "10"
    ports:
      - "25565:25565/tcp"
      - "25575:25575/tcp"
      - "24454:24454/udp"
    volumes:
      - ./data:/data
    """)

    assert rendered.strip() == expected.strip()
