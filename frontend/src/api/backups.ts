import { apiFetch } from "../lib/api";
import type { ResponseMessage } from "./types";

function asPosix(p: string) {
  // turn `triggered\2025-07-03-00-05.tar.gz` → `triggered/2025-07-03-00-05.tar.gz`
  return p.replaceAll("\\", "/");
}

/* -------------------------------------------------------------------------- */
/*  Backups                                                                   */
/* -------------------------------------------------------------------------- */

export const listBackups = (name: string) =>
    apiFetch<string[]>(`/backups/${encodeURIComponent(name)}`);

export const triggerBackup = (name: string) =>
    apiFetch<ResponseMessage>(`/backups/${encodeURIComponent(name)}/trigger`, {
        method: "PUT",
    });

export const restoreBackup = (instance: string, filePath: string) =>
    apiFetch<ResponseMessage>(
        `/backups/${encodeURIComponent(instance)}/${encodeURIComponent(asPosix(filePath))}/restore`,
        { method: "POST" },
    );

export const deleteBackup = (instance: string, filePath: string) =>
    apiFetch<void>(
        `/backups/${encodeURIComponent(instance)}/${encodeURIComponent(asPosix(filePath))}`,
        { method: "DELETE" },
    );