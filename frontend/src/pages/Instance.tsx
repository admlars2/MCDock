import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  useInstances,
  useStartInstance,
  useStopInstance,
  useRestartInstance,
} from "../hooks/useInstances";
import { openLogs } from "../api/instances";

export default function InstancePage() {
  const { name } = useParams<{ name: string }>();

  /* ───────── data & mutations ───────── */
  const { data, isLoading, isError } = useInstances();
  const instance = data?.find((i) => i.name === name);

  const startMut   = useStartInstance();
  const stopMut    = useStopInstance();
  const restartMut = useRestartInstance();

  /* ───────── logs state ───────── */
  const [logs, setLogs] = useState<string[]>([]);
  const logRef = useRef<HTMLDivElement>(null);

  /* Open / close the WebSocket when `name` changes */
  useEffect(() => {
    if (!name) return;
    const socket = openLogs(name);

    socket.onmessage = (ev) =>
      setLogs((prev) => [...prev.slice(-199), ev.data]); // keep 200
    socket.onerror = () =>
      setLogs((prev) => [...prev, "[Error receiving logs]"]);

    return () => socket.close();
  }, [name]);

  /* Auto-scroll on new lines */
  useEffect(() => {
    logRef.current?.scrollTo(0, logRef.current.scrollHeight);
  }, [logs]);

  /* ───────── render ───────── */
  if (isLoading) return <p className="p-6">Loading instance…</p>;
  if (isError || !instance)
    return <p className="p-6 text-red-600">Instance not found.</p>;

  const isRunning = instance.status === "running";

  return (
    <div className="p-6 space-y-6 text-white">
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
      </div>

      {/* live logs */}
      <div
        ref={logRef}
        className="h-64 overflow-y-auto bg-black text-green-400 font-mono text-sm rounded p-3 border border-gray-700"
      >
        {logs.length === 0 ? (
          <p className="text-gray-500">Waiting for logs…</p>
        ) : (
          logs.map((line, i) => <div key={i}>{line}</div>)
        )}
      </div>
    </div>
  );
}
