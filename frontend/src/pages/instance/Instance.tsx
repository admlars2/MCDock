import { useParams, Link } from "react-router-dom";
import {
    useInstances,
    useStartInstance,
    useStopInstance,
    useRestartInstance,
} from "../../hooks/useInstances";
import LogsPanel  from "../../components/instance/LogPanel";
import StatsPanel from "../../components/instance/StatsPanel";

export default function Instance() {
    const { name } = useParams<{ name: string }>();

    /* data & mutations */
    const { data, isLoading, isError } = useInstances();
    const instance   = data?.find((i) => i.name === name);
    const startMut   = useStartInstance();
    const stopMut    = useStopInstance();
    const restartMut = useRestartInstance();

    const isRunning = instance?.status === "running";

    /* guards */
    if (isLoading) return <p className="p-6">Loading instance…</p>;
    if (isError || !instance)
        return <p className="p-6 text-red-600">Instance not found.</p>;

    /* UI */
    return (
        <div className="p-6 w-max space-y-6 text-white">
        {/* header + controls */}
        <div className="flex flex-wrap items-center gap-4">
            <h1 className="text-2xl font-semibold flex-grow">{instance.name}</h1>

            {isRunning ? (
            <button
                onClick={() => stopMut.mutate(instance.name)}
                disabled={stopMut.isPending}
                className="px-4 py-2 bg-yellow-600 rounded hover:bg-yellow-700 disabled:opacity-50"
            >
                {stopMut.isPending ? "Stopping…" : "Stop"}
            </button>
            ) : (
            <button
                onClick={() => startMut.mutate(instance.name)}
                disabled={startMut.isPending}
                className="px-4 py-2 bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
            >
                {startMut.isPending ? "Starting…" : "Start"}
            </button>
            )}

            <button
            onClick={() => restartMut.mutate(instance.name)}
            disabled={restartMut.isPending}
            className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
            >
            {restartMut.isPending ? "Restarting…" : "Restart"}
            </button>

            <Link
                to={`/instances/${instance.name}/compose`}
                className="px-4 py-2 bg-gray-500 rounded hover:bg-gray-600"
            >
                Edit Compose
            </Link>

            <Link
                to={`/instances/${instance.name}/backups`}
                className="px-4 py-2 bg-purple-600 rounded hover:bg-purple-700"
            >
                Backups
            </Link>

            <Link
                to={`/instances/${instance.name}/schedules`}
                className="px-4 py-2 bg-blue-400 rounded hover:bg-blue-500"
            >
                Schedules
            </Link>
        </div>

        {/* panels */}
        <LogsPanel  instanceName={instance.name} isRunning={isRunning} />
        <StatsPanel instanceName={instance.name} isRunning={isRunning} />
        </div>
    );
}
