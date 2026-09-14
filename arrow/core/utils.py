# -*- coding: utf-8 -*-
"""通用小工具：颜色计算。不依赖 pygame。"""


def lerp_color(c1, c2, t):
    """颜色线性插值，t 取 0~1。用 round 而非截断，保证 t=0/1 时精确等于端点色。"""
    t = max(0.0, min(1.0, t))
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))
