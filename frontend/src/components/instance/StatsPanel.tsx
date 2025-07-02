import { useEffect, useRef, useState } from "react";
import { openStats } from "../../api/instances";
import { useRestartInstance } from "../../hooks/useInstances";

interface Props {
    instanceName: string;
    isRunning: boolean;
}

interface StatState {
    cpu: number | null;   // percent
    mem: number | null;   // MiB
}

export default function StatsPanel({ instanceName, isRunning }: Props) {
    const restartMut = useRestartInstance();
    const [stats, setStats] = useState<StatState>({ cpu: null, mem: null });
    const socketRef = useRef<WebSocket | null>(null);

    /* manage WebSocket */
    useEffect(() => {
        if (restartMut.isPending) {
        socketRef.current?.close();
        socketRef.current = null;
        return;
        }

        if (isRunning) {
        const ws = openStats(instanceName);
        socketRef.current = ws;

        ws.onmessage = ev => {
            try {
            const { cpu, mem } = JSON.parse(ev.data);
            console.log(ev)
            setStats({ cpu, mem });
            } catch {
            /* ignore malformed frames */
            }
        };

        ws.onerror = () => setStats({ cpu: null, mem: null });
        ws.onclose = () => setStats({ cpu: null, mem: null });

        return () => ws.close();
        }

        socketRef.current?.close();
        socketRef.current = null;
        setStats({ cpu: null, mem: null });
    }, [instanceName, isRunning, restartMut.isPending]);

    /* simple helper for display */
    const fmt = (v: number | null, unit: string) =>
        v === null ? "—" : `${v.toFixed(1)} ${unit}`;

    return (
        <div className="grid grid-cols-2 gap-4 text-sm text-gray-300">
        {/* CPU */}
        <div>
            <p className="uppercase text-xs tracking-wider text-gray-400">CPU</p>
            <p className="text-lg text-white">{fmt(stats.cpu, "%")}</p>
            <div className="w-full h-2 bg-gray-700 rounded">
            <div
                className="h-2 bg-green-500 rounded"
                style={{ width: `${Math.min(stats.cpu ?? 0, 100)}%` }}
            />
            </div>
        </div>

        {/* Memory */}
        <div>
            <p className="uppercase text-xs tracking-wider text-gray-400">Memory</p>
            <p className="text-lg text-white">{fmt(stats.mem, "MiB")}</p>
            <div className="w-full h-2 bg-gray-700 rounded">
            <div
                className="h-2 bg-blue-500 rounded"
                style={{
                width:
                    stats.mem !== null
                    ? `${Math.min((stats.mem / 4096) * 100, 100)}%` // assumes 4 GiB soft-cap; tweak as needed
                    : "0%",
                }}
            />
            </div>
        </div>
        </div>
    );
}
