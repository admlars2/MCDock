const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";
const REST_URL = new URL(API_BASE, window.location.origin);
const WS_PROTO = REST_URL.protocol === "https:" ? "wss:" : "ws:";
const WS_BASE  = `${WS_PROTO}//${REST_URL.host}${REST_URL.pathname.replace(/\/?$/, "/")}`;

export function buildWsUrl(path: string): string {
    const relPath = path.replace(/^\/+/, "");
    const url = new URL(relPath, WS_BASE);

    const jwt = (window as any).currentJwt as string | null;
    if (jwt) url.searchParams.set("token", jwt);

    return url.toString();
}