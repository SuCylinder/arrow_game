# -*- coding: utf-8 -*-
"""全局配置：窗口、棋盘、颜色、方向与状态机常量。"""

# ---------------- 窗口 / 帧率 ----------------
WIDTH, HEIGHT = 640, 680  # 窗口尺寸
FPS = 60

# ---------------- 棋盘 ----------------
N = 5  # N×N 网格
CELL = 88  # 单格像素
GRID_W = CELL * N
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y = 150  # 棋盘左上角

# ---------------- 格子值 / 方向 ----------------
EMPTY, UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3, 4
DIRS = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}  # (行增量, 列增量)

# ---------------- 规则 ----------------
MISTAKES_PER_LEVEL = 3  # 每关失误次数
MIN_LENGTH, MAX_LENGTH = 1, 4  # 箭头长度（含身体）范围

# ---------------- 颜色 ----------------
BG = (24, 26, 38)
CELL_BG = (46, 51, 72)
CELL_LINE = (60, 66, 94)
TEXT = (232, 236, 248)
DIM = (150, 158, 184)
RED = (231, 76, 76)
BTN = (58, 64, 90)
BTN_HOVER = (78, 86, 120)
BTN_PRIMARY = (52, 120, 210)
BTN_PRIMARY_HOVER = (74, 146, 238)
BODY_DARKEN = 0.78  # 身体颜色压暗比例，用来区分头（亮）和身体（暗）
ARROW_COLORS = {
    UP: (92, 158, 255),
    DOWN: (88, 201, 129),
    LEFT: (247, 168, 71),
    RIGHT: (186, 122, 243),
}

# ---------------- 状态机 ----------------
STATE_START = "start"
STATE_PLAY = "play"
STATE_WIN = "win"
STATE_LOSE = "lose"
