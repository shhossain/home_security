from typing import Sequence
from pydantic import BaseModel


class Box(BaseModel):
    top: int
    right: int
    bottom: int
    left: int

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def area(self):
        return self.width * self.height

    def near_frame(self, frame_width: int, frame_height: int) -> int:
        area_ratio = self.area / (frame_width * frame_height)
        return int((1 - area_ratio) * 100)

    def __getitem__(self, idx: int):
        if idx < 0 or idx > 3:
            raise IndexError("Index must be between 0 and 3")
        return [self.left, self.top, self.right, self.bottom][idx]

    @classmethod
    def from_list(cls, lst: Sequence[int]) -> "Box":
        return cls(top=lst[0], right=lst[1], bottom=lst[2], left=lst[3])

    def update(self, other: "Box"):
        self.top = other.top
        self.right = other.right
        self.bottom = other.bottom
        self.left = other.left

    def match_percentage(self, other: "Box") -> float:
        intersection = max(
            0, min(self.right, other.right) - max(self.left, other.left)
        ) * max(0, min(self.bottom, other.bottom) - max(self.top, other.top))
        # Calculate the area of union
        union = (
            (self.right - self.left) * (self.bottom - self.top)
            + (other.right - other.left) * (other.bottom - other.top)
            - intersection
        )
        return intersection / union

    def scale_copy(self, factor: float) -> "Box":
        return Box(
            top=int(self.top * factor),
            right=int(self.right * factor),
            bottom=int(self.bottom * factor),
            left=int(self.left * factor),
        )
