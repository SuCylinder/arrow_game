# -*- coding: utf-8 -*-
"""箭头绘制与字体工具。"""

import pygame
import pygame.gfxdraw

from arrow.config import CELL, DOWN, HEAD_SIZE, LEFT, UP


def make_font(size, bold=False):
    """优先选带中文字形的字体，找不到再退回默认字体。"""
    names = "microsoftyahei,microsoftyaheiui,simhei,notosanscjksc,arialunicodems"
    try:
        return pygame.font.SysFont(names, size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)


def draw_arrow_head(surface, cx, cy, direction, color):
    """在 (cx, cy) 处画一个指向 direction 的三角箭头。

    用 gfxdraw 的填充 + 抗锯齿描边，边缘平滑无毛刺。
    """
    s = CELL * HEAD_SIZE
    pts = [(0.0, -s), (s * 0.9, s * 0.72), (-s * 0.9, s * 0.72)]  # 基础形状朝上
    if direction == UP:
        rot = lambda x, y: (x, y)  # noqa: E731
    elif direction == DOWN:
        rot = lambda x, y: (-x, -y)  # noqa: E731
    elif direction == LEFT:
        rot = lambda x, y: (y, -x)  # noqa: E731
    else:
        rot = lambda x, y: (-y, x)  # noqa: E731
    poly = [(cx + rot(x, y)[0], cy + rot(x, y)[1]) for x, y in pts]
    pygame.gfxdraw.filled_polygon(surface, poly, color)
    pygame.gfxdraw.aapolygon(surface, poly, color)
