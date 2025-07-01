export interface HealthResponse {
    status: "ok" | string;
}

export type InstanceStatus = 'running' | 'stopped' | 'error';

export interface InstanceInfo {
    name: string;
    status: InstanceStatus;
}

export interface EnvVar {
    key: string;
    value: string;
}

export interface PortBinding {
    host_port: number;
    container_port: number;
    type: 'tcp' | 'udp';
}

/** Body for POST /instances/create  (matches FastAPI’s InstanceCreate) */
export interface InstanceCompose {
    name: string;
    image: string;
    eula: boolean;
    memory: string;             // e.g. "4G"
    env: EnvVar[];
    ports: PortBinding[];
}

/** Body for PUT /instances/{name}/compose */
export interface InstanceUpdate {
    eula: boolean;
    memory: string;
    env: EnvVar[];
    ports: PortBinding[];
}

export interface ResponseMessage {
    message: string;
}

export interface CronSchedule {
  /** crontab string, e.g. "0 3 * * *"  */
  cron: string;
}

export interface ScheduledJob {
  id: string;
  /** The cron spec or human-readable trigger string */
  schedule: string;
  /** ISO timestamp of next run, or null */
  next_run: string | null;
}

export interface TokenResponse {
    token: string;
    user: string;
}