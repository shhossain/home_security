import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import FileResponse
from prisma import Prisma
from prisma.types import FaceWhereInput
from pydantic import BaseModel
from core.face import initialize_face_recognition, save_face
from utils.constants import current_frame_path
from models.face import db
from fastapi.middleware.cors import CORSMiddleware
import datetime as dt
from cam import process_video_feed
import threading
import shutil
import tempfile
import time

db = Prisma()


# app lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    print("Connected to database")
    threading.Thread(target=process_video_feed).start()
    initialize_face_recognition()
    yield
    db.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChangeNameRequest(BaseModel):
    name: str


@app.post("/api/faces/{face_id}/rename")
async def rename_face(face_id: str, req: ChangeNameRequest):
    face = db.face.update(
        where={"id": face_id}, data={"name": req.name, "is_unknown": False}
    )
    return face


@app.post("/api/faces/{face_id}/delete")
async def delete_face(face_id: str):
    db.face.delete(where={"id": face_id})
    return {"message": "Face deleted"}


@app.get("/api/faces")
def get_faces(active: Optional[bool] = None):
    where: FaceWhereInput = {}
    if active is not None:
        where["active"] = active

    faces = db.face.find_many(where=where)
    time = dt.datetime.now(dt.UTC) - dt.timedelta(minutes=60)

    total_known = db.face.count(where={"is_unknown": False})
    total_unknown = db.face.count(where={"is_unknown": True})
    recent_attempts = 0

    for face in faces:
        if face.last_seen > time:
            recent_attempts += 1

        if not face.active:
            continue

        last_log = db.log.find_first(
            where={"faceId": face.id},
            order={"timestamp": "desc"},
        )
        if last_log:
            time_diff = (dt.datetime.now(dt.UTC) - last_log.timestamp).total_seconds()
            face.active = time_diff < 10
            db.face.update(where={"id": face.id}, data={"active": face.active})

    return {
        "faces": faces,
        "stats": {
            "total_known": total_known,
            "total_unknown": total_unknown,
            "recent_attempts": recent_attempts,
        },
    }


@app.get("/api/faces/{face_id}")
def get_face(face_id: str):
    face = db.face.find_unique(where={"id": face_id})
    return face


@app.get("/api/faces/image/{face_id}")
def get_face_image(face_id: str):
    face = db.face.find_unique(where={"id": face_id})
    if not face:
        return {"error": "Face not found"}

    if not face.face_image_path:
        return {"error": "Face image not found"}

    return FileResponse(face.face_image_path)


@app.post("/api/faces/upload")
async def upload_face(name: str, file: UploadFile = File(...)):
    # Save uploaded file to temp location
    temp_path = tempfile.mktemp(suffix=".jpg")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save face using existing function
    face = save_face(temp_path, name)

    # Cleanup temp file
    Path(temp_path).unlink(missing_ok=True)

    return face


@app.websocket("/ws/video")
async def video_websocket(websocket: WebSocket):
    await websocket.accept()
    last_frame_time = 0
    frame_interval = 1 / 24  # Reduce to 24 FPS for stability
    last_frame_content = None

    try:
        while True:
            current_time = time.time()
            if current_time - last_frame_time < frame_interval:
                await asyncio.sleep(0)
                continue

            if not current_frame_path.exists():
                await asyncio.sleep(0)
                continue

            try:
                with open(current_frame_path, "rb") as f:
                    frame_bytes = f.read()
                    # Only send frame if it's different from the last one
                    if frame_bytes != last_frame_content:
                        await websocket.send_bytes(frame_bytes)
                        last_frame_content = frame_bytes
                        last_frame_time = current_time
            except (FileNotFoundError, PermissionError):
                continue

    except WebSocketDisconnect:
        print("Client disconnected")
