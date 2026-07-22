# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from strenum import StrEnum


class SceneFunction(StrEnum):
    CHANGE_SCENE = "scene_x"
    CHANGE_ALL = "scene_all"
    SCENE_OFF = "scene_off"
    SCENE_OFF_ALL = "scene_off_all"
