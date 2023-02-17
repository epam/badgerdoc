from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass
class BorderBox:
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int
    bbox_id: int = field(init=False)

    def __post_init__(self) -> None:
        self.bbox_id = id(self)

    @property
    def box(self) -> Tuple[int, int, int, int]:
        return (
            self.top_left_x,
            self.top_left_y,
            self.bottom_right_x,
            self.bottom_right_y,
        )

    @property
    def width(self) -> int:
        return self.bottom_right_x - self.top_left_x

    @property
    def height(self) -> int:
        return self.bottom_right_y - self.top_left_y

    def merge(self, bb: BorderBox) -> BorderBox:
        return BorderBox(
            top_left_x=min(self.top_left_x, bb.top_left_x),
            top_left_y=min(self.top_left_y, bb.top_left_y),
            bottom_right_x=max(self.bottom_right_x, bb.bottom_right_x),
            bottom_right_y=max(self.bottom_right_y, bb.bottom_right_y),
        )

    def box_is_inside_another(self, bb2: BorderBox, threshold: float = 0.9) -> bool:
        (
            intersection_area,
            bb1_area,
            bb2_area,
        ) = self.get_boxes_intersection_area(other_box=bb2)
        if intersection_area == 0:
            return False
        return any((intersection_area / bb) > threshold for bb in (bb1_area, bb2_area))

    def box_is_inside_box(self, bb2: BorderBox, threshold: float = 0.95) -> bool:
        (
            intersection_area,
            bb1_area,
            bb2_area,
        ) = self.get_boxes_intersection_area(other_box=bb2)
        if intersection_area == 0:
            return False
        return bool((intersection_area / bb1_area) > threshold)

    def get_boxes_intersection_area(
        self, other_box: BorderBox
    ) -> Tuple[float, int, int]:
        bb1 = self.box
        bb2 = other_box.box
        x_left = max(bb1[0], bb2[0])
        y_top = max(bb1[1], bb2[1])
        x_right = min(bb1[2], bb2[2])
        y_bottom = min(bb1[3], bb2[3])
        if x_right < x_left or y_bottom < y_top:
            intersection_area = 0.0
        else:
            intersection_area = (x_right - x_left + 1) * (y_bottom - y_top + 1)
        bb1_area = (bb1[2] - bb1[0] + 1) * (bb1[3] - bb1[1] + 1)
        bb2_area = (bb2[2] - bb2[0] + 1) * (bb2[3] - bb2[1] + 1)
        return intersection_area, bb1_area, bb2_area

    def __getitem__(self, item: int) -> int:
        return self.box[item]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> BorderBox:
        return cls(
            top_left_x=d.get("left", 0),
            top_left_y=d.get("top", 0),
            bottom_right_x=d.get("left", 0) + d.get("width", 0),
            bottom_right_y=d.get("top", 0) + d.get("height", 0),
        )
