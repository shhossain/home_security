from multiprocessing import Value
import pickle
import time
import face_recognition
import threading
from queue import Queue, Empty
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
# Replace the Queue() initialization with a size limit
q = Queue(maxsize=5)  # Increased queue size slightly
recognition_timeout = 2.0  # seconds
last_open_door = Value("d", 0)


def _start_recognizing(*, frame: np.ndarray, face: Face, tolerance: float):
    try:
        # Add timeout for face encoding
        start_time = time.time()
        face_encodings = face_recognition.face_encodings(
            frame, [(face.bbox.top, face.bbox.right, face.bbox.bottom, face.bbox.left)]
        )

        if time.time() - start_time > recognition_timeout:
            print("Face recognition timeout")
            return

        if not face_encodings:
            return

        # Process known faces
        face_encoding = face_encodings[0]
        matches = []

        with lock:  # Use lock only for the comparison
            matches = face_recognition.compare_faces(
                known_face_encodings,
                face_encoding,
                tolerance=tolerance,
            )

        if True in matches:
            name = known_face_names[matches.index(True)]
            f = db.face.find_unique(where={"name": name})
            if f:
                print(f"Recognized face: {name}")
                face.update_from_db(f)
                face.is_unknown = False

                if (
                    should_open_door(face, settings.liveness_threshold)
                    and time.time() - last_open_door.value > settings.door_open_delay
                ):
                    last_open_door.value = time.time()
                    threading.Thread(target=open_and_close_door, daemon=True).start()
        else:
            # Process unknown faces similar to before but with timeout check
            if time.time() - start_time > recognition_timeout:
                return

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

    except Exception as e:
        print(f"Recognition error: {e}")
    finally:
        face.is_loaded = True


# def recognize_faces():
#     print("Starting face recognition")
#     while should_run_thread.value:
#         try:
#             kw = q.get(timeout=0.5)
#             _start_recognizing(**kw)
#             q.task_done()
#         except Empty:
#             # Queue is empty, just continue waiting
#             time.sleep(0.1)  # Sleep a bit to prevent CPU thrashing
#             continue
#         except Exception as e:
#             print(f"Error in recognition loop: {e}")
#             time.sleep(0.1)  # Sleep on error to prevent rapid retries
#             continue

#         time.sleep(0.01)  # Small sleep to prevent CPU overload


is_recognizing = Value("b", False)


def recognize_faces():
    if is_recognizing.value:
        return

    while not q.empty():
        is_recognizing.value = True
        try:
            kw = q.get(timeout=0.5)
            _start_recognizing(**kw)
            q.task_done()
        except Empty:
            # Queue is empty, just continue waiting
            time.sleep(0.1)
            continue

    is_recognizing.value = False


def start_recognizing(*, frame: np.ndarray, face: Face, tolerance: float = 0.7):
    print("Queueing recognition")
    try:
        # Use put_nowait to prevent blocking
        if not q.full():
            q.put_nowait({"frame": frame, "face": face, "tolerance": tolerance})
            threading.Thread(target=recognize_faces).start()
        else:
            print("Recognition queue full, skipping face...")
    except Exception as e:
        print(f"Error queueing recognition: {e}")
