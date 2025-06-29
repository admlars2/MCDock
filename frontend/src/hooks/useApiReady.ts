import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../api/health";
import type { HealthResponse } from "../api/types";

export function useApiReady() {
    return useQuery<HealthResponse>({
        queryKey: ["health"],
        queryFn:  getHealth,

        retry: false,
        staleTime: Infinity,
        refetchOnWindowFocus: false, 
        refetchInterval: (query) => query.state.status === "error" ? 5_000 : false,
    });
}