import { 
    useQuery,
    useMutation,
    useQueryClient,
    type UseMutationOptions,
} from "@tanstack/react-query";
import { listInstances, startInstance, stopInstance } from "../api/instances";
import { useApiReady }   from "./useApiReady";          // the health-check hook
import type { InstanceInfo, ResponseMessage} from "../api/types";

export function useInstances() {
    const { data: health, isSuccess: healthSuccess } = useApiReady();
    const enabled = healthSuccess && health?.status === "ok";

    return useQuery<InstanceInfo[]>({
        queryKey: ["instances"],
        queryFn : listInstances,
        enabled,            // ← magic line
        staleTime: 30_000,  // cache for 30 s; tweak as you like
    });
}

export function useStartInstance(
    options?: UseMutationOptions<ResponseMessage, unknown, string>,
    ) {
    const qc = useQueryClient();

    return useMutation<ResponseMessage, unknown, string>({
        mutationKey: ["startInstance"],
        mutationFn:  startInstance,
        onSuccess: (data, name, ctx) => {
        qc.invalidateQueries({ queryKey: ["instances"] });  // refresh table
        options?.onSuccess?.(data, name, ctx);
        },
        ...options,
    });
}

export function useStopInstance(
    options?: UseMutationOptions<ResponseMessage, unknown, string>,
    ) {
    const qc = useQueryClient();

    return useMutation<ResponseMessage, unknown, string>({
        mutationKey: ["stopInstance"],
        mutationFn:  stopInstance,
        onSuccess: (data, name, ctx) => {
        qc.invalidateQueries({ queryKey: ["instances"] });
        options?.onSuccess?.(data, name, ctx);
        },
        ...options,
    });
}