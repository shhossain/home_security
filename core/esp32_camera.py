import cv2
import numpy as np
import requests

session = requests.Session()
session.headers.update({"Connection": "keep-alive"})

# def get_video_feed(url):
#     try:
#         response = session.get(url, stream=True)
#         if not response.ok:
#             print(f"Bad response: {response.status_code}")
#             return None

#         bytes_array = bytearray(b"")
#         for chunk in response.iter_content(chunk_size=8192):  # Increased chunk size
#             bytes_array.extend(chunk)

#             # Find the beginning and end of JPEG
#             a = bytes_array.find(b"\xff\xd8")
#             b = bytes_array.find(b"\xff\xd9")

#             if a != -1 and b != -1:
#                 jpg = bytes_array[a : b + 2]
#                 bytes_array = bytes_array[b + 2 :]

#                 try:
#                     # Use IMREAD_REDUCED_COLOR_2 for faster decoding
#                     frame = cv2.imdecode(
#                         np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_REDUCED_COLOR_2
#                     )
#                     return frame
#                 except Exception as e:
#                     print(f"Error decoding frame: {e}")
#                     continue

#     except Exception as e:
#         print(f"Error in get_video_feed: {e}")
#     return None


def get_video_feed(url):
    response = session.get(url, stream=True)
    if not response.ok:
        print(f"Bad response: {response.status_code}")
        return None

    bytes_array = bytearray(b"")
    for chunk in response.iter_content(chunk_size=1024):  # Increased chunk size
        bytes_array.extend(chunk)

        # Find the beginning and end of JPEG
        a = bytes_array.find(b"\xff\xd8")
        b = bytes_array.find(b"\xff\xd9")

        if a != -1 and b != -1:
            jpg = bytes_array[a : b + 2]
            bytes_array = bytes_array[b + 2 :]

            try:
                # Use IMREAD_REDUCED_COLOR_2 for faster decoding
                frame = cv2.imdecode(
                    np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_REDUCED_COLOR_2
                )
                return frame
            except Exception as e:
                print(f"Error decoding frame: {e}")
                continue
