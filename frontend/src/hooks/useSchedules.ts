import {
    useQuery,
    useMutation,
    useQueryClient,
    type UseQueryOptions,
    type UseMutationOptions,
} from "@tanstack/react-query";

import {
    listSchedules,
    addBackupSchedule,
    addRestartSchedule,
    deleteSchedule,
} from "../api/schedules";
import type { ResponseMessage, ScheduledJob } from "../api/types";

/* ── list schedules for one instance ───────────────────────────── */
export function useSchedules(
    instance: string,
    opts?: UseQueryOptions<ScheduledJob[]>,
) {
    return useQuery<ScheduledJob[]>({
        queryKey: ["schedules", instance],
        queryFn: () => listSchedules(instance),
        ...opts,
    });
}

/* internal helper ------------------------------------------------ */
function invalidate(qc: ReturnType<typeof useQueryClient>, instance: string) {
    qc.invalidateQueries({ queryKey: ["schedules", instance] });
}

/* ── create BACKUP schedule ────────────────────────────────────── */
export function useAddBackupSchedule(
    instance: string,
    opts?: UseMutationOptions<ResponseMessage, unknown, string>, // payload = cron
) {
    const qc = useQueryClient();
    return useMutation<ResponseMessage, unknown, string>({
        mutationKey: ["addBackupSchedule", instance],
        mutationFn: (cron) => addBackupSchedule(instance, cron),
        onSuccess: (d, cron, ctx) => {
        invalidate(qc, instance);
        opts?.onSuccess?.(d, cron, ctx);
        },
        ...opts,
    });
}

/* ── create RESTART schedule ───────────────────────────────────── */
export function useAddRestartSchedule(
    instance: string,
    opts?: UseMutationOptions<ResponseMessage, unknown, string>, // payload = cron
) {
    const qc = useQueryClient();
    return useMutation<ResponseMessage, unknown, string>({
        mutationKey: ["addRestartSchedule", instance],
        mutationFn: (cron) => addRestartSchedule(instance, cron),
        onSuccess: (d, cron, ctx) => {
        invalidate(qc, instance);
        opts?.onSuccess?.(d, cron, ctx);
        },
        ...opts,
    });
}

/* ── delete any schedule by job-id ─────────────────────────────── */
export function useDeleteSchedule(
    instance: string,
    opts?: UseMutationOptions<void, unknown, string>, // payload = jobId
) {
    const qc = useQueryClient();
    return useMutation<void, unknown, string>({
        mutationKey: ["deleteSchedule", instance],
        mutationFn: (jobId) => deleteSchedule(jobId),
        onSuccess: (d, jobId, ctx) => {
        invalidate(qc, instance);
        opts?.onSuccess?.(d, jobId, ctx);
        },
        ...opts,
    });
}
