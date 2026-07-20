# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SectionData:
    start_led_id: int
    stop_led_id: int

    def __len__(self) -> int:
        return len(self.__slots__)
