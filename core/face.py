from pathlib import Path
import pickle
import time
import face_recognition
import threading
from queue import Queue
import numpy as np
from models.face import Face, db
from models.helpers import Box
from utils.constants import em_path, img_folder
import shutil


known_face_encodings = []
known_face_names = []

unknown_face_encodings = []
unknown_face_names = []


def save_face(img_path: str, name: str):
    f = db.face.find_unique(where={"name": name})
    if f:
        print(f"Face with name {name} already exists")
        return

    print(f"Saving face {name}")
    # copy image file
    image_path = img_folder / str(name + ".jpg")
    shutil.copyfile(img_path, image_path)

    image = face_recognition.load_image_file(image_path)
    embedding = face_recognition.face_encodings(image)[0]
    epath = str(em_path / str(name + ".pkl"))
    with open(epath, "wb") as f:
        pickle.dump(embedding, f)

    box = Box(left=0, top=0, right=0, bottom=0)
    face = Face(
        name=name,
        bbox=box,
        face_image_path=image_path,
        face_embeddings_path=epath,
        is_unknown=False,
    )
    face.active = False
    face.create()
    known_face_encodings.append(embedding)
    known_face_names.append(name)

    return face


def load_faces():
    while True:
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


def _start_recognizing(*, frame: np.ndarray, face: Face, tolerance: float = 0.7):
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

        else:
            matches = face_recognition.compare_faces(
                unknown_face_encodings,
                face_encodings[0],
                tolerance=tolerance + 0.1,
            )
            if True in matches:
                name = unknown_face_names[matches.index(True)]
                f = db.face.find_unique(where={"name": name})
                if f:
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
    while True:
        kw = q.get()
        _start_recognizing(**kw)
        q.task_done()
        time.sleep(0.1)


def start_recognizing(*, frame: np.ndarray, face: Face, tolerance: float = 0.7):
    q.put({"frame": frame, "face": face, "tolerance": tolerance})


def initialize_face_recognition():
    save_face(r"C:\Users\sifat\Downloads\sifat.jpg", "Sifat")
    threading.Thread(target=recognize_faces, daemon=True).start()
    threading.Thread(target=load_faces, daemon=True).start()


# initialize_face_recognition()
