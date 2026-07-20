# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from wled_ros_driver.types.scene_function import SceneFunction
from wled_ros_driver.types.color_data import Color


@dataclass(frozen=True, slots=True)
class RunLightsData:
    scene_function: SceneFunction
    color: Color
    brightness: int
    start_led_id: int
    stop_led_id: int

    def __len__(self) -> int:
        return len(self.__slots__)

    def __str__(self) -> str:

        return f"color:{self.color}, brightness:{self.brightness}, start:{self.start_led_id}, stop:{self.stop_led_id}"
