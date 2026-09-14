# -*- coding: utf-8 -*-
"""动画：箭头飞出（蛇形跟随）与碰撞（原地晃动变色）。"""

import math

from arrow.config import ARROW_COLORS, CELL, DIRS, GRID_X, GRID_Y, RED
from arrow.core.logic import fly_track
from arrow.core.utils import darken, lerp_color


class FlyAnim:
    """滑出动画：头部沿飞行方向滑出，身体逐格沿「头走过的路径」跟随。

    为整支箭头建一条轨道：尾巴延伸端 → 身体各格（尾→头）→ 头部前方射线。
    所有节点以同一弧长速度沿轨道滑动，相邻格间距恒为 1 格，因此弯折会
    从尾部开始逐节解开，头部先出界、尾巴最后离开，像蛇钻进洞口。
    """

    def __init__(self, arrow):
        self.arrow = arrow
        self.direction = arrow.direction
        points, self.total = fly_track(arrow)
        self.duration = 0.18 + 0.04 * self.total
        self.elapsed = 0.0
        self.done = False

        # 轨道末尾接一段出界射线（够长即可，按飞行方向线性外推）
        hr, hc = arrow.head
        dr, dc = DIRS[arrow.direction]
        end = (hr + dr * (self.total + 2), hc + dc * (self.total + 2))
        self.track = points + [end]

        # 弧长表：cum[k] 是 track[k] 距轨道起点的弧长
        self.cum = [0.0]
        for a, b in zip(self.track, self.track[1:]):
            self.cum.append(self.cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        # 各节点的初始弧长（尾巴延伸端 + 每个格子，尾→头）
        self.offsets = self.cum[: len(points)]

    def _at(self, u):
        """轨道上弧长为 u 处的网格坐标（线性插值）。"""
        if u <= 0.0:
            return self.track[0]
        for k in range(len(self.track) - 1):
            if u <= self.cum[k + 1]:
                a, b = self.track[k], self.track[k + 1]
                seg = self.cum[k + 1] - self.cum[k]
                t = (u - self.cum[k]) / seg if seg > 0 else 0.0
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        return self.track[-1]

    def update(self, dt):
        self.elapsed = min(self.elapsed + dt, self.duration)
        if self.elapsed >= self.duration:
            self.done = True

    def slide(self):
        """当前滑行弧长（格）：ease-out，先快后慢。"""
        p = self.elapsed / self.duration
        return self.total * (1 - (1 - p) ** 3)

    def nodes(self, s):
        """给定滑行弧长 s 时各节点的网格坐标（尾端延伸 → 尾 → 头），供测试与绘制使用。"""
        return [self._at(u + s) for u in self.offsets]

    def grid_points(self):
        """当前各节点的网格坐标（尾端延伸 → 各格尾→头）。"""
        return self.nodes(self.slide())

    def points(self):
        """当前各节点的像素坐标，头部在前（供 draw_arrow_polyline 使用）。"""
        return [
            (GRID_X + c * CELL + CELL * 0.5, GRID_Y + r * CELL + CELL * 0.5)
            for (r, c) in reversed(self.grid_points())
        ]

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
