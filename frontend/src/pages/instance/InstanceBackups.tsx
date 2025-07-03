import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
    useBackups,
    useTriggerBackup,
    useRestoreBackup,
    useDeleteBackup,
} from "../../hooks/useBackups";

type Mode = "restore" | "delete";

function groupByBucket(list: string[]) {
    const map: Record<string, string[]> = {};
    for (const path of list) {
        const [bucket, rest] = path.split(/[/\\](.+)/); // works on \ or /
        (map[bucket] ??= []).push(rest);
    }
    // lexicographic newest-first inside each bucket
    Object.values(map).forEach(arr => arr.sort().reverse());
    // predictable bucket order (triggered first, then alpha)
    const orderedKeys = Object.keys(map).sort((a, b) =>
        a === "triggered" ? -1 : b === "triggered" ? 1 : a.localeCompare(b)
    );
    return orderedKeys.map(k => [k, map[k]] as const);
}

export default function InstanceBackups() {
    const { name } = useParams<{ name: string }>();
    const navigate = useNavigate();

    /* data */
    const { data: backups, isLoading, isError } = useBackups(name!);

    /* mutations */
    const triggerMut = useTriggerBackup(name!);
    const restoreMut = useRestoreBackup(name!);
    const deleteMut  = useDeleteBackup (name!);

    /* modal state */
    const [pending, setPending] = useState<{file: string; mode: Mode}|null>(null);
    const closeModal = () => setPending(null);

    const confirm = (file: string, mode: Mode) => setPending({ file, mode });

    const execute = () => {
        if (!pending) return;
        if (pending.mode === "restore") restoreMut.mutate(pending.file);
        if (pending.mode === "delete")  deleteMut .mutate(pending.file);
        closeModal();
    };

    /* render */
    return (
        <div className="p-6 max-w-3xl mx-auto text-white space-y-6">
        {/* header */}
        <div className="flex items-center gap-4">
            <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 rounded bg-gray-600 hover:bg-gray-500"
            >
            ← Back
            </button>
            <h1 className="text-2xl font-semibold flex-grow">
            Backups for {name}
            </h1>

            <button
            onClick={() => triggerMut.mutate()}
            disabled={triggerMut.isPending}
            className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 disabled:opacity-50"
            >
            {triggerMut.isPending ? "Creating…" : "Backup now"}
            </button>
        </div>

        {/* list */}
        {isLoading && <p>Loading backups…</p>}
        {isError   && <p className="text-red-500">Failed to load backups.</p>}

        {backups?.length === 0 && (
            <p className="text-gray-400">No backups yet.</p>
        )}

        {backups && backups.length > 0 && (
        <div className="space-y-4">
            {groupByBucket(backups).map(([bucket, files]) => (
            <details key={bucket} className="bg-gray-800 rounded">
                <summary className="cursor-pointer px-4 py-2 select-none
                                    flex justify-between items-center">
                <span className="capitalize">{bucket}</span>
                <span className="text-xs text-gray-400">{files.length} file(s)</span>
                </summary>

                {/* one bucket ------------------------------------------------ */}
                <ul className="space-y-2 p-4 pt-3">
                {files.map(file => (
                    <li key={file}
                        className="flex items-center justify-between bg-gray-900
                                rounded p-3 text-sm">
                    <span className="truncate max-w-[60%]">{file}</span>

                    <div className="flex gap-2">
                        <button
                        onClick={() => confirm(`${bucket}/${file}`, "restore")}
                        disabled={restoreMut.isPending}
                        className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-700
                                    disabled:opacity-50">
                        Restore
                        </button>
                        <button
                        onClick={() => confirm(`${bucket}/${file}`, "delete")}
                        disabled={deleteMut.isPending}
                        className="px-3 py-1 rounded bg-red-600 hover:bg-red-700
                                    disabled:opacity-50">
                        Delete
                        </button>
                    </div>
                    </li>
                ))}
                </ul>
            </details>
            ))}
        </div>
        )}

        {/* modal */}
        {pending && (
            <div className="fixed inset-0 backdrop-blur-sm bg-black/60 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded p-6 w-80 space-y-4 text-center">
                <p>
                {pending.mode === "restore"
                    ? "Restore"
                    : "Delete"}{" "}
                <span className="font-mono break-all">{pending.file}</span>?
                {pending.mode === "restore" && (
                    <>
                    <br />
                    The server will be stopped and restarted.
                    </>
                )}
                </p>

                <div className="flex justify-center gap-4">
                <button
                    onClick={closeModal}
                    className="px-4 py-2 rounded bg-gray-600 hover:bg-gray-500"
                >
                    Cancel
                </button>
                <button
                    onClick={execute}
                    disabled={restoreMut.isPending || deleteMut.isPending}
                    className="px-4 py-2 rounded bg-red-600 hover:bg-red-700 disabled:opacity-50"
                >
                    {pending.mode === "restore"
                    ? restoreMut.isPending
                        ? "Restoring…"
                        : "Confirm"
                    : deleteMut.isPending
                        ? "Deleting…"
                        : "Confirm"}
                </button>
                </div>
            </div>
            </div>
        )}
        </div>
    );
}