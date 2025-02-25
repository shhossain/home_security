import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from prisma import Prisma
from prisma.types import FaceWhereInput
from pydantic import BaseModel
from core.face import load_faces, recognize_faces, save_face
from models.helpers import Box
from utils.constants import current_frame_path, should_process_video
from models.face import db
from fastapi.middleware.cors import CORSMiddleware
import datetime as dt
from cam import process_video_feed
import threading
import shutil
import tempfile
import aiofiles
import async_timeout
from PIL import Image, ImageDraw, ImageFont
import base64
import face_recognition
from utils.constants import frame_lock_path, should_run_thread
from utils.helpers import base64_to_image, image_to_base64
from multiprocessing import Value
import uvicorn
from models.config import Config, settings
from models.status import ESP32CameraStatus
from core.controller import set_flash, set_servo_angle, open_and_close_door

db = Prisma()
is_video_feed_running = Value("b", False)


# save_face(r"C:\Users\sifat\Downloads\sifat.jpg", "Sifat")
# threading.Thread(target=recognize_faces, daemon=True).start()
# threading.Thread(target=load_faces, daemon=True).start()
# threading.Thread(target=process_video_feed).start()


def init():
    threading.Thread(
        target=save_face,
        args=(r"C:\Users\sifat\Downloads\sifat.jpg", "Sifat"),
        daemon=True,
    ).start()
    threading.Thread(target=process_video_feed).start()
    threading.Thread(target=recognize_faces).start()
    threading.Thread(target=load_faces).start()


# app lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    print("Connected to database")
    init()
    yield
    db.disconnect()


app = FastAPI(lifespan=lifespan)

# Add CORS middleware immediately after app creation.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler to ensure CORS headers are included in error responses.
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


class ChangeNameRequest(BaseModel):
    name: str


# String url = "http://" + server_ip + "/camera?ip=" + local_ip;


def _process_video_feed():
    should_process_video.value = True
    is_video_feed_running.value = True
    print("Restarting video feed")
    process_video_feed()


@app.get("/camera")
def get_camera(ip: str):
    if is_video_feed_running.value:
        should_process_video.value = False
        is_video_feed_running.value = False

    settings.set("esp32_ip", ip)

    # run the video feed 5 seconds later
    print("Camera IP changed to =>", ip)

    threading.Timer(10, _process_video_feed).start()

    return {"message": "Camera IP changed"}


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


class DetectedFace(BaseModel):
    id: int
    bbox: dict
    image_data: str


class MultiFaceUploadResponse(BaseModel):
    faces: List[DetectedFace]
    preview_image: str


class FaceSaveRequest(BaseModel):
    file_base64: str
    faces: List[dict]


@app.post("/api/faces/detect")
async def detect_faces_in_image(file: UploadFile = File(...)):
    # Save uploaded file to temp location
    temp_path = tempfile.mktemp(suffix=".jpg")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load image and detect faces
    image = face_recognition.load_image_file(temp_path)
    face_locations = face_recognition.face_locations(image)

    # Create numbered preview image
    img = Image.fromarray(image)
    draw = ImageDraw.Draw(img)
    # Compute dynamic font size and rectangle thickness based on image width
    font_size = max(12, img.width // 50)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    rect_thickness = max(2, img.width // 300)

    detected_faces = []
    for idx, (top, right, bottom, left) in enumerate(face_locations, 1):
        # Draw number on image using dynamic font size
        draw.text((left, top - font_size), str(idx), font=font, fill="green")
        draw.rectangle(
            [(left, top), (right, bottom)], outline="green", width=rect_thickness
        )
        # Extract face image
        face_image = image[top:bottom, left:right]
        face_image_b64 = image_to_base64(face_image)

        detected_faces.append(
            DetectedFace(
                id=idx,
                bbox={"top": top, "right": right, "bottom": bottom, "left": left},
                image_data=face_image_b64,
            )
        )

    # Save preview image
    preview_path = tempfile.mktemp(suffix=".jpg")
    img.save(preview_path)
    with open(preview_path, "rb") as f:
        preview_b64 = base64.b64encode(f.read()).decode()

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)
    Path(preview_path).unlink(missing_ok=True)

    return MultiFaceUploadResponse(faces=detected_faces, preview_image=preview_b64)


@app.post("/api/faces/save-multiple")
async def save_multiple_faces(req: FaceSaveRequest):
    # Remove data URL prefix if present
    file_base64 = req.file_base64
    img = base64_to_image(file_base64)
    if img is None or img.size == 0:
        raise ValueError("Failed to decode image from base64")
    temp_path = tempfile.mktemp(suffix=".jpg")
    cv2.imwrite(temp_path, img)
    results = []
    for face in req.faces:
        try:
            saved_face = save_face(temp_path, face["name"], Box(**face["bbox"]))
            results.append({"id": face["id"], "success": True, "face": saved_face})
        except Exception as e:
            results.append({"id": face["id"], "success": False, "error": str(e)})
    Path(temp_path).unlink(missing_ok=True)
    return {"results": results}


@app.websocket("/ws/video")
async def video_websocket(websocket: WebSocket):
    await websocket.accept()
    last_frame_hash = None

    try:
        while True:
            try:
                # Skip if lock file exists (write in progress)
                if frame_lock_path.exists():
                    await asyncio.sleep(0.001)
                    continue

                async with async_timeout.timeout(0.1):
                    if not current_frame_path.exists():
                        continue

                    try:
                        async with aiofiles.open(current_frame_path, "rb") as f:
                            frame_data = await f.read()
                    except PermissionError:
                        await asyncio.sleep(0.001)
                        continue

                    # Skip if frame is too small or corrupted
                    if len(frame_data) < 100:
                        continue

                    # Calculate frame hash to avoid sending duplicates
                    frame_hash = hash(frame_data)
                    if frame_hash == last_frame_hash:
                        continue

                    # Send frame size first, then frame data
                    size_data = len(frame_data).to_bytes(4, byteorder="big")
                    await websocket.send_bytes(size_data)
                    await websocket.send_bytes(frame_data)

                    last_frame_hash = frame_hash

            except (asyncio.TimeoutError, FileNotFoundError, PermissionError):
                await asyncio.sleep(0.001)
                continue

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket.client_state.value != 3:
            await websocket.close()


@app.get("/api/config")
def get_config():
    return settings.model_dump()


@app.put("/api/config")
async def update_config(updates: Config):
    settings.update(updates)
    return settings.model_dump()


@app.get("/api/esp32/status")
def get_esp32_status():
    try:
        status = ESP32CameraStatus(settings)
        return status.model_dump()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/esp32/control")
async def control_esp32(command: dict):
    cmd_type = command.get("type")
    value = command.get("value")

    if cmd_type == "flash":
        set_flash(value)
    elif cmd_type == "servo":
        set_servo_angle(value)
    elif cmd_type == "door":
        if value:
            open_and_close_door()
    else:
        return {"error": "Invalid command type"}

    return {"success": True}


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        should_run_thread.value = False

    # exit
