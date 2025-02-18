import cv2
import atexit


caps: dict[int | str, cv2.VideoCapture] = {}


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
