import cv2
import numpy as np


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
            (darkness_percentage - threshold)
            * (max_flash_intensity / (100 - threshold))
        )
        return min(val, max_flash_intensity)

    return 0
