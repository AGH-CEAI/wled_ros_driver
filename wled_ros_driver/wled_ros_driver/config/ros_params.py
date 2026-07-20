# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from strenum import StrEnum


class RosParams(StrEnum):
    SCENE_OFF_KEY = "scene_off"
    SCENE_CUSTOM_KEY = "scene_custom"
    SECTION_ALL_KEY = "section_all"

    WLED_CONTROLLER_URL = "wled_url"
    WLED_SEGMENTS_COUNT = "wled_count"
