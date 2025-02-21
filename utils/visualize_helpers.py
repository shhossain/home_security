import cv2
import numpy as np

from models.face import Face


def draw_faces(frame, faces: list[Face]):
    # Get frame dimensions for relative sizing
    frame_height, frame_width, _ = frame.shape
    base_thickness = max(1, int(frame_width * 0.002))  # Relative line thickness
    corner_length = int(frame_width * 0.03)  # Relative corner length
    font_scale = frame_width * 0.001  # Relative font size

    # Colors
    CORNER_COLOR = (0, 255, 0)  # Green corners
    TEXT_BG_COLOR = (50, 50, 200)  # Dark blue background for text
    TEXT_COLOR = (255, 255, 255)
    INFO_COLOR = (255, 128, 0)  # Orange for additional info

    for face in faces:
        box = face.bbox
        top, right, bottom, left = box.top, box.right, box.bottom, box.left

        # Draw corners instead of full rectangle
        # Top-left
        cv2.line(
            frame,
            (left, top),
            (left + corner_length, top),
            CORNER_COLOR,
            base_thickness,
        )
        cv2.line(
            frame,
            (left, top),
            (left, top + corner_length),
            CORNER_COLOR,
            base_thickness,
        )
        # Top-right
        cv2.line(
            frame,
            (right - corner_length, top),
            (right, top),
            CORNER_COLOR,
            base_thickness,
        )
        cv2.line(
            frame,
            (right, top),
            (right, top + corner_length),
            CORNER_COLOR,
            base_thickness,
        )
        # Bottom-left
        cv2.line(
            frame,
            (left, bottom),
            (left + corner_length, bottom),
            CORNER_COLOR,
            base_thickness,
        )
        cv2.line(
            frame,
            (left, bottom - corner_length),
            (left, bottom),
            CORNER_COLOR,
            base_thickness,
        )
        # Bottom-right
        cv2.line(
            frame,
            (right - corner_length, bottom),
            (right, bottom),
            CORNER_COLOR,
            base_thickness,
        )
        cv2.line(
            frame,
            (right, bottom - corner_length),
            (right, bottom),
            CORNER_COLOR,
            base_thickness,
        )

        # Text positioning and sizing
        text_height = int(frame_height * 0.04)
        padding = int(frame_width * 0.01)

        # Always show additional information on the left side
        info_y = top + text_height
        cv2.putText(
            frame,
            f"REAL: {int(face.liveness * 100)}%",
            (left - padding, info_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale * 0.7,
            INFO_COLOR,
            base_thickness,
        )

        near = box.near_frame(frame_width, frame_height)
        cv2.putText(
            frame,
            f"CLOSE: {near}",
            (left - padding, info_y + text_height),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale * 0.7,
            INFO_COLOR,
            base_thickness,
        )

        # Name or loading animation display
        text_x = right - padding
        text_y = top - padding if top > text_height else bottom + text_height

        if not face.is_loaded:
            # Loading animation with dots
            dot_spacing = int(frame_width * 0.008)
            dot_radius = max(2, int(frame_width * 0.003))
            last_dot = face.state.get("last_dot", 0)

            for i in range(3):
                dot_x = text_x - (i * dot_spacing * 2)
                dot_alpha = 255 if (i + last_dot) % 3 == 0 else 100
                cv2.circle(
                    frame, (dot_x, text_y), dot_radius, (*TEXT_COLOR, dot_alpha), -1
                )

            face.state["last_dot"] = (last_dot + 1) % 3
        else:
            # Name display
            text_size = cv2.getTextSize(
                face.name, cv2.FONT_HERSHEY_DUPLEX, font_scale, base_thickness
            )[0]
            text_x -= text_size[0]  # Adjust x position for text alignment

            # Background for name
            bg_padding = int(padding / 2)
            cv2.rectangle(
                frame,
                (text_x - bg_padding, text_y - text_size[1] - bg_padding),
                (text_x + text_size[0] + bg_padding, text_y + bg_padding),
                TEXT_BG_COLOR,
                cv2.FILLED,
            )

            cv2.putText(
                frame,
                face.name,
                (text_x, text_y),
                cv2.FONT_HERSHEY_DUPLEX,
                font_scale,
                TEXT_COLOR,
                base_thickness,
            )

    return frame
