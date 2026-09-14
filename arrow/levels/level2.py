# -*- coding: utf-8 -*-
"""第 2 关（8 支单格箭头）。

箭头格式：(方向, 行, 列)
参考通关顺序：(4,1) → (3,0) → (4,3) → (3,1) → (3,2) → (4,2) → (3,4) → (2,1)
"""

from arrow.config import DOWN, LEFT, RIGHT, UP

LEVEL = [
    (DOWN, 2, 1),
    (LEFT, 3, 4),
    (RIGHT, 4, 2),
    (LEFT, 3, 2),
    (DOWN, 3, 1),
    (UP, 4, 3),
    (LEFT, 3, 0),
    (LEFT, 4, 1),
]
