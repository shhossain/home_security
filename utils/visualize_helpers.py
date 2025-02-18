import cv2
import numpy as np

from models.face import Face


def draw_faces(frame, faces: list[Face]):
    # Color definitions
    BOX_COLOR = (0, 255, 0)  # Green box
    NAME_BG_COLOR = (50, 50, 200)  # Dark blue background for name
    LIVENESS_COLOR = (255, 128, 0)
    NEAR_COLOR = (255, 128, 0)

    for face in faces:
        box = face.bbox
        top, right, bottom, left = box.top, box.right, box.bottom, box.left

        # Draw a rectangle around the face with green color
        cv2.rectangle(frame, (left, top), (right, bottom), BOX_COLOR, 2)

        # Draw a label with a name below the face
        cv2.rectangle(
            frame, (left, bottom + 5), (right, bottom + 40), NAME_BG_COLOR, cv2.FILLED
        )
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(
            frame, face.name, (left + 6, bottom + 34), font, 1.0, (255, 255, 255), 1
        )

        # Liveness indicator with orange color
        cv2.putText(
            frame,
            f"Liveness: {int(face.liveness * 100)}%",
            (left, top - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            LIVENESS_COLOR,
            2,
        )

        # Near indicator with deep yellow color
        frame_height, frame_width, _ = frame.shape
        near = box.near_frame(frame_width, frame_height)
        cv2.putText(
            frame,
            f"Near: {near}",
            (left, top - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            NEAR_COLOR,
            2,
        )

        # Loading animation with rainbow colors
        if not face.is_loaded:
            center = (left + 30, top + 30)
            radius = 15
            last_angle = face.state.get("last_angle", 0)

            # Draw base circle with purple color
            cv2.circle(frame, center, radius, (255, 0, 255), 2)

            # Draw rotating dots with rainbow colors
            for i in range(8):
                angle = last_angle + (i * 45)
                dot_x = int(center[0] + radius * np.cos(np.radians(angle)))
                dot_y = int(center[1] + radius * np.sin(np.radians(angle)))

                # Create rainbow effect
                hue = (i * 180 // 8 + last_angle) % 180
                hsv_color = np.array([[[hue, 255, 255]]], dtype=np.uint8)
                rgb_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]

                # Draw colored dot
                cv2.circle(frame, (dot_x, dot_y), 3, rgb_color.tolist(), -1)

            face.state["last_angle"] = (last_angle + 5) % 360

    return frame
