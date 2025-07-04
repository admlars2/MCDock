import { apiFetch } from "../lib/api";
import { buildWsUrl } from "../lib/ws";
import type {
    InstanceInfo,
    ResponseMessage,
    InstanceUpdate,
    InstanceCompose,
} from "./types";

/* -------------------------------------------------------------------------- */
/*  Instance-lifecycle helpers                                                */
/* -------------------------------------------------------------------------- */

export const listInstances = () =>
    apiFetch<InstanceInfo[]>("/instances/");

export const startInstance = (name: string) =>
    apiFetch<ResponseMessage>(`/instances/${name}/start`, {
        method: "POST",
    });

export const stopInstance = (name: string) =>
    apiFetch<ResponseMessage>(`/instances/${name}/stop`, {
        method: "POST",
    });

export const restartInstance = (name: string) =>
    apiFetch<ResponseMessage>(`/instances/${name}/restart`, {
        method: "POST",
    });

export const sendCommand = (name: string, command: string) =>
    apiFetch<ResponseMessage>(`/instances/${name}/cmd`, {
        method: "POST",
        json: { command },
    });

/* -------------------------------------------------------------------------- */
/*  Compose & properties                                                      */
/* -------------------------------------------------------------------------- */

export const getCompose   = (name: string) =>
    apiFetch<InstanceCompose>(`/instances/${name}/compose`);

export const updateCompose = (name: string, patch: InstanceUpdate) =>
    apiFetch<ResponseMessage>(`/instances/${name}/compose`, {
        method: 'PUT',
        json: patch,
    });

/* -------------------------------------------------------------------------- */
/*  Template & instance creation                                              */
/* -------------------------------------------------------------------------- */

export const createInstance = (payload: InstanceCompose) =>
    apiFetch<ResponseMessage>('/instances/create', {
        method: 'POST',
        json: payload,
    });

/* -------------------------------------------------------------------------- */
/*  Logs and Stats                                                            */
/* -------------------------------------------------------------------------- */

export function openLogs(instance: string): WebSocket {
    return new WebSocket(buildWsUrl(`/instances/${instance}/logs`));
}

export function openStats(instance: string): WebSocket {
    return new WebSocket(buildWsUrl(`/instances/${instance}/stats`));
}