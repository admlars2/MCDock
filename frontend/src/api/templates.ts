import type { InstanceCompose } from "./types"

export const STARTER_COMPOSE: InstanceCompose = {
    name: "mc-server",
    image: "itzg/minecraft-server:latest",
    eula: false,
    memory: "6G",
    env: [
        {
            key: "TYPE",
            value: "fabric"
        },
        {
            key: "VERSION",
            value: "1.21.6"
        },
        {
            key: "PACKWIZ_URL",
            value: "https://raw.githubusercontent.com/admlars2/proximity-optimized-vanilla/main/pack.toml"
        },
        {
            key: "MODRINTH_DOWNLOAD_DEPENDENCIES",
            value: "required"
        },
        {
            key: "LEVEL",
            value: "world"
        },
        {
            key: "DIFFICULTY",
            value: "HARD"
        },
        {
            key: "SEED",
            value: "custom-seed"
        },
        {
            key: "ENABLE_WHITELIST",
            value: "TRUE"
        },
        {
            key: "WHITELIST",
            value: "YourUsername"
        },
        {
            key: "SPAWN_PROTECTION",
            value: "0"
        },
        {
            key: "SIMULATION_DISTANCE",
            value: "6"
        },
        {
            key: "VIEW_DISTANCE",
            value: "10"
        }
    ],
    ports: [
        {
            host_port: 25565,
            container_port: 25565,
            type: "tcp"
        },
        {
            host_port: 25575,
            container_port: 25575,
            type: "tcp"
        },
        {
            host_port: 24454,
            container_port: 24454,
            type: "udp"
        }
    ]
}