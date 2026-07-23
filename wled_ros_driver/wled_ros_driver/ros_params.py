# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from strenum import StrEnum


class RosParams(StrEnum):
    SERVICE_NAME = "wled_scene_change"

    WLED_CONTROLLER_URL = "wled_url"
    WLED_SEGMENTS_COUNT = "wled_count"

    SCENE_OFF_KEY = "scene_off"
    SCENE_CUSTOM_KEY = "scene_custom"

    SECTION_ALL_KEY = "section_all"

    SCENES_YAML_NAME = "scenes"
    SCENES_COLOR_PARAMETER = "color"

    REQUEST_SCENE_KEY = "scene"
    REQUEST_SECTION_KEY = "section"

    SCENE_SET_MESSAGE = "Scene complete"
    SCENE_ERROR_MESSAGE = "Failed to execute scene"
