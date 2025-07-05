# MCDock

_MCDock_ is a modern control-panel for running **Minecraft servers inside Docker containers**.  
It ships with a FastAPI backend, a React + TypeScript web UI, scheduler, WebSocket console, and an opinionated workflow for backups and updates.

---

## 🚀 Quick Start

1. **Clone** the repo and `cd` into it.
2. Paste the Compose file below into **`docker-compose.yml`** (edit secrets if you like).
3. Run

```bash
docker compose up --build -d
````

4. Open **[http://localhost:8080](http://localhost:8080)** in your browser.
   Default login → **admin / admin123**

```yaml
# docker-compose.yml
services:
  panel:
    image: ghcr.io/admlars2/mcdock:latest   # pull from GHCR
    container_name: mcdock
    restart: unless-stopped

    ports:
      - "8080:8000"           # host:container

    volumes:
      - {minecraft-server-directory}:/data          # change this!

    environment:
      MC_ROOT: /data
      CORS_ORIGINS: [http://localhost:8080]
      JWT_SECRET: super-secret-change-me-123        # change this!
      PANEL_USER: your-username                     # change this!
      PANEL_PASSWORD_HASH: generated_pwd_hash       # change this!

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### 🔑  Generate a new password hash

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Generate a JWT Token

```bash
python backend/generate_pw_hash.py "your-strong-password"
```

Copy the output string into `PANEL_PASSWORD_HASH`.

---

## 📂  Project Structure

```
MCDock/
├─ backend/     FastAPI API, schedulers, Docker integration
├─ frontend/    React + Vite web interface
├─ Dockerfile   Multi-stage build (UI → backend static)
└─ docker-compose.yml
```

---

## ✨  Features

| Category              | Highlights                                             |
| --------------------- | ------------------------------------------------------ |
| **Server lifecycle**  | Create, start, stop, restart servers with one click    |
| **Real-time console** | Live logs & commands over WebSockets                   |
| **Scheduler**         | Cron-style tasks for backups, restarts, or mod updates |
| **Backups**           | Tar + rotate logic, configurable retention             |
| **Metrics**           | CPU, RAM and TPS charts (Prometheus-ready)             |
| **Auth**              | JWT-based login, hashed passwords, CORS configurable   |
| **CI-ready**          | Multistage image, Push-to-Deploy via GitHub Actions    |

---

## 🛠️  Development

```bash
# UI hot-reload
cd frontend
npm ci
npm run dev        # http://localhost:5173

# API hot-reload
cd ../backend
poetry install
uvicorn src.mcdock.main:app --reload --port 8000
```

The Vite dev-server is already proxied to `localhost:8000`, so API calls work without CORS headaches.

---

## 📜  License

MIT © 2025 Adam Larson