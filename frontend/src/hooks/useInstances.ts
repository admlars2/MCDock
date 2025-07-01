import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  listInstances,
  startInstance,
  stopInstance,
  restartInstance,
  deleteInstance,
  createInstance,
} from "../api/instances";
import { useApiReady } from "./useApiReady";
import type {
  InstanceInfo,
  ResponseMessage,
  InstanceCompose,
} from "../api/types";

/* ─────────────────── GET list ─────────────────── */
export function useInstances() {
    const { data: health, isSuccess } = useApiReady();
    const enabled = isSuccess && health?.status === "ok";

    return useQuery<InstanceInfo[]>({
        queryKey: ["instances"],
        queryFn: listInstances,
        enabled,
        staleTime: 30_000,
    });
}

/* ─────────────────── mutations helper ─────────── */
function invalidateInstances(qc: ReturnType<typeof useQueryClient>) {
    qc.invalidateQueries({ queryKey: ["instances"] });
}

/* ---- start ---- */
export function useStartInstance(
    opts?: UseMutationOptions<ResponseMessage, unknown, string>,
) {
    const qc = useQueryClient();
    return useMutation({
        mutationKey: ["startInstance"],
        mutationFn: startInstance,
        onSuccess: (d, n, ctx) => {
        invalidateInstances(qc);
        opts?.onSuccess?.(d, n, ctx);
        },
        ...opts,
    });
    }

/* ---- stop ---- */
export function useStopInstance(
    opts?: UseMutationOptions<ResponseMessage, unknown, string>,
) {
    const qc = useQueryClient();
    return useMutation({
        mutationKey: ["stopInstance"],
        mutationFn: stopInstance,
        onSuccess: (d, n, ctx) => {
        invalidateInstances(qc);
        opts?.onSuccess?.(d, n, ctx);
        },
        ...opts,
    });
    }

/* ---- restart (optional) ---- */
export function useRestartInstance(
    opts?: UseMutationOptions<ResponseMessage, unknown, string>,
) {
    const qc = useQueryClient();
    return useMutation({
        mutationKey: ["restartInstance"],
        mutationFn: restartInstance,
        onSuccess: (d, n, ctx) => {
        invalidateInstances(qc);
        opts?.onSuccess?.(d, n, ctx);
        },
        ...opts,
    });
}

/* ---- delete (optional) ---- */
export function useDeleteInstance(
    opts?: UseMutationOptions<void, unknown, string>,
) {
    const qc = useQueryClient();
    return useMutation({
        mutationKey: ["deleteInstance"],
        mutationFn: deleteInstance,
        onSuccess: (d, n, ctx) => {
        invalidateInstances(qc);
        opts?.onSuccess?.(d, n, ctx);
        },
        ...opts,
    });
}

/* ---- create ---- */
export function useCreateInstance(
    opts?: UseMutationOptions<ResponseMessage, unknown, InstanceCompose>,
    ) {
    const qc = useQueryClient();
    return useMutation({
        mutationKey: ["createInstance"],
        mutationFn: createInstance,              // (payload) => api call
        onSuccess: (d, payload, ctx) => {
        invalidateInstances(qc);               // refresh list on success
        opts?.onSuccess?.(d, payload, ctx);
        },
        ...opts,
    });
}