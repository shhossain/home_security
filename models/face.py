import json
from typing import Optional, Sequence
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from models.helpers import Box
from prisma import Prisma
from prisma.models import Face as FaceModel
from prisma.types import FaceUpdateInput
import atexit

db = Prisma()
db.connect()

atexit.register(db.disconnect)


class Face(BaseModel):
    bbox: Box

    id: str = str(uuid4())
    name: str = "Unknown"
    created_at: datetime = datetime.now()
    liveness: float = 0.0
    active: bool = True

    face_image_path: Optional[str] = None
    face_embeddings_path: Optional[str] = None
    is_unknown: bool = True
    last_seen: datetime = datetime.now()
    last_data_update: datetime = datetime.now()
    is_loaded: bool = False

    state: dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.name == "Unknown":
            self.name = f"Unknown_{self.id.split('-')[0]}"

    def create(self):
        if self.face_image_path is None or self.face_embeddings_path is None:
            raise ValueError("Face image path and embeddings path must be provided")

        print(f"Creating face {self.name}")
        db.face.create(
            data={
                "id": self.id,
                "name": self.name,
                "liveness": self.liveness,
                "bbox": json.dumps(self.bbox.model_dump()),
                "face_image_path": self.face_image_path,
                "face_embeddings_path": self.face_embeddings_path,
                "is_unknown": self.is_unknown,
                "last_seen": self.last_seen,
            }
        )

    def live_update(self, other: "Face", update_face: bool = False):
        self.bbox = other.bbox
        self.liveness = other.liveness
        self.active = other.active
        self.last_seen = datetime.now()

        time_diff = (datetime.now() - self.last_data_update).total_seconds()
        if not time_diff < 5:
            return
        self.last_data_update = datetime.now()

        # First check if face exists in database
        existing_face = db.face.find_unique(where={"name": self.name})
        if existing_face is None:
            return

        data: FaceUpdateInput = {
            "bbox": json.dumps(self.bbox.model_dump()),
            "liveness": self.liveness,
            "active": self.active,
            "last_seen": self.last_seen,
        }

        if update_face:
            pass  # TODO: Update face image path and embeddings path

        db.face.update(where={"name": self.name}, data=data)

        # Create log entry with confirmed face ID
        db.log.create(
            data={
                "faceId": existing_face.id,
                "liveness": self.liveness,
            }
        )

    def update_from_db(self, other: FaceModel):
        self.name = other.name
        self.face_image_path = other.face_image_path
        self.face_embeddings_path = other.face_embeddings_path

    def scale_copy(self, factor: float) -> "Face":
        face = self.model_copy()
        face.bbox = self.bbox.scale_copy(factor)
        return face

    def most_similar(self, others: Sequence["Face"]):
        max_match = 0
        most_similar = None
        for other in others:
            match = self.bbox.match_percentage(other.bbox)
            if match > max_match:
                max_match = match
                most_similar = other

        return (most_similar, max_match)
