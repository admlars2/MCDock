// components/LogsPane.tsx
import { useEffect, useRef, useState } from "react";
import { openLogs } from "../../api/instances";
import { useRestartInstance } from "../../hooks/useInstances";

interface Props {
    instanceName: string;
    isRunning: boolean;
}

export default function LogsPane({ instanceName, isRunning }: Props) {
    const restartMut = useRestartInstance();   // to watch .isPending
    const [lines, setLines] = useState<string[]>([]);
    const socketRef = useRef<WebSocket | null>(null);
    const divRef    = useRef<HTMLDivElement>(null);

    const push = (txt: string) =>
        setLines(prev => [...prev.slice(-199), txt]);

    /* manage WebSocket */
    useEffect(() => {
        if (restartMut.isPending) {
            socketRef.current?.close();
            socketRef.current = null;
            push("-- restart initiated --");
            return;
        }

        if (isRunning) {
            const ws = openLogs(instanceName);
            socketRef.current = ws;

            ws.onmessage = ev => push(ev.data);
            ws.onerror   = () => push("[log stream error]");
            ws.onclose   = () => push("-- log stream closed --");

            return () => ws.close();
        }

        socketRef.current?.close();
        socketRef.current = null;
        push("-- server stopped --");
    }, [instanceName, isRunning, restartMut.isPending]);

    /* auto-scroll */
    useEffect(() => {
        divRef.current?.scrollTo(0, divRef.current.scrollHeight);
    }, [lines]);

    return (
        <div
        ref={divRef}
        className="h-64 overflow-y-auto bg-black text-green-400 font-mono text-sm rounded p-3 border border-gray-700"
        >
        {lines.length === 0 ? (
            <p className="text-gray-500">
            {isRunning ? "Waiting for logs…" : "Server is offline."}
            </p>
        ) : (
            lines.map((l, i) => <div key={i}>{l}</div>)
        )}
        </div>
    );
}
