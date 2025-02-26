from typing import Dict, Optional, TypedDict
from pydantic import BaseModel
import requests

from models.config import Config

#   p += sprintf(p, "\"xclk\":%u,", s->xclk_freq_hz / 1000000);
#   p += sprintf(p, "\"pixformat\":%u,", s->pixformat);
#   p += sprintf(p, "\"framesize\":%u,", s->status.framesize);
#   p += sprintf(p, "\"quality\":%u,", s->status.quality);
#   p += sprintf(p, "\"brightness\":%d,", s->status.brightness);
#   p += sprintf(p, "\"contrast\":%d,", s->status.contrast);
#   p += sprintf(p, "\"saturation\":%d,", s->status.saturation);
#   p += sprintf(p, "\"sharpness\":%d,", s->status.sharpness);
#   p += sprintf(p, "\"special_effect\":%u,", s->status.special_effect);
#   p += sprintf(p, "\"wb_mode\":%u,", s->status.wb_mode);
#   p += sprintf(p, "\"awb\":%u,", s->status.awb);
#   p += sprintf(p, "\"awb_gain\":%u,", s->status.awb_gain);
#   p += sprintf(p, "\"aec\":%u,", s->status.aec);
#   p += sprintf(p, "\"aec2\":%u,", s->status.aec2);
#   p += sprintf(p, "\"ae_level\":%d,", s->status.ae_level);
#   p += sprintf(p, "\"aec_value\":%u,", s->status.aec_value);
#   p += sprintf(p, "\"agc\":%u,", s->status.agc);
#   p += sprintf(p, "\"agc_gain\":%u,", s->status.agc_gain);
#   p += sprintf(p, "\"gainceiling\":%u,", s->status.gainceiling);
#   p += sprintf(p, "\"bpc\":%u,", s->status.bpc);
#   p += sprintf(p, "\"wpc\":%u,", s->status.wpc);
#   p += sprintf(p, "\"raw_gma\":%u,", s->status.raw_gma);
#   p += sprintf(p, "\"lenc\":%u,", s->status.lenc);
#   p += sprintf(p, "\"hmirror\":%u,", s->status.hmirror);
#   p += sprintf(p, "\"dcw\":%u,", s->status.dcw);
#   p += sprintf(p, "\"colorbar\":%u", s->status.colorbar);
#   p += sprintf(p, ",\"led_intensity\":%u", currentFlashIntensity);
#   p += sprintf(p, ",\"servo_angle\":%u", currentServoAngle);


class ESP32CameraStatusData(BaseModel):
    xclk: int
    pixformat: int
    framesize: int
    quality: int
    brightness: int
    contrast: int
    saturation: int
    sharpness: int
    special_effect: int
    wb_mode: int
    awb: int
    awb_gain: int
    aec: int
    aec2: int
    ae_level: int
    aec_value: int
    agc: int
    agc_gain: int
    gainceiling: int
    bpc: int
    wpc: int
    raw_gma: int
    lenc: int
    hmirror: int
    dcw: int
    colorbar: int
    led_intensity: int
    servo_angle: int


class ESP32CameraStatus:
    def __init__(self, config: Config):
        self.config = config
        data = self.load_status()
        self.data = ESP32CameraStatusData(**data)

    def load_status(self) -> Dict[str, int]:
        for _ in range(3):
            try:
                response = requests.get(f"http://{self.config.esp32_ip}/status")
                if response.ok:
                    return response.json()
            except requests.RequestException as e:
                print(f"Error loading status: {e}")

        raise Exception("Could not load status")
