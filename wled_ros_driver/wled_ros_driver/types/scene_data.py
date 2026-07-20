# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from wled_ros_driver.types.color_data import Color


@dataclass(frozen=True, slots=True)
class SceneData:
    brightness: int
    start: int
    stop: int
    effect: str
    color: Color

    def __len__(self) -> int:
        return len(self.__slots__)

    def __str__(self) -> str:
        return f"color:{self.color}, brightness:{self.brightness}"
