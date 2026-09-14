# -*- coding: utf-8 -*-
"""第 1 关（6 支单格箭头）。

箭头格式：(方向, 行, 列)
参考通关顺序：(4,3) → (2,3) → (2,0) → (1,3) → (1,1) → (1,2)
"""

from arrow.config import DOWN, LEFT, RIGHT, UP

LEVEL = [
    (LEFT, 1, 2),
    (DOWN, 1, 1),
    (UP, 1, 3),
    (RIGHT, 2, 0),
    (DOWN, 2, 3),
    (RIGHT, 4, 3),
]
