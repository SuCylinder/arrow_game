# -*- coding: utf-8 -*-
"""箭头绘制与字体工具。"""

import pygame

from arrow.config import CELL, DIRS, DOWN, LEFT, UP


def make_font(size, bold=False):
    """优先选带中文字形的字体，找不到再退回默认字体。"""
    names = "microsoftyahei,microsoftyaheiui,simhei,notosanscjksc,arialunicodems"
    try:
        return pygame.font.SysFont(names, size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)


def draw_arrow_head(surface, cx, cy, direction, color):
    """在 (cx, cy) 处画一个指向 direction 的三角箭头（头部）。"""
    s = CELL * 0.30
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
    pygame.draw.polygon(surface, color, poly)


def draw_arrow_full(surface, head_cx, head_cy, direction, length, color, body_color):
    """画一支完整箭头：长度 ≥2 先画身体长条，再叠上头部三角形。

    几何约定（都相对头中心）：
      身体从头中心向后延伸到「尾巴格的远边缘」再多冒 0.06 格（盖住格子
      之间约 6px 的缝隙），即总长 (length-1) + 0.56 格；身体半宽 0.22 格，
      比头部三角形底座（0.27 格）略窄，这样能看出箭头尖。
    """
    if length > 1:
        dr, dc = DIRS[direction]
        ax, ay = dc, dr  # 屏幕坐标下的前进方向（x, y）
        bx, by = -ax, -ay  # 反方向（身体延伸的方向）
        tail_cx = head_cx + bx * (length - 1) * CELL
        tail_cy = head_cy + by * (length - 1) * CELL
        end_cx = tail_cx + bx * CELL * 0.56
        end_cy = tail_cy + by * CELL * 0.56
        px, py = -by, bx  # 身体宽度方向（与前进方向垂直）
        half = CELL * 0.22
        corners = [
            (head_cx + px * half, head_cy + py * half),
            (head_cx - px * half, head_cy - py * half),
            (end_cx - px * half, end_cy - py * half),
            (end_cx + px * half, end_cy + py * half),
        ]
        pygame.draw.polygon(surface, body_color, corners)
    draw_arrow_head(surface, head_cx, head_cy, direction, color)
