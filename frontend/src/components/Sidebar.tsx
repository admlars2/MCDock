import { Link, useLocation } from "react-router-dom";
import { useApiReady }        from "../hooks/useApiReady";

export default function Sidebar() {
    const { pathname }            = useLocation();
    const { data, isLoading,
            isError, isFetching } = useApiReady();

    /* ------- API status derivation ------- */
    const apiStatus =
        isError            ? "down"
    : isLoading          ? "loading"
    : isFetching         ? "refreshing"
    : data?.status === "ok"
        ? "up"
        : "down";

    const dotClass =
        apiStatus === "up"          ? "bg-green-500"
    : apiStatus === "loading"     ? "bg-yellow-400 animate-pulse"
    : apiStatus === "refreshing"  ? "bg-yellow-300 animate-ping"
    :                              "bg-red-600";

    /* ------- helper: active link styling ------- */
    const linkBase   = "flex items-center gap-2 px-4 py-2 rounded-md";
    const activeCls  = "bg-gray-700 text-white";
    const inactive   = "text-gray-300 hover:bg-gray-700 hover:text-white";

    return (
        <aside className="h-screen w-56 bg-gray-800 text-gray-100 flex flex-col">
        {/* Brand / title */}
        <div className="px-4 py-3 text-xl font-semibold tracking-wide">
            MCDock Panel
        </div>

        {/* Nav links */}
        <nav className="flex-1 mt-4 space-y-1">
            <Link
            to="/instances"
            className={`${linkBase} ${pathname.startsWith("/instances") ? activeCls : inactive}`}
            >
            🗄️ <span>Instances</span>
            </Link>

            <Link
            to="/schedules"
            className={`${linkBase} ${pathname.startsWith("/schedules") ? activeCls : inactive}`}
            >
            ⏰ <span>Schedules</span>
            </Link>
        </nav>

        {/* Footer: API status */}
        <div className="px-4 py-3 border-t border-gray-700 flex items-center gap-2 text-sm">
            <span className={`inline-block w-3 h-3 rounded-full ${dotClass}`} />
            {apiStatus === "up"
            ? "API online"
            : apiStatus === "loading"
            ? "Connecting…"
            : apiStatus === "refreshing"
            ? "Re-checking…"
            : "API offline"}
        </div>
        </aside>
    );
}
