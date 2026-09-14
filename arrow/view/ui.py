# -*- coding: utf-8 -*-
"""箭头绘制、面板/文字/背景等界面装饰工具。"""

import pygame
import pygame.gfxdraw

from arrow.config import (
    BG_BOTTOM,
    BG_TOP,
    CELL,
    DOWN,
    HEAD_SIZE,
    LEFT,
    PANEL,
    PANEL_LINE,
    SHADOW,
    UP,
)


def make_font(size, bold=False):
    """优先选带中文字形的字体，找不到再退回默认字体。"""
    names = "microsoftyahei,microsoftyaheiui,simhei,notosanscjksc,arialunicodems"
    try:
        return pygame.font.SysFont(names, size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)


def arrow_polygon(cx, cy, direction, size):
    """返回指向 direction 的三角形顶点列表（中心 cx,cy，中心到顶点 size 像素）。"""
    pts = [(0.0, -size), (size * 0.9, size * 0.72), (-size * 0.9, size * 0.72)]
    if direction == UP:
        rot = lambda x, y: (x, y)  # noqa: E731
    elif direction == DOWN:
        rot = lambda x, y: (-x, -y)  # noqa: E731
    elif direction == LEFT:
        rot = lambda x, y: (y, -x)  # noqa: E731
    else:
        rot = lambda x, y: (-y, x)  # noqa: E731
    return [(cx + rot(x, y)[0], cy + rot(x, y)[1]) for x, y in pts]


def draw_arrow_head(surface, cx, cy, direction, color, size=None, shadow=False):
    """在 (cx, cy) 处画一个指向 direction 的三角箭头。

    用 gfxdraw 的填充 + 抗锯齿描边，边缘平滑无毛刺；
    shadow=True 时先画一层向右下偏移的暗色投影，增加立体感。
    """
    if size is None:
        size = CELL * HEAD_SIZE
    poly = arrow_polygon(cx, cy, direction, size)
    if shadow:
        pygame.gfxdraw.filled_polygon(
            surface, [(x + 1.5, y + 2.5) for x, y in poly], SHADOW
        )
    pygame.gfxdraw.filled_polygon(surface, poly, color)
    pygame.gfxdraw.aapolygon(surface, poly, color)


def draw_panel(surface, rect, color=PANEL, alpha=235, line=PANEL_LINE, radius=12):
    """画一个圆角半透明面板（先铺底色再描 1px 边线）。"""
    rect = pygame.Rect(rect)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*color, alpha), panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, (*line, 255), panel.get_rect(), 1, border_radius=radius)
    surface.blit(panel, rect.topleft)


def draw_text_shadowed(surface, font, text, color, center=None, midleft=None,
                       offset=2):
    """带右下投影的文字（先画暗色副本再画正文）。返回正文的矩形。"""
    shade = font.render(text, True, SHADOW)
    body = font.render(text, True, color)
    rect = body.get_rect(center=center) if center is not None \
        else body.get_rect(midleft=midleft)
    surface.blit(shade, rect.move(offset, offset))
    surface.blit(body, rect)
    return rect


_bg_cache = {}


def make_gradient_bg(size):
    """垂直渐变背景，按尺寸缓存（只在首次调用时逐行生成）。"""
    if size not in _bg_cache:
        w, h = size
        surf = pygame.Surface(size)
        for y in range(h):
            t = y / max(1, h - 1)
            color = tuple(
                round(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)
            )
            pygame.draw.line(surf, color, (0, y), (w, y))
        _bg_cache[size] = surf
    return _bg_cache[size]
