from multiprocessing import Value
import threading
from typing import Optional
import requests
from enum import Enum
import time
import socket
from models.config import settings
from models.status import ESP32CameraStatus


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


# ESP32_IP = "192.168.0.52"
# VIDEO_URL = f"http://{ESP32_IP}:81/stream"
# CONTROL_URL = f"http://{ESP32_IP}/control"
# BUZZER_URL = f"http://{ESP32_IP}/buzzer"
# SERVO_URL = f"http://{ESP32_IP}/servo"
# STATUS_URL = f"http://{ESP32_IP}/status"


def get_video_url(ip):
    return f"http://{ip}:81/stream"


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
    if verify_esp32_connection(settings.esp32_ip):
        print(f"[1] Found esp32 camera at {settings.esp32_ip}")
        return settings.esp32_ip

    ip = find_esp32_ip()
    if ip:
        settings.set("esp32_ip", ip)
        set_framesize(ScreenResolution.SXGA_1280_1024)
        print(f"[+] Found esp32 camera at {ip}")
        return ip

    return None


def buzzer(state, duration: float = 1):
    try:
        requests.get(
            f"http://{settings.esp32_ip}/buzzer?state={1 if state else 0}&duration={duration}",
            timeout=1,
        )
    except requests.RequestException as e:
        print(f"Error controlling buzzer: {e}")


def control_buzzer(state, duration: float = 1):
    threading.Thread(target=buzzer, args=(state, duration), daemon=True).start()


def set_control(var, val, blocking: bool = False):
    def _set_control(var, val):
        try:
            response = requests.get(
                f"http://{settings.esp32_ip}/control?var={var}&val={val}", timeout=1
            )
            return response.ok
        except requests.RequestException as e:
            print(f"Error controlling flash: {e}")
            time.sleep(0.1)

    if blocking:
        return _set_control(var, val)
    else:
        threading.Thread(target=_set_control, args=(var, val), daemon=True).start()


check_frunning = Value("b", False)


def check_and_set_framesize():
    if check_frunning.value:
        return

    try:
        status = ESP32CameraStatus(settings)
        if status.data.framesize != ScreenResolution.SXGA_1280_1024.value:
            set_framesize(ScreenResolution.SXGA_1280_1024)
            print("Framesize changed to SXGA_1280_1024")
    except Exception as e:
        print(f"Error checking framesize: {e}")
    finally:
        check_frunning.value = False


def set_flash(intensity, **kw):
    return set_control("led_intensity", intensity, **kw)


def set_framesize(size: ScreenResolution, **kw):
    return set_control("framesize", size.value, **kw)


def set_servo_angle(angle, **kw):
    return set_control("servo_angle", angle, **kw)


def open_door():
    print("Opening door")
    set_servo_angle(90)  # Open door


def close_door():
    print("Closing door")
    set_servo_angle(0)  # Close door


def open_and_close_door():
    open_door()
    time.sleep(settings.door_open_for)
    close_door()


if __name__ == "__main__":
    # open_and_close_door()
    while 1:
        i = int(input("Enter angle: "))
        set_servo_angle(i)
