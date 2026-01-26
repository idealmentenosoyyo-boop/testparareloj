import { Timestamp } from "firebase/firestore";

export interface DeviceData {
    id: string; // The document ID (device_id)
    online: boolean;
    last_seen: Timestamp;
    updated_at: string;

    // Position
    last_lat?: number;
    last_lng?: number;
    last_gps_timestamp?: Timestamp;

    // State
    last_battery?: number;
    steps_today?: number;

    // Health
    last_hr?: number;
    last_spo2?: number;
    last_bp?: string; // "sys/dia"
    last_bp_sys?: number; // Sistólica
    last_bp_dia?: number; // Diastólica
}

export interface DeviceEvent {
    id: string;
    event_type: string;
    type?: string;
    timestamp: Timestamp;

    // Position
    lat?: number;
    lng?: number;
    speed?: number;
    course?: number;
    sat?: number;
    valid?: boolean;

    // Health / Heartbeat
    bat?: number;
    hr?: number;
    spo2?: number;
    bp_sys?: number;
    bp_dia?: number;
    steps?: number;
    tumbles?: number;
    source?: string;
}
