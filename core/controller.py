import json
import threading
from typing import Optional
import requests
from enum import Enum
import time
from utils.constants import app_path
import socket


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


ESP32_IP = "192.168.0.52"
config_path = app_path / "config.json"
if config_path.exists():
    with open(config_path, "r") as f:
        config = json.load(f)
        ESP32_IP = config.get("esp32_ip", ESP32_IP)

VIDEO_URL = f"http://{ESP32_IP}:81/stream"
CONTROL_URL = f"http://{ESP32_IP}/control"
BUZZER_URL = f"http://{ESP32_IP}/buzzer"
SERVO_URL = f"http://{ESP32_IP}/servo"
STATUS_URL = f"http://{ESP32_IP}/status"


def change_esp32_ip(ip):
    global ESP32_IP, VIDEO_URL, CONTROL_URL, BUZZER_URL, SERVO_URL, STATUS_URL
    ESP32_IP = ip
    with open(config_path, "w") as f:
        json.dump({"esp32_ip": ip}, f)

    VIDEO_URL = f"http://{ESP32_IP}:81/stream"
    CONTROL_URL = f"http://{ESP32_IP}/control"
    BUZZER_URL = f"http://{ESP32_IP}/buzzer"
    SERVO_URL = f"http://{ESP32_IP}/servo"
    STATUS_URL = f"http://{ESP32_IP}/status"


def verify_esp32_connection(ip):
    for _ in range(3):
        try:
            print(f"[GET] http://{ip}/status", end="\r")
            response = requests.get(f"http://{ip}/status", timeout=1)
            return response.ok
        except requests.RequestException:
            pass

    return False


def find_esp32_ip() -> Optional[str]:
    device_ip = socket.gethostbyname(socket.gethostname())
    ip_parts = device_ip.split(".")
    ip_parts[-1] = "1"
    gateway_ip = ".".join(ip_parts)

    def check_ip(ip, result):
        if verify_esp32_connection(ip):
            result.append(ip)

    threads = []
    result = []

    for i in range(1, 255):
        ip = f"{gateway_ip[:-1]}{i}"
        thread = threading.Thread(target=check_ip, args=(ip, result))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    return result[0] if result else None


def find_and_change_esp32_ip():
    # first check current ip
    if verify_esp32_connection(ESP32_IP):
        print(f"[1] Found esp32 camera at {ESP32_IP}")
        return ESP32_IP

    ip = find_esp32_ip()
    if ip:
        change_esp32_ip(ip)
        print(f"[+] Found esp32 camera at {ip}")
        return ip

    return None


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


def set_servo_angle(angle):
    try:
        requests.get(f"{SERVO_URL}?angle={angle}")
    except requests.RequestException as e:
        print(f"Error controlling servo: {e}")


def open_door():
    set_servo_angle(90)  # Open door


def close_door():
    set_servo_angle(0)  # Close door


def open_and_close_door():
    open_door()
    time.sleep(2)
    close_door()


if __name__ == "__main__":
    # open_and_close_door()
    while 1:
        i = int(input("Enter angle: "))
        set_servo_angle(i)
