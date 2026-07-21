# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from wled_ros_driver.types.tuples import Color
from wled_ros_driver.types.enum_types import SceneFunction
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SectionData:
    section_id: int
    start_led_id: int
    stop_led_id: int

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
    effect: str

    def __len__(self) -> int:
        return len(self.__slots__)

    def __str__(self) -> str:
        return f"color:{self.color}, brightness:{self.brightness}, start:{self.start_led_id}, stop:{self.stop_led_id}"


@dataclass(frozen=True, slots=True)
class SceneData:
    brightness: int
    color: Color

    def __len__(self) -> int:
        return len(self.__slots__)

    def __str__(self) -> str:
        return f"color:{self.color}, brightness:{self.brightness}, start:{self.start}, stop:{self.stop}, color:{self.color}"
