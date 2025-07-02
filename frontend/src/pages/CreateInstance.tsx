import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateInstance } from "../hooks/useInstances";
import { COMPOSE_TEMPLATE } from "../api/templates";
import { InstanceForm } from "../components/InstanceForm";

export default function CreateInstance() {
    /* ───────── state ───────── */
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

    /* ─── UI ─────────────────────────────────────────────── */
    return (
        <div className="w-full max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">Create new instance</h1>

        {err && <p className="mb-4 text-red-500 whitespace-pre-wrap">{err}</p>}

        <InstanceForm initial={COMPOSE_TEMPLATE} onSubmit={(payload) => createMut.mutate(payload)} saving={createMut.isPending} />
        </div>
    );
}