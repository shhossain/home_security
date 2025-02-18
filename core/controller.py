import threading
import requests
from enum import Enum


class ScreenResolution(Enum):
    UXGA_1600_1200 = 15
    SXGA_1280_1024 = 14
    HD = 13
    XGA_1024_768 = 12
    SVGA_800_600 = 11
    VGA_640_480 = 10
    HVGA_480_320 = 9
    CIF_400_296 = 8
    QVGA_320_240 = 6
    S_240_240 = 5
    HQVGA_240_176 = 4
    QCIF_176_144 = 3
    S_128_128 = 2
    QQVGA_160_120 = 1
    S_96_96 = 0


ESP32_IP = "192.168.0.61"
VIDEO_URL = f"http://{ESP32_IP}:81/stream"
CONTROL_URL = f"http://{ESP32_IP}/control"
BUZZER_URL = f"http://{ESP32_IP}/buzzer"


def change_esp32_ip(ip):
    global ESP32_IP
    ESP32_IP = ip


def buzzer(state, duration: float = 1):
    try:
        requests.get(f"{BUZZER_URL}?state={1 if state else 0}&duration={duration}")
    except requests.RequestException as e:
        print(f"Error controlling buzzer: {e}")


def control_buzzer(state, duration: float = 1):
    threading.Thread(target=buzzer, args=(state, duration), daemon=True).start()


def set_flash(intensity):
    return set_control("led_intensity", intensity)


def set_control(var, val):
    for _ in range(3):
        try:
            params = {"var": var, "val": val}
            response = requests.get(CONTROL_URL, params=params)
            return response.ok
        except requests.RequestException as e:
            print(f"Error controlling flash: {e}")
            return False


def set_framesize(size: ScreenResolution):
    return set_control("framesize", size.value)
