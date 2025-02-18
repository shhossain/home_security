import cv2
import atexit
import socket
import struct
import numpy as np
from urllib.parse import urlparse

from torch import le

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


# def receive_webcam_stream(host: str, port: int = 9999):
#     """
#     Receives and displays a video stream from a remote webcam server.

#     Args:
#         host (str): The IP address of the server
#         port (int): The port number to connect to (default: 9999)
#     """
#     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     client_socket.connect((host, port))

#     data = b""
#     payload_size = struct.calcsize(">L")

#     try:
#         while True:
#             while len(data) < payload_size:
#                 packet = client_socket.recv(4096)
#                 if not packet:
#                     return
#                 data += packet

#             packed_size = data[:payload_size]
#             data = data[payload_size:]
#             frame_size = struct.unpack(">L", packed_size)[0]

#             while len(data) < frame_size:
#                 data += client_socket.recv(4096)

#             frame_data = data[:frame_size]
#             data = data[frame_size:]

#             frame = cv2.imdecode(
#                 np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR
#             )
#             if frame is None:
#                 continue

#             cv2.imshow("Received Stream", frame)
#             if cv2.waitKey(1) == 27:  # Press ESC to exit
#                 break
#     except Exception as e:
#         print("Client stopped:", e)
#     finally:
#         client_socket.close()
#         cv2.destroyAllWindows()


def receive_webcan_stream(url: str):
    p = urlparse(url)
    host = p.hostname
    port = p.port

    if url not in sc:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        sc[url] = client_socket
        atexit.register(lambda: client_socket.close())
    else:
        client_socket = sc[url]

    data = b""
    payload_size = struct.calcsize(">L")

    try:
        while len(data) < payload_size:
            packet = client_socket.recv(4096)
            if not packet:
                return
            data += packet

        packed_size = data[:payload_size]
        data = data[payload_size:]
        frame_size = struct.unpack(">L", packed_size)[0]

        while len(data) < frame_size:
            data += client_socket.recv(4096)

        frame_data = data[:frame_size]
        data = data[frame_size:]

        frame = cv2.imdecode(
            np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR
        )

        return frame
    except Exception as e:
        return None
