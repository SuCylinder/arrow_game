# -*- coding: utf-8 -*-
"""评分与计时格式化。不依赖 pygame。"""

from arrow.config import (
    SCORE_PER_ARROW,
    SCORE_PER_MISTAKE,
    TIME_BONUS_MAX,
    TIME_BONUS_SECONDS,
)


def stars_for(mistakes_left):
    """剩余失误 → 星级：满失误 3 星，掉 1 次 2 星，其余 1 星。"""
    if mistakes_left >= 3:
        return 3
    if mistakes_left == 2:
        return 2
    return 1


def score_for(arrow_total, mistakes_left, seconds):
    """得分 = 箭头数×基础分 + 剩余失误奖励 + 时间奖励。

    时间奖励从 TIME_BONUS_MAX 起、随用时线性递减，到 TIME_BONUS_SECONDS
    时恰好降为 0，之后保持 0（不会因为拖更久而反向变高）。
    """
    base = arrow_total * SCORE_PER_ARROW + mistakes_left * SCORE_PER_MISTAKE
    t = min(1.0, max(0.0, seconds / TIME_BONUS_SECONDS))
    bonus = round(TIME_BONUS_MAX * (1 - t))
    return base + bonus


def format_time(seconds):
    """秒数 → "MM:SS"（超过 99 分钟按实际分钟数显示）。"""
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
