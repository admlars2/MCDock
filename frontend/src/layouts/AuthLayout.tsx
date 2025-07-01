import { Outlet } from "react-router-dom";
import Sidebar    from "../components/Sidebar";
import { useAuth } from "../context/AuthContext";

export default function AuthLayout() {
    const { token } = useAuth();

    return (
        <div className="flex min-h-screen bg-gray-900 text-gray-100">
            <Sidebar />

            <main className="flex-1 flex items-center justify-center">
                {token ? (
                    <Outlet />
                ) : (
                    <p className="text-gray-400">Please sign in to access the panel.</p>
                )}
            </main>
        </div>
    );
}