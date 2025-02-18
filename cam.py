import cv2
import time

from core.esp32_camera import get_video_feed
from core.controller import VIDEO_URL, ScreenResolution, set_flash, set_framesize
from core.face import initialize_face_recognition, start_recognizing
from core.face_detection import FaceDetection
from core.face_liveness import LivenessDetection
from core.webcam import get_webcam_feed, get_remote_webcam_feed
from models.face import Face
from utils.helpers import calculate_darkness_percentage, calculate_flash_intensity
from utils.visualize_helpers import draw_faces
from utils.constants import deepPix_checkpoint_path, img_folder, current_frame_path


def process_video_feed(show_video: bool = False):
    frame_skip = 2  # Process every 2nd frame instead of 3

    faceDetector = FaceDetection(max_num_faces=1)
    livenessDetector = LivenessDetection(
        checkpoint_path=deepPix_checkpoint_path.as_posix()
    )

    if show_video:
        cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Video", 800, 600)

    # set_framesize(ScreenResolution.SXGA_1280_1024)

    no_cam_img_path = "imgs/no-cam.png"
    no_cam_frame = cv2.imread(no_cam_img_path)

    detected_faces: dict[str, Face] = {}
    current_frame = 0
    last_flash_change = -1
    last_flash_intensity = 0

    is_frame_available = True
    print("Starting video feed...")
    while True:
        try:
            # frame = get_video_feed(VIDEO_URL)
            frame = get_remote_webcam_feed("http://192.168.0.60:9999")
            if frame is None:  # Check if frame is None
                frame = no_cam_frame
                is_frame_available = False

            small_frame = cv2.resize(
                frame, (0, 0), fx=0.5, fy=0.5
            )  # Resize frame to 1/4th size to increase speed

            if current_frame == 0 and is_frame_available:
                if last_flash_change == -1 or time.time() - last_flash_change > 5:
                    if last_flash_intensity > 0:
                        set_flash(
                            0
                        )  # Turn off flash so calculate darkness level is accurate

                    darkness_level = calculate_darkness_percentage(frame)
                    flash_intensity = calculate_flash_intensity(
                        darkness_level, threshold=70, max_flash_intensity=255
                    )
                    if flash_intensity > 0:
                        set_flash(flash_intensity)
                        last_flash_change = time.time()
                        last_flash_intensity = flash_intensity

                    print(
                        f"Darkness level: {darkness_level}, Flash intensity: {flash_intensity}"
                    )

                frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                # face_locations = face_recognition.face_locations(frame_rgb, model="hog")
                faces, boxes = faceDetector(frame_rgb)

                matched_ids = []
                for f, box in zip(faces, boxes):
                    liveness_val = livenessDetector(face_arr=f)
                    print(f"Face liveness: {liveness_val}")
                    face = Face(bbox=box, liveness=liveness_val)
                    face_path = str(img_folder / f"{face.id}.jpg")
                    f = cv2.cvtColor(f, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(face_path, f)
                    face.face_image_path = face_path
                    most_similar, max_match = face.most_similar(
                        list(detected_faces.values())
                    )

                    face_matched = False
                    if most_similar is not None:
                        if max_match > 0.8:
                            for b in detected_faces.values():
                                if b.id == most_similar.id:
                                    face_matched = True

                                    matched_ids.append(b.id)
                                    b.live_update(face)
                                    break

                    if not face_matched:
                        start_recognizing(frame=frame_rgb, face=face)
                        detected_faces[face.id] = face
                        matched_ids.append(face.id)

                # detected_faces = {
                #     k: v for k, v in detected_faces.items() if k in matched_ids
                # }

                new_detected_faces = {}
                for k, v in detected_faces.items():
                    if k in matched_ids:
                        new_detected_faces[k] = v
                    else:
                        v.active = False
                        v.live_update(v)

                detected_faces = new_detected_faces
                print(f"Found {len(faces)} faces", end="\r")

            if is_frame_available:
                current_frame = (current_frame + 1) % frame_skip
                frame = draw_faces(
                    frame, [f.scale_copy(2) for f in detected_faces.values()]
                )
                # Resize frame to a reasonable size before saving
                frame = cv2.resize(frame, (1280, 720))
                cv2.imwrite(
                    str(current_frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
                )

            if show_video:
                cv2.imshow("Video", frame)

                # Add shorter wait time and more frequent window updates
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
            # Remove the sleep delay that was here

        except KeyboardInterrupt:
            break

        except Exception as e:
            print(f"Error in main loop: {e}")
            # Reduce error wait time
            time.sleep(0.05)

    set_flash(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    initialize_face_recognition()
    process_video_feed(show_video=True)
