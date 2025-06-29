import { apiFetch } from "../lib/api";
import type { HealthResponse } from "./types";

export function getHealth() {
    return apiFetch<HealthResponse>("/health", { auth: false, timeout: 1_000});
}