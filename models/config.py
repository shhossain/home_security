import time
from typing import Literal, TypedDict, overload
import json
from utils.constants import app_path
from pydantic import BaseModel
from prisma import Prisma
import os
import threading

config_path = app_path / "config.json"


ConfigKeys = Literal[
    "esp32_ip",
    "liveness_threshold",
    "door_open_delay",
    "door_open_for",
    "max_face_detection",
    "face_detection_threshold",
    "show_video",
    "fps",
]

config_name = os.getenv("CONFIG_NAME", "esp32_config")

db = Prisma()
db.connect()


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
        # run load_config in every 5 seconds
        threading.Thread(target=self._load_config_thread, daemon=True).start()

    def _load_config_thread(self):
        while True:
            self.load_config()
            time.sleep(5)

    def load_config(self):
        config = db.settings.find_unique(where={"name": config_name})
        if config:
            for _ in range(3):
                try:
                    val = json.loads(config.value)
                    for key, value in val.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                    break
                except json.JSONDecodeError:
                    print("Invalid JSON")
                except Exception as e:
                    print(f"Error loading config: {e}")
        else:
            self._save_config()

    def _save_config(self):
        for _ in range(3):
            try:
                db.settings.upsert(
                    where={"name": config_name},
                    data={
                        "create": {
                            "name": config_name,
                            "value": json.dumps(self.model_dump()),
                        },
                        "update": {"value": json.dumps(self.model_dump())},
                    },
                )
                break
            except Exception as e:
                print(f"Error saving config: {e}")

    def update(self, obj):
        updated = self.model_validate(obj)
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
            "fps",
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
            "fps",
        ],
    ) -> int: ...
    def get(self, key: ConfigKeys):
        return getattr(self, key)


settings = Config()
settings.load_config()


__all__ = ["settings"]
