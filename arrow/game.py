# -*- coding: utf-8 -*-
"""游戏主体：状态机、事件处理、动画更新与胜负判定。

界面绘制与按钮布局分别委托给 arrow.view.screens 和 arrow.view.button_layout；
draw() 与 _build_buttons() 保留为薄封装，方便外部和测试调用。
"""

import pygame

from arrow.config import (
    CELL,
    EMPTY,
    FPS,
    GRID_W,
    GRID_X,
    GRID_Y,
    HEIGHT,
    MISTAKES_PER_LEVEL,
    N,
    STATE_LOSE,
    STATE_PLAY,
    STATE_START,
    STATE_WIN,
    WIDTH,
)
from arrow.core.logic import build_arrows, can_fly, count_arrows
from arrow.levels import LEVELS
from arrow.view import button_layout, screens
from arrow.view.animations import FlyAnim, ShakeAnim
from arrow.view.ui import make_font


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("箭头消除")
        self.clock = pygame.time.Clock()

        self.font_title = make_font(60, bold=True)
        self.font_big = make_font(56, bold=True)
        self.font_hud = make_font(22)
        self.font_msg = make_font(22)
        self.font_btn = make_font(20)
        self.font_small = make_font(18)

        self.level_index = 0
        self.board = [[EMPTY] * N for _ in range(N)]
        self.arrows = []
        self.arrow_by_id = {}
        self.mistakes_left = MISTAKES_PER_LEVEL
        self.message = ""
        self.anims = []
        self.state = STATE_START
        self.buttons = []
        self._build_buttons()

    # ---------- 状态切换 ----------
    def _build_buttons(self):
        """按当前状态重建按钮列表（委托给 view.button_layout）。"""
        self.buttons = button_layout.build_buttons(self)

    def start_game(self):
        """从第 1 关开始新游戏。"""
        self.level_index = 0
        self.load_level()

    def to_start(self):
        self.state = STATE_START
        self.anims.clear()
        self._build_buttons()

    def next_level(self):
        if self.level_index + 1 >= len(LEVELS):
            return  # 已是最后一关，无下一关
        self.level_index += 1
        self.load_level()

    def restart_level(self):
        self.load_level()
        self.message = "已重开本关"

    def load_level(self):
        """载入当前关：按定义重建箭头、还原失误和动画。"""
        self.board, self.arrows = build_arrows(LEVELS[self.level_index])
        self.arrow_by_id = {a.id: a for a in self.arrows}
        self.mistakes_left = MISTAKES_PER_LEVEL
        self.anims.clear()
        self.state = STATE_PLAY
        self.message = f"第 {self.level_index + 1} 关：点箭头头部让它飞出去"
        self._build_buttons()

    # ---------- 核心逻辑 ----------
    def can_fly(self, r, c):
        """路径检测（转发到 logic.can_fly，便于外部按棋盘调用）。"""
        return can_fly(self.board, self.arrow_by_id, r, c)

    def pixel_to_cell(self, pos):
        """屏幕坐标 → 格子坐标，落在棋盘外返回 None。"""
        x, y = pos
        if not (GRID_X <= x < GRID_X + GRID_W and GRID_Y <= y < GRID_Y + GRID_W):
            return None
        return (y - GRID_Y) // CELL, (x - GRID_X) // CELL

    def try_click(self, r, c):
        """点击某个格子：空格提示、身体提示、头部可飞则滑出、被挡则碰撞扣失误。"""
        value = self.board[r][c]
        if value == EMPTY:
            self.message = f"({r}, {c}) 是空格子"
            return

        arrow = self.arrow_by_id[value]
        if any(a.arrow is arrow for a in self.anims):
            return  # 动画中的箭头锁住，防连点
        if (r, c) != arrow.head:
            self.message = "只能点箭头头部（身体点不动）"
            return
        if self.mistakes_left <= 0:
            return  # 失误已用完：等动画结束进失败界面

        if self.can_fly(r, c):
            self.anims.append(FlyAnim(arrow))
            self.message = "飞出去了！"
        else:
            self.anims.append(ShakeAnim(arrow))
            self.mistakes_left -= 1
            if self.mistakes_left > 0:
                self.message = f"被箭头挡住了，失误 -1（剩 {self.mistakes_left}）"
            else:
                self.message = "失误用完了……"

    # ---------- 事件 / 更新 ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.on_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_START:
                        return False  # 开始界面按 Esc 直接退出
                    self.to_start()
                elif event.key == pygame.K_r and self.state == STATE_PLAY:
                    self.restart_level()
        return True

    def on_click(self, pos):
        for btn in self.buttons:
            if btn.hit(pos):
                btn.callback()
                return
        if self.state == STATE_PLAY:
            cell = self.pixel_to_cell(pos)
            if cell is not None:
                self.try_click(*cell)

    def update(self, dt):
        # 推进动画
        for anim in self.anims:
            anim.update(dt)
        finished = [a for a in self.anims if a.done]
        for anim in finished:
            self.anims.remove(anim)
            if isinstance(anim, FlyAnim):  # 飞完了才把整支箭头从棋盘移除
                arrow = anim.arrow
                for r, c in arrow.cells:
                    self.board[r][c] = EMPTY
                arrow.alive = False

        # 动画全部结束、且还在游戏中时，判定胜负
        if self.state == STATE_PLAY and not self.anims:
            if count_arrows(self.arrows) == 0:
                self.state = STATE_WIN
                self._build_buttons()
            elif self.mistakes_left <= 0:
                self.state = STATE_LOSE
                self._build_buttons()

    # ---------- 绘制 ----------
    def draw(self):
        """按状态绘制界面（委托给 view.screens）。"""
        screens.draw(self, pygame.mouse.get_pos())

    # ---------- 主循环 ----------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
