# -*- coding: utf-8 -*-
"""颜色表。"""

from arrow.config.rules import DOWN, LEFT, RIGHT, UP

# ---------------- 颜色 ----------------
BG = (24, 26, 38)
BG_TOP = (28, 31, 46)      # 背景渐变（顶部）
BG_BOTTOM = (20, 22, 32)   # 背景渐变（底部）
CELL_BG = (46, 51, 72)
CELL_LINE = (60, 66, 94)
TEXT = (232, 236, 248)
DIM = (150, 158, 184)
RED = (231, 76, 76)
GREEN = (88, 201, 129)     # 通关图标 / 星级
GOLD = (247, 200, 92)      # 星级金星
HINT = (255, 236, 150)     # 提示光环
BTN = (58, 64, 90)
BTN_HOVER = (78, 86, 120)
BTN_PRIMARY = (52, 120, 210)
BTN_PRIMARY_HOVER = (74, 146, 238)
BTN_LINE = (44, 49, 70)            # 按钮描边（比底色略深，内嵌质感）
BTN_PRIMARY_LINE = (34, 88, 160)   # 主按钮描边（比底色略深）
PANEL = (34, 38, 56)               # 面板底色（配 alpha 使用）
PANEL_LINE = (62, 70, 100)         # 面板描边
PILL = (48, 54, 78)                # 提示胶囊底色
SHADOW = (12, 13, 20)              # 投影颜色
GRID_FRAME = (30, 33, 48)          # 棋盘外框
ARROW_COLORS = {
    UP: (92, 158, 255),
    DOWN: (88, 201, 129),
    LEFT: (247, 168, 71),
    RIGHT: (186, 122, 243),
}
