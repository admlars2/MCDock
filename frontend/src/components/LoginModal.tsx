import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginModal({ open, onClose }: { open: boolean; onClose(): void }) {
    const { login }  = useAuth();
    const [err, setErr] = useState("");
    const [shake, setShake] = useState(false);     // trigger CSS keyframe

    if (!open) return null;

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);

        // grab and validate
        const username = fd.get("username");
        const password = fd.get("password");

        if (!username || !password) {
            setErr("Both fields are required");
            return;
        }

        try {
            await login(username as string, password as string);
            setErr("");
            onClose();
        } catch {
            setErr("Invalid credentials");
            setShake(true);
            setTimeout(() => setShake(false), 400);
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <form
            onSubmit={handleSubmit}
            className="bg-gray-800 text-white p-8 rounded space-y-4 w-80"
        >
            <h2 className="text-xl font-semibold">Sign in</h2>

            {err && (
            <p className={`text-red-400 ${shake ? "animate-shake" : ""}`}>{err}</p>
            )}

            <input
                name="username"
                placeholder="Username"
                className="w-full p-2 rounded bg-gray-700 text-white text-lg placeholder-gray-400"
            />
            <input
                name="password"
                type="password"
                placeholder="Password"
                className="w-full p-2 rounded bg-gray-700 text-white text-lg placeholder-gray-400"
            />

            <div className="flex gap-2 justify-end">
            <button
                type="button"
                onClick={onClose}
                className="px-3 py-1 cursor-pointer"
            >
                Cancel
            </button>
            <button
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded cursor-pointer"
            >
                Log in
            </button>
            </div>
        </form>
        </div>
    );
}