# Copyright (c) 2025-2026, AGH Center of Excellence in Artificial Intelligence
# All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
from typing import NamedTuple,Sequence

# 1. Define the named tuple structure
class Color(NamedTuple):
    R: int
    G: int
    B: int

    @classmethod
    def from_list(cls, values: Sequence[int]) -> "Color":
        if len(values) != 3:
            raise ValueError("Color must have exactly 3 components: R, G, B")
        return cls(*values)

    def __str__(self) -> str:
        return f"R:{self.R} G:{self.G} B:{self.B}"
