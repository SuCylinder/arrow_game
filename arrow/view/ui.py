# -*- coding: utf-8 -*-
"""箭头绘制与字体工具。"""

import pygame

from arrow.config import BODY_R, BODY_W, CELL, DOWN, HEAD_SIZE, LEFT, TAIL_EXT, UP


def make_font(size, bold=False):
    """优先选带中文字形的字体，找不到再退回默认字体。"""
    names = "microsoftyahei,microsoftyaheiui,simhei,notosanscjksc,arialunicodems"
    try:
        return pygame.font.SysFont(names, size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)


def draw_arrow_head(surface, cx, cy, direction, color):
    """在 (cx, cy) 处画一个指向 direction 的三角箭头（头部）。"""
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
    pygame.draw.polygon(surface, color, poly)


def draw_arrow_polyline(surface, pts, direction, color, body_color):
    """按像素点列画一支箭头：pts[0] 是头部中心，之后依次是身体与尾端延伸。

    几何约定：身体用各节点连成的粗折线画出（半宽 BODY_R 格，比头部三角形
    底座略窄，这样能看出箭头尖）；每个折点画同色圆做圆角；
    头部三角形最后叠上。pts 只有一个点时只画头部（单格箭头）。
    """
    if len(pts) > 1:
        width = int(CELL * BODY_W)  # 直径 = 2 × BODY_R 格
        radius = int(CELL * BODY_R)
        for k in range(len(pts) - 1):
            pygame.draw.line(surface, body_color, pts[k], pts[k + 1], width)
        for p in pts:
            pygame.draw.circle(surface, body_color, (int(p[0]), int(p[1])), radius)
    draw_arrow_head(surface, pts[0][0], pts[0][1], direction, color)


def draw_arrow_full(surface, head_cx, head_cy, arrow, color, body_color):
    """按箭头静止时的形状画：把头中心与各格错开 (c-hc, r-hr) 格即可。"""
    hr, hc = arrow.head
    pts = [
        (head_cx + (c - hc) * CELL, head_cy + (r - hr) * CELL)
        for (r, c) in arrow.cells
    ]
    if arrow.length > 1:
        # 尾巴沿最后一段方向再冒 0.56 格（盖住格缝）
        dr = arrow.cells[-1][0] - arrow.cells[-2][0]
        dc = arrow.cells[-1][1] - arrow.cells[-2][1]
        pts.append((pts[-1][0] + dc * CELL * TAIL_EXT,
                    pts[-1][1] + dr * CELL * TAIL_EXT))
    draw_arrow_polyline(surface, pts, arrow.direction, color, body_color)
