import torch
import cv2
import numpy as np
from torch.nn.functional import interpolate
from models.helpers import Box


def get_size(img):
    if isinstance(img, (np.ndarray, torch.Tensor)):
        return img.shape[1::-1]
    else:
        return img.size


def imresample(img, sz):
    im_data = interpolate(img, size=sz, mode="area")
    return im_data


def crop_resize(img: np.ndarray, box: Box, image_size):
    if box.right <= box.left or box.bottom <= box.top:
        return None
    try:
        cropped = img[box.top : box.bottom, box.left : box.right]
        if cropped.size == 0:
            return None
        return cv2.resize(
            cropped, (image_size, image_size), interpolation=cv2.INTER_AREA
        ).copy()
    except Exception as e:
        print(f"Error in crop_resize: {e}")
        return None


def extract_face(img: np.ndarray, box: Box, image_size=160, margin=0):
    try:
        raw_image_size = get_size(img)
        margin_x = margin * (box.right - box.left) / (image_size - margin)
        margin_y = margin * (box.bottom - box.top) / (image_size - margin)

        box = Box(
            left=max(0, int(box.left - margin_x / 2)),
            top=max(0, int(box.top - margin_y / 2)),
            right=min(raw_image_size[0], int(box.right + margin_x / 2)),
            bottom=min(raw_image_size[1], int(box.bottom + margin_y / 2)),
        )

        face = crop_resize(img, box, image_size)
        return face
    except Exception as e:
        print(f"Error in extract_face: {e}")
        return None
