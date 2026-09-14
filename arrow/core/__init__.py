# -*- coding: utf-8 -*-
"""纯逻辑层：箭头模型、盘面规则、生成/求解、评分、存档（不依赖 pygame）。"""

from arrow.core.logic import (
    Arrow,
    build_arrows,
    can_fly,
    count_arrows,
    fly_distance,
)
from arrow.core.scoring import format_time, score_for, stars_for
from arrow.core.solver import flyable_arrows, greedy_pick, solve_sequence
from arrow.core.utils import lerp_color

__all__ = [
    "Arrow",
    "build_arrows",
    "can_fly",
    "count_arrows",
    "fly_distance",
    "flyable_arrows",
    "greedy_pick",
    "solve_sequence",
    "stars_for",
    "score_for",
    "format_time",
    "lerp_color",
]
