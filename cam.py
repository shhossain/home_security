from pathlib import Path
import threading
import cv2
import time
import os
from core.esp32_camera import get_video_feed
from core.controller import (
    ScreenResolution,
    check_and_set_framesize,
    get_video_url,
    set_flash,
    set_framesize,
    find_and_change_esp32_ip,
)
from core.face import load_faces, recognize_faces, save_face, start_recognizing
from core.face_detection import FaceDetection
from core.face_liveness import LivenessDetection
from core.webcam import get_remote_webcam_feed, get_webcam_feed
from models.face import Face
from models.config import settings
from utils.helpers import (
    calculate_darkness_percentage,
    calculate_flash_intensity,
)
from utils.visualize_helpers import draw_faces
from utils.constants import (
    deepPix_checkpoint_path,
    img_folder,
    current_frame_path,
    FILE_PERMS,
    should_run_thread,
)


def get_frame(cam: str):
    print(f"Getting frame from {cam}...", end="\r")
    if cam == "esp32":
        try:
            print(f"Getting frame from {settings.esp32_ip}...", end="\r")
            return get_video_feed(get_video_url(settings.esp32_ip))
        except Exception as e:
            for _ in range(3):
                print("Error getting video feed, retrying...")
                if find_and_change_esp32_ip():
                    return
                print("Could not find esp32 camera, retrying...")
                time.sleep(2)

    elif (
        cam.isnumeric()
        or cam.startswith("http")
        or cam.startswith("rtsp")
        or Path(cam).exists()
    ):
        return get_webcam_feed(cam if not cam.isnumeric() else int(cam))

    elif "demo" in cam:
        path = "https://videos.pexels.com/video-files/3981739/3981739-uhd_3840_2160_30fps.mp4"
        return get_webcam_feed(path, repeat=True)

    else:
        raise ValueError("Invalid camera source")


def process_video_feed():
    frame_skip = 1

    faceDetector = FaceDetection(max_num_faces=settings.max_face_detection)
    livenessDetector = LivenessDetection(
        checkpoint_path=deepPix_checkpoint_path.as_posix()
    )

    if settings.show_video:
        cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Video", 800, 600)

    set_framesize(ScreenResolution.SXGA_1280_1024)
    set_flash(0)

    no_cam_img_path = "imgs/no-cam.png"
    no_cam_frame = cv2.imread(no_cam_img_path)

    detected_faces: dict[str, Face] = {}
    current_frame = 0
    last_flash_change = time.time()
    last_flash_intensity = 0
    # last_open_door = time.time()

    is_frame_available = True
    print("Starting video feed...")
    while should_run_thread.value:
        try:
            frame = get_frame(settings.cam_str)
            print("Frame received...")

            if frame is None:
                frame = no_cam_frame
                is_frame_available = False
            else:
                is_frame_available = True
                threading.Thread(target=check_and_set_framesize, daemon=True).start()

            if is_frame_available:
                # Optimize frame resize
                frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_NEAREST)

                # Draw faces on the frame
                drawing_frame = frame.copy()
                if len(detected_faces) > 0:
                    drawing_frame = draw_faces(frame, list(detected_faces.values()))

                # Higher quality JPEG compression for better visualization
                encode_params = [
                    int(cv2.IMWRITE_JPEG_QUALITY),
                    85,  # Increased quality
                    int(cv2.IMWRITE_JPEG_OPTIMIZE),
                    1,
                    int(cv2.IMWRITE_JPEG_PROGRESSIVE),
                    1,
                ]

                success, buffer = cv2.imencode(".jpg", drawing_frame, encode_params)
                if success:
                    # Write directly to file instead of using temporary file
                    try:
                        with open(current_frame_path, "wb") as f:
                            f.write(buffer.tobytes())
                        os.chmod(current_frame_path, FILE_PERMS)
                    except Exception as e:
                        print(f"Frame write error: {e}")

            # Reduced processing frequency
            if is_frame_available:
                print("Processing frame...")
                # if last_flash_change == -1 or time.time() - last_flash_change > 10:
                #     if last_flash_intensity > 0:
                #         set_flash(0)

                #     darkness_level = calculate_darkness_percentage(frame)
                #     flash_intensity = calculate_flash_intensity(
                #         darkness_level, threshold=80, max_flash_intensity=255
                #     )
                #     if flash_intensity > 0:
                #         set_flash(flash_intensity)
                #         last_flash_change = time.time()
                #         last_flash_intensity = flash_intensity

                #     print(
                #         f"Darkness level: {darkness_level}, Flash intensity: {flash_intensity}"
                #     )

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                print("Detecting faces...")
                faces, boxes = faceDetector(frame_rgb)

                matched_ids = []
                ignore_ids = []
                for fce, box in zip(faces, boxes):
                    # liveness_val = 0
                    print("Detecting liveness...")
                    liveness_val = livenessDetector(face_arr=fce)
                    print(f"Face liveness: {liveness_val}")
                    face = Face(bbox=box, liveness=liveness_val)
                    # frame width and height
                    frame_width, frame_height = frame.shape[1], frame.shape[0]
                    near = face.bbox.near_frame(frame_width, frame_height)
                    face.near = near
                    face_path = str(img_folder / f"{face.id}.jpg")
                    fce = cv2.cvtColor(fce, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(face_path, fce)
                    face.face_image_path = face_path
                    most_similar, max_match = face.most_similar(
                        [f for f in detected_faces.values() if f.id not in ignore_ids]
                    )

                    face_matched = False
                    if most_similar is not None:
                        if max_match > 0.8:
                            for b in detected_faces.values():
                                if b.id == most_similar.id:
                                    face_matched = True
                                    matched_ids.append(b.id)
                                    ignore_ids.append(b.id)
                                    b.live_update(face)
                                    break

                    if not face_matched:
                        print("Starting recognizing...")
                        start_recognizing(frame=frame_rgb, face=face)
                        detected_faces[face.id] = face
                        matched_ids.append(face.id)

                print("Filtering faces...")
                new_detected_faces = {}
                for k, v in detected_faces.items():
                    if k in matched_ids:
                        new_detected_faces[k] = v

                        # if face is unknown check it again
                        if v.is_loaded and v.is_unknown:
                            start_recognizing(
                                frame=frame_rgb,
                                face=v,
                                tolerance=settings.face_detection_threshold,
                            )
                    else:
                        v.active = False
                        v.live_update(v)

                detected_faces = new_detected_faces
                print(f"Found {len(faces)} faces", end="\r")

            current_frame = (current_frame + 1) % frame_skip

            if settings.show_video:
                cv2.imshow("Video", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    settings.set("show_video", 0)
            else:
                cv2.destroyAllWindows()

            if settings.fps:
                time.sleep(1 / settings.fps)

            time.sleep(0.001)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(0.05)

    set_flash(0)
    cv2.destroyAllWindows()


def init():
    threading.Thread(
        target=save_face,
        args=(r"C:\Users\sifat\Downloads\sifat.jpg", "Sifat"),
        daemon=True,
    ).start()
    threading.Thread(target=process_video_feed).start()
    threading.Thread(target=recognize_faces).start()
    threading.Thread(target=load_faces).start()


if __name__ == "__main__":
    settings.set("show_video", 1)

    init()
