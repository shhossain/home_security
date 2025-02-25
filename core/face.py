from multiprocessing import Value
import pickle
import time
import face_recognition
import threading
from queue import Queue
import numpy as np
from core.controller import open_and_close_door
from models.config import settings
from models.face import Face, db
from models.helpers import Box
from utils.constants import em_path, img_folder, should_run_thread
import cv2
from typing import Optional
from utils.face_detection_helpers import extract_face
from utils.helpers import should_open_door


known_face_encodings = []
known_face_names = []

unknown_face_encodings = []
unknown_face_names = []


def save_face(img_path: str, name: str, bbox: Optional[Box] = None):
    f = db.face.find_unique(where={"name": name})
    if f:
        raise ValueError(f"Face with name {name} already exists")

    print(f"Saving face {name}")
    # image = face_recognition.load_image_file(img_path)
    image = cv2.imread(img_path)
    if bbox:
        face_img = extract_face(image, bbox, margin=1)
        if face_img is None:
            raise ValueError("Invalid face bounding box")
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        embedding = face_recognition.face_encodings(face_img)[0]
        image = face_img
    else:
        embedding = face_recognition.face_encodings(image)[0]
        bbox = Box(left=0, top=0, right=image.shape[1], bottom=image.shape[0])

    # Save face image
    image_path = img_folder / f"{name}.jpg"
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(image_path), image)

    # Save embedding
    epath = em_path / f"{name}.pkl"
    with open(epath, "wb") as f:
        pickle.dump(embedding, f)

    face = Face(
        name=name,
        bbox=bbox,
        face_image_path=str(image_path),
        face_embeddings_path=str(epath),
        is_unknown=False,
    )
    face.active = False
    face.create()

    known_face_encodings.append(embedding)
    known_face_names.append(name)

    return face


def load_faces():
    while should_run_thread.value:
        total = db.face.count()
        if total == len(known_face_names) + len(unknown_face_names):
            time.sleep(1)
            continue

        known_face_encodings.clear()
        known_face_names.clear()
        faces = db.face.find_many(where={"is_unknown": False})
        for face in faces:
            path = face.face_embeddings_path
            with open(path, "rb") as f:
                embedding = pickle.load(f)

            known_face_encodings.append(embedding)
            known_face_names.append(face.name)

        unknown_face_encodings.clear()
        unknown_face_names.clear()
        faces = db.face.find_many(where={"is_unknown": True})
        for face in faces:
            path = face.face_embeddings_path
            with open(path, "rb") as f:
                embedding = pickle.load(f)

            unknown_face_encodings.append(embedding)
            unknown_face_names.append(face.name)

        time.sleep(1)


lock = threading.Lock()
q = Queue()
last_open_door = Value("d", 0)


def _start_recognizing(*, frame: np.ndarray, face: Face, tolerance: float):
    box = face.bbox
    face_encodings = face_recognition.face_encodings(
        frame, [(box.top, box.right, box.bottom, box.left)]
    )
    if face_encodings:
        matches = face_recognition.compare_faces(
            known_face_encodings,
            face_encodings[0],
            tolerance=tolerance,
        )
        if True in matches:
            name = known_face_names[matches.index(True)]
            f = db.face.find_unique(where={"name": name})
            if f:
                face.update_from_db(f)

                if (
                    should_open_door(
                        face,
                        settings.liveness_threshold,
                    )
                    and time.time() - last_open_door.value > settings.door_open_delay
                ):
                    last_open_door.value = time.time()
                    open_and_close_door()

        else:
            matches = face_recognition.compare_faces(
                unknown_face_encodings,
                face_encodings[0],
                tolerance=tolerance,
            )
            if True in matches:
                name = unknown_face_names[matches.index(True)]
                f = db.face.find_unique(where={"name": name})
                if f:
                    face.is_unknown = False
                    face.update_from_db(f)

            else:
                if face.liveness < 0.5:
                    return

                epath = str(em_path / str(face.name + ".pkl"))
                with open(epath, "wb") as f:
                    pickle.dump(face_encodings[0], f)

                face.face_embeddings_path = epath
                face.is_unknown = True
                face.create()

                unknown_face_encodings.append(face_encodings[0])
                unknown_face_names.append(face.name)

    face.is_loaded = True


def recognize_faces():
    print("Starting face recognition")
    while should_run_thread.value:
        kw = q.get()
        _start_recognizing(**kw)
        q.task_done()
        time.sleep(0.1)


def start_recognizing(*, frame: np.ndarray, face: Face, tolerance: float = 0.7):
    q.put({"frame": frame, "face": face, "tolerance": tolerance})
