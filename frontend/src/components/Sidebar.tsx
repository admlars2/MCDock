import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useApiReady }  from "../hooks/useApiReady";
import { useAuth }      from "../context/AuthContext";
import LoginModal from "./LoginModal";

export default function Sidebar() {
    const { pathname } = useLocation();
    const { token, user, logout } = useAuth();
    const [showModal, setShowModal] = useState(false);

    // ─── API status ───────────────────────────────────────────────
    const { data, isLoading, isError, isFetching } = useApiReady();
    const apiStatus =
        isError ? "down"
        : isLoading ? "loading"
        : isFetching ? "refreshing"
        : data?.status === "ok"
        ? "up"
        : "down";

    const dotClass =
        apiStatus === "up" ? "bg-green-500"
        : apiStatus === "loading" ? "bg-yellow-400 animate-pulse"
        : apiStatus === "refreshing" ? "bg-yellow-300 animate-ping"
        : "bg-red-600";

    // ─── nav link helpers ─────────────────────────────────────────
    const linkBase  = "flex items-center gap-2 px-4 py-2 rounded-md";
    const activeCls = "bg-gray-700 text-white";
    const inactive  = "text-gray-300 hover:bg-gray-700 hover:text-white";

    // ─── handlers ────────────────────────────────────────────────
    async function handleLogout() {
        await logout();
        setShowModal(true);
    }

    return (
        <>
        <aside className="h-screen w-64 bg-gray-800 text-gray-100 text-lg flex flex-col">
            {/* Title */}
            <div className="px-4 py-3 text-xl font-semibold tracking-wide">
                MCDock Panel
            </div>

            {/* Nav links */}
            <nav className="flex-1 mt-4 space-y-1">
                <Link
                to="/instances"
                className={`${linkBase} ${pathname.endsWith("/instances") ? activeCls : inactive}`}
                >
                🗄️ <span>Instances</span>
                </Link>
            </nav>

            {/* Auth & API status footer */}
            <div className="px-4 py-3 border-t border-gray-700 flex flex-col gap-2 text-base">
                {/* Logged-in / Logged-out row */}
                {token ? (
                <div className="flex items-center justify-between">
                    <span className="truncate">Signed in as <strong>{user}</strong></span>
                    <button
                        onClick={handleLogout}
                        className="text-red-400 hover:text-red-300"
                        title="Logout"
                    >
                    ⏻
                    </button>
                </div>
                ) : (
                <button
                    onClick={() => setShowModal(true)}
                    className="text-blue-400 hover:underline text-left"
                >
                    Log in →
                </button>
                )}

                {/* API health row */}
                <div className="flex items-center gap-2 text-xs">
                <span className={`inline-block w-3 h-3 rounded-full ${dotClass}`} />
                {apiStatus === "up"
                    ? "API online"
                    : apiStatus === "loading"
                    ? "Connecting…"
                    : apiStatus === "refreshing"
                    ? "Re-checking…"
                    : "API offline"}
                </div>
                
            </div>
        </aside>
        <LoginModal open={showModal} onClose={() => setShowModal(false)} />
        </>
    );
}