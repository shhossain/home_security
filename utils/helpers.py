import base64
import cv2
import numpy as np

from models.face import Face


def calculate_darkness_percentage(frame: np.ndarray, threshold: int = 50) -> float:
    """
    Calculate the darkness percentage of a frame.
    The frame is considered dark if the pixel intensity is less than the threshold.

    Args:
        frame (np.ndarray): The frame to calculate the darkness percentage.
        threshold (int): The threshold to consider a pixel as dark. Lower is darker. Default is 50.

    Returns:
        float: The darkness percentage of the frame. 0-100.
    """

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

    dark_pixels = np.sum(gray < threshold)

    # Calculate percentage (0-100)
    total_pixels = frame.shape[0] * frame.shape[1]
    darkness_percentage = (dark_pixels / total_pixels) * 100

    return float(darkness_percentage)


def calculate_flash_intensity(
    darkness_percentage: float, threshold: int = 50, max_flash_intensity: int = 100
) -> int:
    """
    Calculate the flash intensity based on the darkness percentage.

    Args:
        darkness_percentage (float): The darkness percentage of the frame. 0-100.
        threshold (int): Consider the frame dark if the darkness percentage is more than this. Default is 50.
        max_flash_intensity (int): The maximum intensity of the flash. Default is 100.

    Returns:
        int: The intensity of the flash. 0-100.
    """

    # flash is 0 to 255
    # turn on flash if darkness is more than 50%

    if darkness_percentage > threshold:
        val = int(
            (darkness_percentage - 50) * (max_flash_intensity / (100 - threshold))
        )
        return min(val, max_flash_intensity)

    return 0


def image_to_base64(image: np.ndarray) -> str:
    """
    Convert an image to base64 string.

    Args:
        image (np.ndarray): The image to convert.

    Returns:
        str: The base64 string of the image.
    """

    _, buffer = cv2.imencode(".jpg", image)
    return base64.b64encode(buffer).decode()


def base64_to_image(base64_string: str) -> np.ndarray:
    """
    Convert a base64 string to an image.

    Args:
        base64_string (str): The base64 string to convert.

    Returns:
        np.ndarray: The image from the base64 string.
    """

    if base64_string.startswith("data:"):
        base64_string = base64_string.split(",")[1]

    buffer = base64.b64decode(base64_string)
    arr = np.frombuffer(buffer, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def should_open_door(face: Face, liveness_threshold: float = 0.8) -> bool:
    """
    Check if the door should be opened based on the face liveness.

    Args:
        face (Face): The face to check the liveness.
        liveness_threshold (float): The threshold to consider the face as real. Default is 0.8.
        near_threshold (float): The threshold to consider the face in front of the camera. Default is 80.
    """
    if face.check_unknown():
        return False

    return face.liveness >= liveness_threshold


def is_less_than_eq(a: float, b: float) -> bool:
    """
    Reference is b
    """
    bv = len(str(b).split(".")[-1])
    a = round(a, bv)
    return a <= b
