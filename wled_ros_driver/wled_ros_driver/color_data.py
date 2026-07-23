# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from typing import NamedTuple


class Color(NamedTuple):
    R: int
    G: int
    B: int

    def __str__(self) -> str:
        return f"R:{self.R} G:{self.G} B:{self.B}"
