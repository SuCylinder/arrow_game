# -*- coding: utf-8 -*-
"""第 4 关（12 支单格箭头）。

箭头格式：(方向, 行, 列)
参考通关顺序：(0,4) → (4,1) → (0,3) → (3,1) → (0,1) → (1,4)
              → (2,1) → (3,3) → (3,0) → (2,4) → (4,3) → (4,4)
"""

from arrow.config import DOWN, LEFT, RIGHT, UP

LEVEL = [
    (UP, 4, 4),
    (LEFT, 4, 3),
    (LEFT, 2, 4),
    (LEFT, 3, 0),
    (UP, 3, 3),
    (DOWN, 2, 1),
    (UP, 1, 4),
    (LEFT, 0, 1),
    (DOWN, 3, 1),
    (RIGHT, 0, 3),
    (LEFT, 4, 1),
    (UP, 0, 4),
]
