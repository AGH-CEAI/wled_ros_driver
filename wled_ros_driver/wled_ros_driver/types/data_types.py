# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from wled_ros_driver.types.enum_types import SceneFunction
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Color:
    R: int
    G: int
    B: int

    def __str__(self) -> str:
        return f"R:{self.R} G:{self.G} B:{self.B}"

    @property
    def as_list(self) -> list[int]:
        return [self.R, self.G, self.B]


@dataclass(frozen=True, slots=True)
class SectionData:
    section_id: int = 0
    start_led_id: int = 0
    stop_led_id: int = 0

    def __len__(self) -> int:
        return len(self.__slots__)


@dataclass(frozen=True, slots=True)
class RunLightsData:
    scene_function: SceneFunction
    color: Color
    brightness: int
    section_id: int
    start_led_id: int
    stop_led_id: int
    effect: str = "Solid"

    def __len__(self) -> int:
        return len(self.__slots__)

    def __str__(self) -> str:
        return f"color:{self.color}, brightness:{self.brightness}, start:{self.start_led_id}, stop:{self.stop_led_id}, effect:{self.effect}"


@dataclass(frozen=True, slots=True)
class SceneData:
    brightness: int = 255
    color: Color = Color(0, 0, 0)

    def __len__(self) -> int:
        return len(self.__slots__)

    def __str__(self) -> str:
        return f"color:{self.color}, brightness:{self.brightness}, start:{self.start}, stop:{self.stop}, color:{self.color}"
