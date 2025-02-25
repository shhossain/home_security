from typing import Literal, TypedDict, overload
import json
from utils.constants import app_path
from pydantic import BaseModel

config_path = app_path / "config.json"


ConfigKeys = Literal[
    "esp32_ip",
    "liveness_threshold",
    "door_open_delay",
    "door_open_for",
    "max_face_detection",
    "face_detection_threshold",
    "show_video",
    "fps"
]


class FaceDetectionConfig(TypedDict):
    max_faces: int
    face_matching_threshold: float


class Config(BaseModel):
    esp32_ip: str = "192.168.0.52"
    liveness_threshold: float = 0.8
    door_open_delay: int = 5
    door_open_for: int = 3
    max_face_detection: int = 3
    face_detection_threshold: float = 0.8
    show_video: int = 0
    cam_str: str = "esp32"
    fps: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load_config(self):
        if config_path.exists():
            with open(config_path, "r") as f:
                try:
                    stored_config = json.load(f)
                    for key, value in stored_config.items():
                        # setattr(self, key, value)
                        if hasattr(self, key):
                            setattr(self, key, value)
                except json.JSONDecodeError:
                    pass

    def _save_config(self):
        with open(config_path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    def update(self, obj):
        updated = self.model_validate(obj)
        print(updated)
        for key, value in updated.model_dump().items():
            setattr(self, key, value)
        self._save_config()

    @overload
    def set(self, key: Literal["esp32_ip"], value: str): ...
    @overload
    def set(
        self,
        key: Literal["liveness_threshold", "face_detection_threshold"],
        value: float,
    ): ...
    @overload
    def set(
        self,
        key: Literal[
            "door_open_delay",
            "door_open_for",
            "max_face_detection",
            "show_video",
            "fps"
        ],
        value: int,
    ): ...

    def set(self, key: ConfigKeys, value):
        setattr(self, key, value)
        self._save_config()

    @overload
    def get(self, key: Literal["esp32_ip"]) -> str: ...
    @overload
    def get(
        self, key: Literal["liveness_threshold", "face_detection_threshold"]
    ) -> float: ...
    @overload
    def get(
        self,
        key: Literal[
            "door_open_delay",
            "door_open_for",
            "max_face_detection",
            "show_video",
            "fps"
        ],
    ) -> int: ...
    def get(self, key: ConfigKeys):
        return getattr(self, key)


settings = Config()
settings.load_config()


__all__ = ["settings"]
