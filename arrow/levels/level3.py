# -*- coding: utf-8 -*-
"""第 3 关（10 支单格箭头）。

箭头格式：(方向, 行, 列)
参考通关顺序：(4,1) → (0,0) → (0,4) → (2,1) → (1,4)
              → (1,1) → (4,2) → (3,2) → (3,4) → (2,0)
"""

from arrow.config import DOWN, LEFT, RIGHT, UP

LEVEL = [
    (UP, 2, 0),
    (RIGHT, 3, 4),
    (UP, 3, 2),
    (LEFT, 4, 2),
    (DOWN, 1, 1),
    (UP, 1, 4),
    (DOWN, 2, 1),
    (LEFT, 0, 4),
    (UP, 0, 0),
    (DOWN, 4, 1),
]
