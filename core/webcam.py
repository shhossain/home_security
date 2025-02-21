import cv2
import atexit
import socket
import struct
import numpy as np
from urllib.parse import urlparse
import threading
import time
import pickle


caps: dict[int | str, cv2.VideoCapture] = {}
current_frame: dict[str, np.ndarray] = {}
lock = threading.Lock()


def get_webcam_feed(index: str | int = 0):
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


def _remote_webcam(url: str):
    p = urlparse(url)
    host_ip = p.hostname
    port = p.port

    client_socket = None
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Add connection timeout
            client_socket.settimeout(5)
            client_socket.connect((host_ip, port))
            # Reset timeout for receiving data
            client_socket.settimeout(None)
            print(f"Connected to {host_ip}:{port}")

            data = b""
            payload_size = struct.calcsize("Q")

            while True:
                try:
                    while len(data) < payload_size:
                        packet = client_socket.recv(4 * 1024)
                        if not packet:
                            raise ConnectionError("Server disconnected")
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

                except socket.timeout:
                    print("Connection timed out")
                    break
                except Exception as e:
                    print(f"Error receiving data: {e}")
                    break

        except socket.timeout:
            print("Connection attempt timed out. Retrying in 1 second...")
        except ConnectionRefusedError:
            print("Connection refused. Retrying in 1 second...")
        except Exception as e:
            print(f"Connection error: {e}. Retrying in 1 second...")
        finally:
            if client_socket is not None:
                client_socket.close()
                time.sleep(1)


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


def get_remote_webcam_feed(url: str):
    with lock:
        if url in current_frame:
            return current_frame[url]
        else:
            if not ping(url):
                raise Exception("Cannot connect to remote webcam")

            threading.Thread(target=_remote_webcam, args=(url,)).start()
            return None
