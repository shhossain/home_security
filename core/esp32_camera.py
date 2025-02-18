import cv2
import numpy as np
import requests

session = requests.Session()


def get_video_feed(url):
    try:
        response = session.get(url, stream=True)
        if not response.ok:
            print(f"Bad response: {response.status_code}")
            return None

        bytes_array = bytearray(b"")
        for chunk in response.iter_content(chunk_size=1024):
            bytes_array.extend(chunk)

            # Find the beginning and end of JPEG
            jpg_start = bytes_array.find(b"\xff\xd8")
            jpg_end = bytes_array.find(b"\xff\xd9")

            if jpg_start != -1 and jpg_end != -1:
                # Extract the JPEG image
                jpg_bytes = bytes_array[jpg_start : jpg_end + 2]
                # Clear the buffer
                bytes_array = bytes_array[jpg_end + 2 :]

                # Decode the image
                try:
                    frame = cv2.imdecode(
                        np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
                    )
                    return frame
                except Exception as e:
                    print(f"Error decoding frame: {e}")

    except Exception as e:
        print(f"Error in get_video_feed: {e}")
    return None
