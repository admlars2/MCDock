
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
    useSchedules,
    useAddBackupSchedule,
    useAddRestartSchedule,
    useDeleteSchedule,
} from "../../hooks/useSchedules";
import CronPicker from "../../components/instance/CronPicker";

function formatISO(iso?: string | null) {
    if (!iso) return "n/a";
    return new Date(iso).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    });
}

export default function InstanceSchedules() {
    const { name } = useParams<{ name: string }>();
    const navigate = useNavigate();
    if (!name) return null;                            // route guard

    /* ───────── data ───────── */
    const { data: jobs, isLoading, isError } = useSchedules(name);

    /* ───────── mutations ──── */
    const addBackup  = useAddBackupSchedule(name);
    const addRestart = useAddRestartSchedule(name);
    const delJob     = useDeleteSchedule(name);

    /* ───────── local state (simple form) ───────── */
    const [cron, setCron]       = useState("0 */1 * * *");
    const [kind, setKind]       = useState<"backup"|"restart">("backup");

    const handleAdd = () => {
        if (!cron.trim()) return;
        (kind === "backup" ? addBackup : addRestart).mutate(cron.trim());
    };

    /* ───────── render ───────── */
    return (
        <div className="p-6 max-w-3xl mx-auto space-y-6 text-white">
        {/* header */}
        <div className="flex items-center gap-4">
            <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 rounded bg-gray-600 hover:bg-gray-500"
            >
            ← Back
            </button>
            <h1 className="text-2xl font-semibold flex-grow">
            Schedules for {name}
            </h1>
        </div>

        <div className="flex flex-wrap items-start gap-6
                        bg-gray-800 p-6 rounded">

            <div className="flex-1 min-w-30">
                <CronPicker value={cron} onChange={setCron} />
            </div>

            <div className="flex flex-col items-center gap-4 w-44">

                <label className="w-full text-sm">
                <span className="block mb-1">Type</span>
                <select
                    value={kind}
                    onChange={e => setKind(e.target.value as any)}
                    className="w-full p-2 rounded bg-gray-700 text-white"
                >
                    <option value="backup">Backup</option>
                    <option value="restart">Restart</option>
                </select>
                </label>

                {/* Add button */}
                <button
                onClick={handleAdd}
                disabled={addBackup.isPending || addRestart.isPending}
                className="h-8 w-full rounded bg-green-600 hover:bg-green-700
                            disabled:opacity-50"
                >
                {addBackup.isPending || addRestart.isPending ? "Adding…" : "Add"}
                </button>
            </div>
        </div>


        {/* list */}
        {isLoading && <p>Loading schedules…</p>}
        {isError   && <p className="text-red-500">Failed to load schedules.</p>}

        {jobs && jobs.length === 0 && (
            <p className="text-gray-400">No schedules yet.</p>
        )}

        {jobs && jobs.length > 0 && (
            <ul className="space-y-2">
            {jobs.map((j) => (
                <li
                key={j.id}
                className="flex items-center justify-between bg-gray-800 rounded p-3"
                >
                <div>
                    <p className="font-mono">{j.id}&nbsp;<span className="text-s text-gray-300">({j.schedule})</span></p>
                    <p className="text-xs text-gray-400">Next: {formatISO(j.next_run)}</p>
                </div>

                <button
                    onClick={() => delJob.mutate(j.id)}
                    disabled={delJob.isPending}
                    className="px-3 py-1 rounded bg-red-600 hover:bg-red-700 disabled:opacity-50 text-sm"
                >
                    Delete
                </button>
                </li>
            ))}
            </ul>
        )}
        </div>
    );
}
