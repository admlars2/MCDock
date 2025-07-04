from enum import Enum

from pydantic import BaseModel, Field, field_validator

# ------------------------------------------------------------------
# COMPLETE list of environment variables recognised by itzg/minecraft-server
# Source: project docs (docker-minecraft-server.readthedocs.io) :contentReference[oaicite:0]{index=0}
# ------------------------------------------------------------------
ALLOWED: set[str] = {
    # ——— General JVM / container options ———
    "UID", "GID", "TZ",
    "MEMORY", "INIT_MEMORY", "MAX_MEMORY",
    "ENABLE_ROLLING_LOGS",
    "ENABLE_JMX", "JMX_HOST",
    "USE_AIKAR_FLAGS", "USE_MEOWICE_FLAGS", "USE_MEOWICE_GRAALVM_FLAGS",
    "JVM_OPTS", "JVM_XX_OPTS", "JVM_DD_OPTS",
    "EXTRA_ARGS", "LOG_TIMESTAMP",

    # ——— Core server options ———
    "TYPE", "EULA", "VERSION", "MOTD", "DIFFICULTY",
    "ICON", "OVERRIDE_ICON",
    "MAX_PLAYERS", "MAX_WORLD_SIZE",
    "ALLOW_NETHER", "ANNOUNCE_PLAYER_ACHIEVEMENTS",
    "ENABLE_COMMAND_BLOCK", "FORCE_GAMEMODE", "GENERATE_STRUCTURES",
    "HARDCORE", "SNOOPER_ENABLED",
    "MAX_BUILD_HEIGHT",
    "SPAWN_ANIMALS", "SPAWN_MONSTERS", "SPAWN_NPCS",
    "SPAWN_PROTECTION",
    "VIEW_DISTANCE", "SIMULATION_DISTANCE",
    "SEED", "MODE", "PVP",
    "LEVEL_TYPE", "GENERATOR_SETTINGS", "LEVEL",
    "ONLINE_MODE", "ALLOW_FLIGHT",
    "SERVER_NAME", "SERVER_PORT",
    "PLAYER_IDLE_TIMEOUT",
    "ENABLE_STATUS", "SYNC_CHUNK_WRITES",
    "ENTITY_BROADCAST_RANGE_PERCENTAGE", "FUNCTION_PERMISSION_LEVEL",
    "NETWORK_COMPRESSION_THRESHOLD", "OP_PERMISSION_LEVEL",
    "PREVENT_PROXY_CONNECTIONS", "USE_NATIVE_TRANSPORT",
    "EXEC_DIRECTLY", "STOP_SERVER_ANNOUNCE_DELAY",
    "PROXY", "CONSOLE", "GUI",
    "STOP_DURATION", "SETUP_ONLY",
    "USE_FLARE_FLAGS", "USE_SIMD_FLAGS",

    # ——— Resource-pack handling ———
    "RESOURCE_PACK", "RESOURCE_PACK_SHA1", "RESOURCE_PACK_ENFORCE",

    # ——— Whitelist management ———
    "ENABLE_WHITELIST", "WHITELIST", "WHITELIST_FILE", "OVERRIDE_WHITELIST",

    # ——— RCON ———
    "ENABLE_RCON", "RCON_PASSWORD", "RCON_PORT",
    "BROADCAST_RCON_TO_OPS",
    "RCON_CMDS_STARTUP", "RCON_CMDS_ON_CONNECT",
    "RCON_CMDS_FIRST_CONNECT", "RCON_CMDS_ON_DISCONNECT",
    "RCON_CMDS_LAST_DISCONNECT",

    # ——— Auto-Pause ———
    "ENABLE_AUTOPAUSE",
    "AUTOPAUSE_TIMEOUT_EST", "AUTOPAUSE_TIMEOUT_INIT",
    "AUTOPAUSE_TIMEOUT_KN", "AUTOPAUSE_PERIOD",
    "AUTOPAUSE_KNOCK_INTERFACE", "DEBUG_AUTOPAUSE",

    # ——— Auto-Stop ———
    "ENABLE_AUTOSTOP",
    "AUTOSTOP_TIMEOUT_EST", "AUTOSTOP_TIMEOUT_INIT",
    "AUTOSTOP_PERIOD", "DEBUG_AUTOSTOP",

    # ——— CurseForge / Modrinth / Packwiz ———
    "CF_API_KEY", "CF_API_KEY_FILE",
    "CF_PAGE_URL", "CF_SLUG", "CF_FILE_ID",
    "CF_FILENAME_MATCHER", "CF_EXCLUDE_INCLUDE_FILE",
    "CF_EXCLUDE_MODS", "CF_FORCE_INCLUDE_MODS",
    "CF_FORCE_SYNCHRONIZE", "CF_SET_LEVEL_FROM",
    "CF_PARALLEL_DOWNLOADS", "CF_OVERRIDES_SKIP_EXISTING",
    "PACKWIZ_URL", "MODRINTH_DOWNLOAD_DEPENDENCIES",
}

class ConnectionType(str, Enum):
    TCP = "tcp"
    UDP = "udp"

class InstanceStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class EnvVar(BaseModel):
    key:  str = Field(pattern=r"^[A-Z0-9_]+$")
    value: str

    @field_validator("key")
    @classmethod
    def check_allowed(cls, v: str) -> str:
        if v not in ALLOWED:
            raise ValueError(f"{v} is not an allowed env var")
        return v

class PortBinding(BaseModel):
    host_port: int = Field(ge=1024, le=65535)
    container_port: int = Field(ge=1024, le=65535)
    type: ConnectionType = ConnectionType.TCP