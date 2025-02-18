from typing import List, Tuple
import mediapipe as mp
import numpy as np
from utils.face_detection_helpers import extract_face
from models.helpers import Box


class FaceDetection:
    def __init__(self, max_num_faces: int = 1):
        self.detector = mp.solutions.face_mesh.FaceMesh(  # type: ignore
            max_num_faces=max_num_faces, static_image_mode=True
        )

    def __call__(self, image: np.ndarray) -> Tuple[List[np.ndarray], List[Box]]:
        h, w = image.shape[:2]
        predictions = self.detector.process(image)
        boxes: list[Box] = []
        faces = []
        if predictions.multi_face_landmarks:
            for prediction in predictions.multi_face_landmarks:
                pts = np.array(
                    [(pt.x * w, pt.y * h) for pt in prediction.landmark],
                    dtype=np.float64,
                )
                bbox = np.vstack([pts.min(axis=0), pts.max(axis=0)])
                bbox = np.round(bbox).astype(np.int32)
                
                # Ensure coordinates are within image bounds
                bbox[0][0] = max(0, bbox[0][0])  # left
                bbox[0][1] = max(0, bbox[0][1])  # top
                bbox[1][0] = min(w, bbox[1][0])  # right
                bbox[1][1] = min(h, bbox[1][1])  # bottom
                
                box = Box(
                    top=bbox[0][1],
                    right=bbox[1][0],
                    bottom=bbox[1][1],
                    left=bbox[0][0],
                )
                
                # Only process if we have a valid box size
                if box.right > box.left and box.bottom > box.top:
                    face_arr = extract_face(image, box)
                    if face_arr is not None and face_arr.size > 0:
                        boxes.append(box)
                        faces.append(face_arr)
                        
        return faces, boxes
