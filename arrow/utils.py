# -*- coding: utf-8 -*-
"""通用小工具：颜色计算。不依赖 pygame。"""

from arrow.config import BODY_DARKEN


def darken(color, factor=BODY_DARKEN):
    """把颜色压暗，用来画身体（和头部区分）。"""
    return tuple(int(v * factor) for v in color)


def lerp_color(c1, c2, t):
    """颜色线性插值，t 取 0~1。"""
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
