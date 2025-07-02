import { useEffect, useRef, useState } from "react";
import { openLogs } from "../../api/instances";
import {
    useRestartInstance,
    useSendCommand,
} from "../../hooks/useInstances";

interface Props {
    instanceName: string;
    isRunning: boolean;
}

export default function LogsPanel({ instanceName, isRunning }: Props) {
    /* ───────── log streaming ───────── */
    const restartMut = useRestartInstance();
    const [lines, setLines] = useState<string[]>([]);
    const socketRef = useRef<WebSocket | null>(null);
    const divRef    = useRef<HTMLDivElement>(null);

    const push = (txt: string) =>
        setLines(prev => [...prev.slice(-199), txt]);

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

    useEffect(() => {
        divRef.current?.scrollTo(0, divRef.current.scrollHeight);
    }, [lines]);

    /* ───────── command input ───────── */
    const [cmd, setCmd] = useState("");
    const inputRef      = useRef<HTMLInputElement>(null);

    // bind instanceName so we only pass the command string to mutate()
    const sendMut = useSendCommand(instanceName, {
        onError  : (e: any) => push(`[✖] ${String(e)}`),
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!cmd.trim()) return;
        sendMut.mutate(cmd.trim());
        push(`> ${cmd.trim()}`);      // echo locally
        setCmd("");
        // keep focus for rapid-fire commands
        inputRef.current?.focus();
    };

    /* ───────── UI ───────── */
    return (
        <div className="space-y-2">
        {/* log window */}
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

        {/* command bar */}
        <form onSubmit={handleSubmit} className="flex gap-2">
            <input
            ref={inputRef}
            type="text"
            value={cmd}
            onChange={(e) => setCmd(e.target.value)}
            placeholder="Type command…"
            disabled={!isRunning}
            className="flex-grow px-3 py-1 rounded bg-gray-800 text-white disabled:opacity-50"
            />
            <button
            type="submit"
            disabled={!isRunning || sendMut.isPending}
            className="px-4 py-1 bg-blue-600 rounded text-white hover:bg-blue-700 disabled:opacity-50"
            >
            {sendMut.isPending ? "Sending…" : "Send"}
            </button>
        </form>
        </div>
    );
}
