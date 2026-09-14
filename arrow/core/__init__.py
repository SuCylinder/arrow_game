# -*- coding: utf-8 -*-
"""纯逻辑层：箭头模型、盘面规则、颜色工具（不依赖 pygame）。"""

from arrow.core.logic import (
    Arrow,
    build_arrows,
    can_fly,
    count_arrows,
    fly_track,
)
from arrow.core.utils import darken, lerp_color

__all__ = [
    "Arrow",
    "build_arrows",
    "can_fly",
    "count_arrows",
    "fly_track",
    "darken",
    "lerp_color",
]
