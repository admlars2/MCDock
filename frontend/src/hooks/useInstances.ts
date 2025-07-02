import {
    useQuery,
    useMutation,
    useQueryClient,
    type UseQueryOptions,
    type UseMutationOptions,
} from "@tanstack/react-query";
import {
    listInstances,
    startInstance,
    stopInstance,
    restartInstance,
    createInstance,
    sendCommand,
    getCompose,
    updateCompose
} from "../api/instances";
import { useApiReady } from "./useApiReady";
import type {
    InstanceInfo,
    ResponseMessage,
    InstanceCompose,
    InstanceUpdate
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

/* ---- restart ---- */
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

/* ---- send command ---- */
export function useSendCommand(
    instanceName: string,
    opts?: UseMutationOptions<ResponseMessage, unknown, string>,
    ) {
    const qc = useQueryClient();

    return useMutation<ResponseMessage, unknown, string>({
        mutationKey: ["sendCommand", instanceName],
        mutationFn : (command) => sendCommand(instanceName, command),
        onSuccess  : (d, v, ctx) => {
        invalidateInstances(qc);
        opts?.onSuccess?.(d, v, ctx);
        },
        ...opts,
    });
}

export function useGetCompose(
    name: string,
    opts?: UseQueryOptions<InstanceCompose>,
) {
    return useQuery<InstanceCompose>({
        queryKey: ["compose", name],
        queryFn : () => getCompose(name),
        ...opts,
    });
}

export function useUpdateCompose(
    name: string,
    opts?: UseMutationOptions<ResponseMessage, unknown, InstanceUpdate>,
) {
    const qc = useQueryClient();

    return useMutation<ResponseMessage, unknown, InstanceUpdate>({
        mutationKey: ["updateCompose", name],
        mutationFn : (patch) => updateCompose(name, patch),
        onSuccess  : (d, patch, ctx) => {
        qc.invalidateQueries({ queryKey: ["compose", name] });
        invalidateInstances(qc);           // status may have changed (RAM/EULA)
        opts?.onSuccess?.(d, patch, ctx);
        },
        ...opts,
    });
}