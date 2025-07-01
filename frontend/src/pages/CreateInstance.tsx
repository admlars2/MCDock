import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCreateInstance } from "../hooks/useInstances";
import type { InstanceCompose, EnvVar, PortBinding } from "../api/types";
import { STARTER_COMPOSE } from "../api/templates";

export default function CreateInstance() {
    /* ───────── state ───────── */
    const [form, setForm] = useState(() => ({
        name  : STARTER_COMPOSE.name,
        image : STARTER_COMPOSE.image,
        memory: STARTER_COMPOSE.memory,
        eula  : STARTER_COMPOSE.eula,
    }));
    const [env, setEnv] = useState<EnvVar[]>(STARTER_COMPOSE.env);
    const [ports, setPorts] = useState<PortBinding[]>(STARTER_COMPOSE.ports);
    const [err, setErr]  = useState("");

    /* ───────── react-query mutation ───────── */
    const nav      = useNavigate();
    const createMut = useCreateInstance({
        onSuccess: () => nav("/instances", { replace: true }),
        onError: (error: any) => {
            const detail = error?.detail?.detail;
            if (Array.isArray(detail)) {
                const msgs = detail.map((d: any) =>
                    typeof d.msg === "string"
                        ? d.msg.replace(/^Value error,\s*/i, "")
                        : null
                ).filter(Boolean).join("\n");
                setErr(msgs || "Failed to create instance");
            } else {
                setErr("Failed to create instance");
            }
        },
    });

    /* ─── helpers (basic fields) ────────────────────────── */
    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        const { name, value, type, checked } = e.target;
        setForm(f => ({ ...f, [name]: type === "checkbox" ? checked : value }));
    }

    /* ─── helpers (env table) ───────────────────────────── */
    function updateEnv(idx: number, field: "key" | "value", value: string) {
        setEnv(rows => rows.map((r, i) => (i === idx ? { ...r, [field]: value } : r)));
    }
    const addEnvRow = () => setEnv(r => [...r, { key: "", value: "" }]);
    const removeEnvRow = (idx: number) => setEnv(r => r.filter((_, i) => i !== idx));

    /* ─── helpers (ports table) ─────────────────────────── */
    function updatePort(
        idx: number,
        field: "host_port" | "container_port" | "type",
        value: string,
    ) {
        setPorts(rows =>
        rows.map((r, i) =>
            i === idx
            ? {
                ...r,
                [field]:
                    field === "type" ? (value as "tcp" | "udp") : Number(value),
                }
            : r,
        ),
        );
    }
    const addPortRow = () => setPorts(r => [...r, { host_port: 1024, container_port: 1024, type: "tcp" }]);
    const removePortRow = (i: number) => setPorts(r => r.filter((_, idx) => idx !== i));

    /* ─── submit ────────────────────────────────────────── */
    function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const payload: InstanceCompose = {
            ...form,
            env,
            ports: ports,
        };
        createMut.mutate(payload);
    }

    /* ─── UI ─────────────────────────────────────────────── */
    return (
        <div className="w-full max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">Create new instance</h1>

        {err && <p className="mb-4 text-red-500 whitespace-pre-wrap">{err}</p>}

        <form
            onSubmit={handleSubmit}
            className="space-y-8 bg-gray-800 text-gray-100 p-6 rounded"
        >
            {/* basic fields */}
            <div className="grid gap-4 md:grid-cols-2">
            <div>
                <label className="block mb-1">Name</label>
                <input
                name="name"
                value={form.name}
                onChange={handleChange}
                required
                className="w-full p-3 rounded bg-gray-700 text-white text-lg"
                />
            </div>
            <div>
                <label className="block mb-1">Docker image</label>
                <input
                name="image"
                value={form.image}
                onChange={handleChange}
                required
                className="w-full p-3 rounded bg-gray-700 text-white text-lg"
                />
            </div>
            <div>
                <label className="block mb-1">Memory (e.g. 6G)</label>
                <input
                type="text"
                name="memory"
                value={form.memory}
                onChange={e =>
                    setForm(f => ({ ...f, memory: e.target.value.toUpperCase().trim() }))
                }
                pattern="^[1-9]\d*[MG]$"
                required
                className="w-full p-3 rounded bg-gray-700 text-white text-lg"
                />
            </div>
            <div
                className="flex justify-center items-center gap-2"
            >
                <input
                    type="checkbox"
                    name="eula"
                    checked={form.eula}
                    onChange={handleChange}
                    className="accent-green-500"
                    />
                <label>
                    Accept Mojang{" "}
                    <a
                        href="https://account.mojang.com/documents/minecraft_eula"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline text-blue-300 hover:text-blue-400"
                    >
                    EULA
                    </a>
                </label>
            </div>
            </div>

            {/* env vars */}
            <div className="space-y-2">
            <div className="flex items-center justify-between">
                <h2 className="font-semibold">Environment variables</h2>
                <button
                type="button"
                onClick={addEnvRow}
                className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                >
                + Add
                </button>
            </div>

            {env.length === 0 && (
                <p className="text-gray-400 text-sm">No variables yet.</p>
            )}

            {env.map((row, idx) => (
                <div key={idx} className="flex gap-2">
                <input
                    value={row.key}
                    onChange={e => updateEnv(idx, "key", e.target.value.toUpperCase())}
                    placeholder="KEY"
                    className="flex-1 p-2 rounded bg-gray-700 text-white"
                />
                <input
                    value={row.value}
                    onChange={e => updateEnv(idx, "value", e.target.value)}
                    placeholder="value"
                    className="flex-1 p-2 rounded bg-gray-700 text-white"
                />
                <button
                    type="button"
                    onClick={() => removeEnvRow(idx)}
                    className="px-3 bg-red-600 hover:bg-red-700 rounded"
                    title="Delete row"
                >
                    ✕
                </button>
                </div>
            ))}
            </div>

            {/* port bindings */}
            <div className="space-y-2">
            <div className="flex items-center justify-between">
                <h2 className="font-semibold">Port bindings</h2>
                <button
                type="button"
                onClick={addPortRow}
                className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                >
                + Add
                </button>
            </div>

            {ports.length === 0 && (
                <p className="text-gray-400 text-sm">No port bindings yet.</p>
            )}

            {ports.map((row, idx) => (
                <div key={idx} className="flex gap-2">
                <input
                    type="number"
                    min={1}
                    max={65535}
                    value={row.host_port}
                    onChange={e => updatePort(idx, "host_port", e.target.value)}
                    placeholder="HOST_PORT"
                    className="w-32 p-2 rounded bg-gray-700 text-white"
                />
                <input
                    type="number"
                    min={1}
                    max={65535}
                    value={row.container_port}
                    onChange={e =>
                    updatePort(idx, "container_port", e.target.value)
                    }
                    placeholder="CONTAINER_PORT"
                    className="w-40 p-2 rounded bg-gray-700 text-white"
                />
                <select
                    value={row.type}
                    onChange={e => updatePort(idx, "type", e.target.value)}
                    className="w-28 p-2 rounded bg-gray-700 text-white capitalize"
                >
                    <option value="tcp">TCP</option>
                    <option value="udp">UDP</option>
                </select>
                <button
                    type="button"
                    onClick={() => removePortRow(idx)}
                    className="px-3 bg-red-600 hover:bg-red-700 rounded"
                    title="Delete row"
                >
                    ✕
                </button>
                </div>
            ))}
            </div>

            {/* actions */}
            <div className="flex gap-3 justify-end">
            <Link
                to="/instances"
                className="px-4 py-2 rounded bg-gray-600 hover:bg-gray-500"
            >
                Cancel
            </Link>
            <button
                disabled={createMut.isPending}
                className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 disabled:opacity-50"
            >
                {createMut.isPending ? "Creating…" : "Create"}
            </button>
            </div>
        </form>
        </div>
    );
}