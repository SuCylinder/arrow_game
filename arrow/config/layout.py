# -*- coding: utf-8 -*-
"""窗口、棋盘、字体与界面锚点常量。

界面锚点（HUD_PANEL / RESULT_* 等）由绘制代码与测试共同引用，
调整分辨率时只需修改本文件。
"""

# ---------------- 窗口 / 帧率 ----------------
WIDTH, HEIGHT = 740, 780
FPS = 60

# ---------------- 棋盘 ----------------
N = 5  # N×N 网格
CELL = 100  # 单格像素
GRID_W = CELL * N
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y = 172  # 棋盘左上角

# ---------------- 箭头几何（单位：格） ----------------
HEAD_SIZE = 0.30  # 头部三角：中心到顶点
HEAD_BASE = 0.72 * HEAD_SIZE  # 头部三角：中心到底边
FLY_MARGIN = 0.04  # 飞出动画的安全余量

# ---------------- 字体大小 ----------------
FONT_TITLE = 68
FONT_BIG = 63
FONT_STAR = 35
FONT_HUD = 25
FONT_MSG = 25
FONT_BTN = 22
FONT_SMALL = 21

# ---------------- 界面锚点 ----------------
HUD_PANEL = (18, 16, 430, 53)   # 顶部 HUD 面板（右缘须与右上按钮留出间隙）
HUD_TEXT_Y = 42                 # HUD 文字 / 圆点中线
HUD_TEXT_X = (35, 163, 300)     # 关卡 / 剩余箭头 / 剩余失误的左边 x
HUD_DOT_X = 404                 # 失误圆点起点
HUD_DOT_STEP = 13               # 失误圆点间距
HUD_DOT_R = 6                   # 失误圆点半径
HUD_PANEL_AI_H = 80             # AI 演示时 HUD 面板高度（多一行标签；下缘与胶囊留隙）
HUD_AI_TAG_POS = (35, 77)       # AI 演示标签中线（midleft，仅 AI 演示时显示的 HUD 第二行）
MSG_Y = 128                     # 提示胶囊中线
TIMER_POS = (413, 726)          # 底栏计时（midleft）
BOTTOM_BAR_Y = 703              # 底栏按钮顶部 y
START_TITLE_Y = 178             # 开始界面标题中线
START_DECO_Y = 247              # 开始界面装饰箭头中线
START_DECO_GAP = 53             # 装饰箭头间距
START_DECO_SIZE = 23            # 装饰箭头大小（中心到顶点）
START_RULES_CENTER = (WIDTH // 2, 392)  # 规则面板中心（与上下元素留出间隙）
START_PROGRESS_Y = 684          # 开始界面底部存档进度摘要中线
SELECT_TITLE_Y = 128            # 选择界面标题中线
SELECT_SUB_Y = 180              # 选择界面副标题中线
RESULT_PANEL = (126, 180, 482, 268)     # 结果界面面板（下缘须容下三星提示行）
RESULT_BADGE_Y = 236            # 徽章中心 y
RESULT_BADGE_R = 39             # 徽章外圈半径（测试探针用 R-4）
RESULT_TITLE_Y = 311            # 结果标题中线
RESULT_STARS_Y = 362            # 星级中线
RESULT_SCORE_Y = 398            # 得分/用时中线
RESULT_HINT_Y = 425             # 三星提示中线
RESULT_SUB_Y = 377              # 失败说明中线
RESULT_NOTE_Y = 364             # AI 演示说明中线

# ---------------- 关卡选择界面 ----------------
SELECT_COLS = 3        # 卡片列数
SELECT_CARD_W = 179    # 卡片宽
SELECT_CARD_H = 148    # 卡片高
SELECT_GAP_X = 25      # 卡片水平间距
SELECT_GAP_Y = 32      # 卡片垂直间距
SELECT_TOP = 224       # 第一行卡片顶部 y
