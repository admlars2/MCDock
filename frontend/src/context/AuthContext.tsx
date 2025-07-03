import { createContext, useContext, useState, useEffect } from "react";
import { getBearerToken, logout as apiLogout } from "../api/auth";

interface AuthState {
    token: string | null;
    user : string | null;
}

interface AuthCtx extends AuthState {
    login(username: string, password: string): Promise<void>;
    logout(): Promise<void>;
}

const AuthContext = createContext<AuthCtx | undefined>(undefined);
const TOKEN_KEY = "panel.jwt";
const USER_KEY  = "panel.user";

function getExpiry(unverifiedJwt: string): number | null {
    try {
        const [, payload] = unverifiedJwt.split(".");
        const decoded = JSON.parse(atob(payload));
        return typeof decoded.exp === "number" ? decoded.exp * 1000 : null;
    } catch {
        return null;
    }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
    const [user , setUser ] = useState<string | null>(() => localStorage.getItem(USER_KEY));

    /** called by the login form */
    async function login(username: string, password: string) {
        const { token, user } = await getBearerToken(username, password);
        setToken(token);
        setUser(user);
        localStorage.setItem(TOKEN_KEY, token);
        localStorage.setItem(USER_KEY, user);
    }

    async function logout() {
        // optional round-trip – ignore errors (token may be expired)
        try { await apiLogout(); } catch {}
        setToken(null);
        setUser(null);
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
    }

    /* when token changes, keep apiFetch up-to-date */
    useEffect(() => {
        // keep global header helper in sync  ❱ both truthy & null
        (window as any).currentJwt = token ?? null;

        // clear previous timer
        let id: number | undefined;
        if (!token) return () => clearTimeout(id);

        const expMs = getExpiry(token);
        if (expMs) {
            const delay = expMs - Date.now();
            id = window.setTimeout(logout, Math.max(delay, 0));
        }
        return () => clearTimeout(id);
    }, [token]);


    return (
        <AuthContext.Provider value={{ token, user, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
    return ctx;
}