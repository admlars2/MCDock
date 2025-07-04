# MCDock Backend

This is the backend service for **MCDock**, a Minecraft server management platform. It provides a REST API and WebSocket endpoints for managing Minecraft server instances, backups, schedules, and authentication.

## Features

- Manage multiple Minecraft server instances via Docker
- Start, stop, and configure servers
- Schedule automatic tasks (backups, restarts, etc.)
- Backup and restore server data
- User authentication and rate limiting
- Real-time updates via WebSockets
- Robust logging and error handling

## Tech Stack

- **Python 3.11+**
- **FastAPI** (REST API)
- **APScheduler** (scheduling)
- **Docker SDK for Python**
- **SQLAlchemy** (job store)
- **SlowAPI** (rate limiting)
- **Starlette** (WebSockets)
- **pytest** (testing)

## Project Structure

```
backend/
├── src/
│   └── mcdock/
│       ├── core/           # Core configs, logging, models
│       ├── routers/        # API route modules
│       ├── services/       # Business logic (Docker, scheduler, etc.)
│       └── main.py         # App entrypoint
├── tests/                  # Unit and integration tests
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11 or newer
- Docker (for managing Minecraft servers)
- (Optional) [Poetry](https://python-poetry.org/) or `pip` for dependency management

### Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/MCDock.git
   cd MCDock/backend
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` and adjust as needed.
   - At minimum, set `MC_ROOT` to the directory where Minecraft instances and logs will be stored.

4. **Run the backend server:**
   ```sh
   uvicorn src.mcdock.main:app --reload
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000).

### Running Tests

```sh
pytest
```

## Configuration

Configuration is managed via environment variables (see `.env.example`). Key settings include:

- `MC_ROOT`: Root directory for Minecraft data and logs
- `DATABASE_URL`: (Optional) URL for APScheduler's job store
- `SECRET_KEY`: For authentication tokens

## API Overview

- **Instances:** `/instances` — Manage Minecraft server instances
- **Backups:** `/backups` — List, trigger, restore, and delete backups
- **Schedules:** `/schedules` — Manage scheduled tasks
- **Auth:** `/auth` — User authentication endpoints

See the [OpenAPI docs](http://localhost:8000/docs) when running the server for full API details.

## Logging

Logs are stored in `mcdock-logs/mcdock.log` under your `MC_ROOT` directory, with rotation and console output enabled.

## Contributing

1. Fork the repo and create your branch.
2. Make your changes and add tests.
3. Run `pytest` to ensure all tests pass.
4. Submit a pull request.

## License

MIT License

---

**MCDock** © 2025