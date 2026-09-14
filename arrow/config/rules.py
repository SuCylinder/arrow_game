# -*- coding: utf-8 -*-
"""游戏规则常量：格子值、方向、胜负状态。"""

# ---------------- 格子值 / 方向 ----------------
EMPTY, UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3, 4
DIRS = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}  # (行增量, 列增量)

# ---------------- 规则 ----------------
MISTAKES_PER_LEVEL = 3  # 每关失误次数

# ---------------- 随机生成 ----------------
RANDOM_ARROW_COUNT = (8, 14)  # 随机挑战：箭头支数范围
MAX_UNLOCKED_LEVEL = 6        # 总关卡数（与 arrow.levels.LEVELS 长度一致）

# ---------------- 评分 / 计时 ----------------
HINT_SECONDS = 1.6      # 提示光环持续时间
AI_STEP_SECONDS = 0.45  # AI 演示每步间隔
TIME_BONUS_MAX = 600      # 时间奖励满分（0 秒时）
TIME_PENALTY_PER_SEC = 5  # 时间奖励每秒衰减；600 / 5 = 120 秒后归零
TIME_BONUS_SECONDS = TIME_BONUS_MAX // TIME_PENALTY_PER_SEC  # 奖励归零点
SCORE_PER_ARROW = 100     # 每支箭头基础分
SCORE_PER_MISTAKE = 200   # 每点剩余失误的奖励分

# ---------------- 状态机 ----------------
STATE_START = "start"
STATE_SELECT = "select"
STATE_PLAY = "play"
STATE_WIN = "win"
STATE_LOSE = "lose"
