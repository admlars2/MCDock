import { apiFetch } from "../lib/api";
import type { TokenResponse, ResponseMessage } from "./types";

export function getBearerToken(username: string, password: string) {
    return apiFetch<TokenResponse>("/auth/login", { 
        auth: false, 
        method: 'POST',
        json: {
            username,
            password
        }
    });
}

export function logout() {
    return apiFetch<ResponseMessage>("/auth/logout", { auth: false, method: 'POST' });
}