# -*- coding: utf-8 -*-
"""全局配置包：窗口布局、颜色、规则常量。

拆成三个子模块，这里统一重导出，外部照旧 `from arrow.config import X` 使用。
"""

from arrow.config.layout import (
    CELL,
    FPS,
    GRID_W,
    GRID_X,
    GRID_Y,
    HEIGHT,
    N,
    WIDTH,
)
from arrow.config.palette import (
    ARROW_COLORS,
    BG,
    BODY_DARKEN,
    BTN,
    BTN_HOVER,
    BTN_PRIMARY,
    BTN_PRIMARY_HOVER,
    CELL_BG,
    CELL_LINE,
    DIM,
    RED,
    TEXT,
)
from arrow.config.rules import (
    DIRS,
    DOWN,
    EMPTY,
    LEFT,
    MAX_LENGTH,
    MIN_LENGTH,
    MISTAKES_PER_LEVEL,
    RIGHT,
    STATE_LOSE,
    STATE_PLAY,
    STATE_START,
    STATE_WIN,
    UP,
)

__all__ = [
    # layout
    "WIDTH",
    "HEIGHT",
    "FPS",
    "N",
    "CELL",
    "GRID_W",
    "GRID_X",
    "GRID_Y",
    # palette
    "BG",
    "CELL_BG",
    "CELL_LINE",
    "TEXT",
    "DIM",
    "RED",
    "BTN",
    "BTN_HOVER",
    "BTN_PRIMARY",
    "BTN_PRIMARY_HOVER",
    "BODY_DARKEN",
    "ARROW_COLORS",
    # rules
    "EMPTY",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "DIRS",
    "MISTAKES_PER_LEVEL",
    "MIN_LENGTH",
    "MAX_LENGTH",
    "STATE_START",
    "STATE_PLAY",
    "STATE_WIN",
    "STATE_LOSE",
]
