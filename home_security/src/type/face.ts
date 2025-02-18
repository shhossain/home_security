export interface Face {
    id: string;
    name: string;
    liveness: number;
    active: boolean;
    createdAt: string;
    last_seen: string;
    is_unknown: boolean;
}