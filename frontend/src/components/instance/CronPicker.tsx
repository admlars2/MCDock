import { useState, useEffect } from "react";

interface Props {
    value: string;
    onChange(v: string): void;
}

function detectMode(cron: string): "minutes"|"hours"|"daily"|"advanced" {
    if (!cron) return "minutes";
    if (cron.startsWith("*/")) return "minutes";
    if (cron.startsWith("0 */")) return "hours";
    const parts = cron.split(" ");
    if (parts.length === 5 && parts.slice(2).every(p => p === "*"))
        return "daily";
    return "advanced";
}

export default function CronPicker({ value, onChange }: Props) {
    const [mode, setMode] = useState(detectMode(value));

    /* ─── per-mode state ─── */
    const [nMinutes, setNMinutes] = useState(5);
    const [nHours,   setNHours]   = useState(1);
    const [hh,       setHh]       = useState(2);
    const [mm,       setMm]       = useState(0);
    const [raw,      setRaw]      = useState(value);
    const [tz,       setTz]       = useState(
        Intl.DateTimeFormat().resolvedOptions().timeZone ?? "UTC",
    );   // used only for the UI preview

    /* ─── keep external `value` in sync ─── */
    /* minutes                                         */
    useEffect(() => {
        if (mode === "minutes") onChange(`*/${nMinutes} * * * *`);
    }, [mode, nMinutes]);

    /* hours                                           */
    useEffect(() => {
        if (mode === "hours") onChange(`0 */${nHours} * * *`);
    }, [mode, nHours]);

    /* daily                                           */
    useEffect(() => {
        if (mode === "daily") onChange(`${mm} ${hh} * * *`);
    }, [mode, hh, mm]);

    /* advanced                                        */
    useEffect(() => {
        if (mode === "advanced") onChange(raw.trim());
    }, [mode, raw]);

    /* ─── UI ─── */
    return (
        <div className="space-y-3">
        {/* mode selector */}
        <select
            value={mode}
            onChange={e => setMode(e.target.value as any)}
            className="p-2 rounded bg-gray-700 text-white"
        >
            <option value="minutes">Every&nbsp;N&nbsp;minutes</option>
            <option value="hours">Every&nbsp;N&nbsp;hours</option>
            <option value="daily">Daily at&nbsp;HH:MM</option>
            <option value="advanced">Advanced (raw&nbsp;cron)</option>
        </select>

        {/* minutes */}
        {mode === "minutes" && (
            <div className="flex items-center gap-2">
            <input
                type="number" min={1}
                value={nMinutes}
                onChange={e => setNMinutes(+e.target.value || 1)}
                className="w-20 p-2 rounded bg-gray-700 text-white text-right"
            />
            <span>minute(s)&nbsp;</span>
            </div>
        )}

        {/* hours */}
        {mode === "hours" && (
            <div className="flex items-center gap-2">
            <input
                type="number" min={1}
                value={nHours}
                onChange={e => setNHours(+e.target.value || 1)}
                className="w-20 p-2 rounded bg-gray-700 text-white text-right"
            />
            <span>hour(s)&nbsp;</span>
            </div>
        )}

        {/* daily */}
        {mode === "daily" && (
            <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-1">
                HH
                <input
                type="number" min={0} max={23}
                value={hh}
                onChange={e => setHh(Math.min(23, Math.max(0, +e.target.value)))}
                className="w-16 p-1 rounded bg-gray-700 text-white text-right"
                />
            </label>
            <label className="flex items-center gap-1">
                MM
                <input
                type="number" min={0} max={59}
                value={mm}
                onChange={e => setMm(Math.min(59, Math.max(0, +e.target.value)))}
                className="w-16 p-1 rounded bg-gray-700 text-white text-right"
                />
            </label>

            {/* time zone selector – purely informational for now */}
            <select
                value={tz}
                onChange={e => setTz(e.target.value)}
                className="p-1 rounded bg-gray-700 text-white"
            >
                {/* keep short: local tz + UTC */}
                <option value={Intl.DateTimeFormat().resolvedOptions().timeZone}>
                {Intl.DateTimeFormat().resolvedOptions().timeZone}
                </option>
                <option value="UTC">UTC</option>
            </select>
            </div>
        )}

        {/* advanced */}
        {mode === "advanced" && (
            <textarea
            value={raw}
            onChange={e => setRaw(e.target.value)}
            rows={2}
            className="w-full p-2 rounded bg-gray-700 text-white font-mono"
            placeholder="*/5 * * * *"
            />
        )}

        {/* preview */}
        <p className="text-sm text-gray-400">
            Cron:&nbsp;<span className="font-mono">{value}</span>
            {mode === "daily" && <>&nbsp;({tz})</>}
        </p>
        </div>
    );
}
