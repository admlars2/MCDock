# MCDock Frontend

This is the frontend for **MCDock**, a Minecraft server management platform. It provides a modern, responsive web UI for managing Minecraft server instances, backups, schedules, and more.

## Features

- Create, edit, and delete Minecraft server instances
- Configure Docker images, memory, environment variables, and ports
- Start, stop, and restart servers
- Real-time log streaming and resource stats (CPU, memory)
- Manage backups: create, restore, and delete
- Schedule automated tasks (backups, restarts, etc.)
- User authentication and session management
- Responsive design with dark mode

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** (build tool)
- **Tailwind CSS** (styling)
- **React Router** (routing)
- **@tanstack/react-query** (data fetching/caching)
- **WebSockets** (real-time logs/stats)
- **ESLint** (linting)

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API clients and types
│   ├── components/    # Reusable UI components
│   ├── context/       # React context (auth, etc.)
│   ├── hooks/         # Custom React hooks
│   ├── layouts/       # Layout components
│   ├── lib/           # Utility functions
│   ├── pages/         # Route-level components
│   ├── index.css      # Tailwind and global styles
│   └── main.tsx       # App entrypoint
├── public/
├── index.html
├── vite.config.ts
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. **Install dependencies:**
   ```sh
   npm install
   ```

2. **Set API base URL:**
   - Create a `.env` file in `frontend/` with:
     ```
     VITE_API_BASE=http://localhost:8000
     ```
   - Adjust the URL if your backend runs elsewhere.

3. **Start the development server:**
   ```sh
   npm run dev
   ```
   The app will be available at [http://localhost:5173](http://localhost:5173) by default.

### Building for Production

```sh
npm run build
```
The output will be in the `dist/` directory.

## Usage

- Log in with your credentials (set up via backend).
- Manage server instances, view logs, stats, backups, and schedules.
- All actions are performed via the backend API.

## Environment Variables

- `VITE_API_BASE`: Base URL for the backend API (default: `http://localhost:8000`).

## Linting

Run ESLint to check code quality:

```sh
npm run lint
```

## Testing

No unit tests are included by default. You can add your own using your preferred React testing library.

## License

MIT License

---

**MCDock** © 2025