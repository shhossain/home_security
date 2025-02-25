export interface Config {
  esp32_ip: string;
  liveness_threshold: number;
  door_open_delay: number;
  darkness_threshold: number;
  max_flash_intensity: number;
  face_detection: {
    max_faces: number;
    face_matching_threshold: number;
  }
}

export interface ESP32Status {
  ip: string;
  flash_intensity: number;
  servo_angle: number;
  video_url: string;
}

export interface ESP32Command {
  type: 'flash' | 'servo' | 'door';
  value: number | boolean;
}
