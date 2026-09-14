# -*- coding: utf-8 -*-
"""动画：箭头飞出（滑出棋盘）与碰撞（原地晃动变色）。"""

import math

from arrow.config import ARROW_COLORS, CELL, DIRS, RED
from arrow.core.utils import darken, lerp_color


class FlyAnim:
    """滑出动画：整支箭头（头+身体）一起沿方向滑出棋盘。"""

    def __init__(self, arrow, distance):
        self.arrow = arrow
        self.r, self.c = arrow.head
        self.direction = arrow.direction
        self.distance = distance  # 需要滑出的格数（含安全余量）
        self.elapsed = 0.0
        dr, dc = DIRS[arrow.direction]
        self.axis = (dc, dr)  # 像素偏移方向（x, y）
        self.duration = 0.18 + 0.04 * distance
        self.offset = (0.0, 0.0)  # 像素偏移
        self.done = False

    def update(self, dt):
        self.elapsed = min(self.elapsed + dt, self.duration)
        p = self.elapsed / self.duration
        ease = 1 - (1 - p) ** 3  # ease-out，先快后慢
        d = self.distance * ease * CELL
        self.offset = (self.axis[0] * d, self.axis[1] * d)
        if p >= 1.0:
            self.done = True

    def head_color(self):
        return ARROW_COLORS[self.direction]

    def body_color(self):
        return darken(ARROW_COLORS[self.direction])


class ShakeAnim:
    """碰撞动画：整支箭头原地晃动，颜色脉冲变红，结束后回到原样。"""

    def __init__(self, arrow):
        self.arrow = arrow
        self.r, self.c = arrow.head
        self.direction = arrow.direction
        self.duration = 0.5
        self.elapsed = 0.0
        dr, dc = DIRS[arrow.direction]
        self.axis = (dc, dr)
        self.offset = (0.0, 0.0)
        self.done = False
        self.mix = 0.0

    def update(self, dt):
        self.elapsed = min(self.elapsed + dt, self.duration)
        p = self.elapsed / self.duration
        amp = math.sin(self.elapsed * 34) * 8 * (1 - p)  # 振幅随时间衰减
        self.offset = (self.axis[0] * amp, self.axis[1] * amp)
        self.mix = math.sin(math.pi * p)  # 0 → 1 → 0 的脉冲
        if p >= 1.0:
            self.done = True

    def head_color(self):
        return lerp_color(ARROW_COLORS[self.direction], RED, self.mix)

    def body_color(self):
        return darken(self.head_color())
