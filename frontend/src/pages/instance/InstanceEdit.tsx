import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
    useGetCompose,
    useUpdateCompose,
} from "../../hooks/useInstances";
import { InstanceForm } from "../../components/InstanceForm";
import type { InstanceCompose, InstanceUpdate } from "../../api/types";

export default function InstanceEdit() {
    const { name } = useParams<{ name: string }>();
    const nav = useNavigate();

    /* ─── fetch existing compose ─── */
    const { data: compose, isLoading, isError } = useGetCompose(name!);

    /* ─── mutation ─── */
    const [err, setErr] = useState("");
    const updateMut = useUpdateCompose(name!, {
        onSuccess: () => nav(`/instances/${name}`, { replace: true }),
        onError: (error: any) => {
        // Axios-style error shape fallback
        const detail = error?.response?.data?.detail ?? error?.detail;
        if (Array.isArray(detail)) {
            setErr(
            detail
                .map((d: any) =>
                typeof d.msg === "string"
                    ? d.msg.replace(/^Value error,\s*/i, "")
                    : null,
                )
                .filter(Boolean)
                .join("\n") || "Failed to update instance",
            );
        } else {
            setErr(typeof detail === "string" ? detail : "Failed to update instance");
        }
        },
    });

    const handleSubmit = (payload: InstanceCompose) => {
        const patch: InstanceUpdate = {
        eula: payload.eula,
        memory: payload.memory,
        env: payload.env,
        ports: payload.ports,
        };
        updateMut.mutate(patch);
    };

    /* ─── guards ─── */
    if (isLoading) return <p className="p-6">Loading compose…</p>;
    if (isError || !compose) return <p className="p-6 text-red-600">Compose not found.</p>;

    /* ─── UI ─── */
    return (
        <div className="w-full max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">Edit { name }</h1>

        {err && (
            <p className="mb-4 text-red-500 whitespace-pre-wrap">{err}</p>
        )}

        <InstanceForm
            initial={compose}
            disableName
            onSubmit={handleSubmit}
            saving={updateMut.isPending}
        />
        </div>
    );
}
