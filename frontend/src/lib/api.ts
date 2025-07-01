type ApiError = { status: number; message: string; detail?: unknown };

export class HttpError extends Error {
    readonly status: number;
    readonly detail?: unknown;
    constructor({ status, message, detail }: ApiError) {
        super(message);
        this.status = status;
        this.detail = detail;
    }
}

const API   = import.meta.env.VITE_API_BASE as string;      // e.g. https://example.com/api

interface FetchOpts extends Omit<RequestInit, "body"> {
    /** automatically attach Bearer token (default true) */
    auth?: boolean;
    /** JSON payload – will be stringified */
    json?: unknown;
    /** milliseconds before abort (default 10 s) */
    timeout?: number;
    /** retry count for 5xx/Network errors (default 0) */
    retries?: number;
}

export async function apiFetch<T = unknown>(
    path: string,
    {
        auth   = true,
        json,
        timeout = 5_000,
        retries = 0,
        headers,
        ...rest
    }: FetchOpts = {},
): Promise<T> {
    const token = (window as any).currentJwt;
    const h = new Headers(headers);

    if (auth && token)  h.set("Authorization", `Bearer ${token}`);
    if (json !== undefined) h.set("Content-Type", "application/json")

    const ctrl = new AbortController();
    const id = setTimeout(() => ctrl.abort(), timeout);

    const init: RequestInit = {
        ...rest,
        headers: h,
        signal : ctrl.signal,
        ...(json !== undefined ? { body: JSON.stringify(json) } : {}),
    };

    try {
        const res = await fetch(API + path, init);

        if (!res.ok) {
            let detail: unknown = undefined;
            try { detail = await res.json(); } catch {}
            throw new HttpError({ status: res.status, message: res.statusText, detail });
        }

        // Auto-detect empty body
        return (res.status === 204 ? (undefined as T) : (await res.json())) as T;
    } catch (err) {
        if (!path.match("auth")) {
            console.log(init)
        }
        console.log(API + path, err)
        if (retries > 0 && (err instanceof TypeError || (err as any).name === "AbortError"))
            return apiFetch(path, { auth, json, timeout, retries: retries - 1, headers, ...rest });
        throw err;
    } finally {
        clearTimeout(id);
    }
}
