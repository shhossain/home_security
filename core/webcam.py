import cv2
import atexit
import socket
import struct
import numpy as np
from urllib.parse import urlparse
import threading
import time
import pickle


caps: dict[int, cv2.VideoCapture] = {}
sc: dict[str, socket.socket] = {}


def get_webcam_feed(index=0):
    if index not in caps:
        caps[index] = cv2.VideoCapture(index)
        atexit.register(lambda: caps[index].release())
    cap = caps[index]

    if not cap.isOpened():
        print(f"Error opening webcam {index}")
        return None

    ret, frame = cap.read()
    if not ret:
        print(f"Error reading frame from webcam {index}")
        return None

    return frame


sc: dict[str, socket.socket] = {}
current_frame: dict[str, np.ndarray] = {}

lock = threading.Lock()


def _remote_webcam(url: str):
    p = urlparse(url)
    host_ip = p.hostname
    port = p.port

    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host_ip, port))
            print(f"Connected to {host_ip}:{port}")

            data = b""
            payload_size = struct.calcsize("Q")

            while True:
                while len(data) < payload_size:
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]

                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)

                lock.acquire()
                current_frame[url] = frame
                lock.release()

        except ConnectionRefusedError:
            print("Connection refused. Retrying in 1 seconds...")
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}. Retrying in 1 seconds...")
            time.sleep(1)
        finally:
            client_socket.close()


def ping(url: str):
    p = urlparse(url)
    host_ip = p.hostname
    port = p.port
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host_ip, port))
        client_socket.close()
        return True
    except Exception as e:
        client_socket.close()
        return False


def remote_webcam(url: str):
    with lock:
        if url in current_frame:
            return current_frame[url]
        else:
            if not ping(url):
                raise Exception("Cannot connect to remote webcam")

            threading.Thread(target=_remote_webcam, args=(url,)).start()
            return None


if __name__ == "__main__":
    server_url = "http://localhost:9999"  # Change this to your server's IP
    print(f"Attempting to connect to {server_url}")

    while True:
        try:
            frame = remote_webcam(server_url)
            if frame is not None:
                cv2.imshow("RECEIVING VIDEO", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(1)

    cv2.destroyAllWindows()
