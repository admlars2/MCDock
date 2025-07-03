import { apiFetch } from "../lib/api";
import type { ResponseMessage, ScheduledJob, CronSchedule } from "./types";

export const listSchedules = (instance: string) =>
  apiFetch<ScheduledJob[]>(`/schedules/${encodeURIComponent(instance)}`);

export const addBackupSchedule = (instance: string, cron: string) =>
    apiFetch<ResponseMessage>(`/schedules/backup/${encodeURIComponent(instance)}`, {
        method: "POST",
        json: { cron } satisfies CronSchedule,
    });

export const addRestartSchedule = (instance: string, cron: string) =>
    apiFetch<ResponseMessage>(`/schedules/restart/${encodeURIComponent(instance)}`, {
        method: "POST",
        json: { cron } satisfies CronSchedule,
    });

export const deleteSchedule = (jobId: string) =>
  apiFetch<void>(`/schedules/${encodeURIComponent(jobId)}`, { method: "DELETE" })