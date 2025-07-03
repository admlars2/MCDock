import {
    useQuery,
    useMutation,
    useQueryClient,
    type UseQueryOptions,
    type UseMutationOptions,
} from "@tanstack/react-query";

import {
    listBackups,
    triggerBackup,
    restoreBackup,
    deleteBackup,
} from "../api/backups";
import type { ResponseMessage } from "../api/types";

/* ---------- helpers ------------------------------------------------ */
function invalidateBackups(
    qc: ReturnType<typeof useQueryClient>,
    instance: string,
) {
    qc.invalidateQueries({ queryKey: ["backups", instance] });
}

/* ---------- list --------------------------------------------------- */
export function useBackups(
    instance: string,
    opts?: UseQueryOptions<string[]>,
) {
    return useQuery<string[]>({
        queryKey: ["backups", instance],
        queryFn: () => listBackups(instance),
        ...opts,
    });
}

/* ---------- trigger ------------------------------------------------ */
export function useTriggerBackup(
    instance: string,
    opts?: UseMutationOptions<ResponseMessage, unknown, void>,
) {
    const qc = useQueryClient();
    return useMutation<ResponseMessage, unknown, void>({
        mutationKey: ["triggerBackup", instance],
        mutationFn: () => triggerBackup(instance),
        onSuccess: (d, v, ctx) => {
        invalidateBackups(qc, instance);
        opts?.onSuccess?.(d, v, ctx);
        },
        ...opts,
    });
}

/* ---------- restore ------------------------------------------------ */
export function useRestoreBackup(
    instance: string,
    opts?: UseMutationOptions<ResponseMessage, unknown, string>,
) {
    const qc = useQueryClient();
    return useMutation<ResponseMessage, unknown, string>({
        mutationKey: ["restoreBackup", instance],
        mutationFn: (file) => restoreBackup(instance, file),
        onSuccess: (d, file, ctx) => {
        invalidateBackups(qc, instance);
        opts?.onSuccess?.(d, file, ctx);
        },
        ...opts,
    });
}

/* ---------- delete ------------------------------------------------- */
export function useDeleteBackup(
    instance: string,
    opts?: UseMutationOptions<void, unknown, string>,
) {
    const qc = useQueryClient();
    return useMutation<void, unknown, string>({
        mutationKey: ["deleteBackup", instance],
        mutationFn: (relPath) => deleteBackup(instance, relPath),
        onSuccess: (v, relPath, ctx) => {
        invalidateBackups(qc, instance);
        opts?.onSuccess?.(v, relPath, ctx);
        },
        ...opts,
    });
}
