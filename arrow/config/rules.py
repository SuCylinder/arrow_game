# -*- coding: utf-8 -*-
"""游戏规则常量：格子值、方向、胜负状态。"""

# ---------------- 格子值 / 方向 ----------------
EMPTY, UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3, 4
DIRS = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}  # (行增量, 列增量)

# ---------------- 规则 ----------------
MISTAKES_PER_LEVEL = 3  # 每关失误次数
MIN_LENGTH, MAX_LENGTH = 1, 4  # 箭头长度（含身体）范围

# ---------------- 状态机 ----------------
STATE_START = "start"
STATE_PLAY = "play"
STATE_WIN = "win"
STATE_LOSE = "lose"
