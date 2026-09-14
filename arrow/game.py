# -*- coding: utf-8 -*-
"""游戏主体：状态机、事件处理、动画更新与胜负判定。

界面绘制与按钮布局分别委托给 arrow.view.screens 和 arrow.view.button_layout；
draw() 与 _build_buttons() 保留为薄封装，方便外部和测试调用。

扩展功能：
  计时 / 撤销成功步 / 提示可飞箭头 / AI 自动演示 / 随机关卡 / 存档与关卡选择。
"""

import random

import pygame
import pygame.gfxdraw

from arrow.config import (
    AI_STEP_SECONDS,
    ARROW_COLORS,
    CELL,
    EMPTY,
    FONT_BIG,
    FONT_BTN,
    FONT_HUD,
    FONT_MSG,
    FONT_SMALL,
    FONT_STAR,
    FONT_TITLE,
    FPS,
    GRID_W,
    GRID_X,
    GRID_Y,
    HEIGHT,
    HINT_SECONDS,
    MISTAKES_PER_LEVEL,
    N,
    RIGHT,
    STATE_LOSE,
    STATE_PLAY,
    STATE_SELECT,
    STATE_START,
    STATE_WIN,
    WIDTH,
)
from arrow.core import save as save_mod
from arrow.core.generator import generate_level
from arrow.core.logic import build_arrows, can_fly, count_arrows
from arrow.core.scoring import score_for, stars_for
from arrow.core.solver import greedy_pick
from arrow.levels import LEVELS
from arrow.view import button_layout, screens
from arrow.view.animations import FlyAnim, ShakeAnim
from arrow.view.ui import arrow_polygon, make_font


class Game:
    def __init__(self, save_path=None):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("箭头消除")
        self.clock = pygame.time.Clock()
        self._set_icon()

        self.font_title = make_font(FONT_TITLE, bold=True)
        self.font_big = make_font(FONT_BIG, bold=True)
        self.font_hud = make_font(FONT_HUD)
        self.font_msg = make_font(FONT_MSG)
        self.font_btn = make_font(FONT_BTN)
        self.font_small = make_font(FONT_SMALL)
        self.font_star = make_font(FONT_STAR)

        self.save_path = save_path
        self.progress = save_mod.load(save_path)

        self.level_index = 0
        self.random_defs = None      # 随机挑战的箭头定义；普通关卡为 None
        self.board = [[EMPTY] * N for _ in range(N)]
        self.arrows = []
        self.arrow_by_id = {}
        self.mistakes_left = MISTAKES_PER_LEVEL
        self.message = ""
        self.anims = []
        self.state = STATE_START
        self.buttons = []

        self.elapsed = 0.0           # 本关用时（秒）
        self.undo_stack = []         # 已成功飞出的箭头
        self.hint_cell = None        # 提示高亮格
        self.hint_timer = 0.0
        self.ai_mode = False         # AI 演示开关
        self.ai_timer = 0.0
        self.ai_used = False         # 本关是否用过 AI（用过则不计成绩）
        self.result = None           # 结算数据 {stars, score, time, best}

        self._build_buttons()

    # ---------- 状态切换 ----------
    def _set_icon(self):
        """画一支青色向右的箭头作为窗口图标（headless 环境下失败则跳过）。"""
        try:
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            poly = arrow_polygon(16, 16, RIGHT, 13)
            pygame.gfxdraw.filled_polygon(icon, poly, ARROW_COLORS[RIGHT])
            pygame.gfxdraw.aapolygon(icon, poly, ARROW_COLORS[RIGHT])
            pygame.display.set_icon(icon)
        except Exception:
            pass

    def _build_buttons(self):
        """按当前状态重建按钮列表（委托给 view.button_layout）。"""
        self.buttons = button_layout.build_buttons(self)

    def start_game(self):
        """从第 1 关开始新游戏。"""
        self.level_index = 0
        self.random_defs = None
        self.load_level()

    def to_start(self):
        self.state = STATE_START
        self.anims.clear()
        self.hint_cell = None
        self._build_buttons()

    def to_select(self):
        """进入关卡选择界面（按存档显示解锁状态与星级）。"""
        self.state = STATE_SELECT
        self.anims.clear()
        self._build_buttons()

    def select_level(self, index):
        """从关卡选择界面进入指定关（未解锁则忽略）。"""
        if not (0 <= index < len(LEVELS)) or index >= self.unlocked_count():
            return
        self.level_index = index
        self.random_defs = None
        self.load_level()

    def unlocked_count(self):
        """已解锁关卡数（1 起，受存档与总关卡数限制）。"""
        return max(1, min(self.progress.get("unlocked", 1), len(LEVELS)))

    def has_progress(self):
        """存档里是否有进度（解锁超过第 1 关或已有最好成绩）。"""
        return self.unlocked_count() > 1 or bool(self.progress.get("best"))

    def continue_level(self):
        """继续游戏：进入存档中已解锁的最后一关（无进度则从第 1 关开始）。"""
        self.level_index = self.unlocked_count() - 1
        self.random_defs = None
        self.load_level()

    def total_stars(self):
        """存档中各关星级之和（用于开始界面进度摘要）。"""
        return sum(
            min(3, max(0, v.get("stars", 0)))
            for v in self.progress.get("best", {}).values()
        )

    def random_level(self):
        """生成一关随机关卡（不写入存档，通关按钮为「换一关」）。"""
        self.random_defs = generate_level()
        self.load_level()
        self.message = "随机挑战：点箭头让它飞出去"

    def next_level(self):
        if self.level_index + 1 >= len(LEVELS):
            return  # 已是最后一关，无下一关
        self.level_index += 1
        self.random_defs = None
        self.load_level()

    def restart_level(self):
        self.load_level()
        self.message = "已重开本关"

    def load_level(self):
        """载入当前关：按定义重建箭头、还原失误/撤销/提示/计时与动画。"""
        defs = self.random_defs if self.random_defs is not None \
            else LEVELS[self.level_index]
        self.board, self.arrows = build_arrows(defs)
        self.arrow_by_id = {a.id: a for a in self.arrows}
        self.mistakes_left = MISTAKES_PER_LEVEL
        self.anims.clear()
        self.elapsed = 0.0
        self.undo_stack = []
        self.hint_cell = None
        self.hint_timer = 0.0
        self.ai_mode = False
        self.ai_timer = 0.0
        self.ai_used = False
        self.result = None
        self.state = STATE_PLAY
        if self.random_defs is None:
            self.message = f"第 {self.level_index + 1} 关：点箭头让它飞出去"
        self._build_buttons()

    def is_random(self):
        return self.random_defs is not None

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
        """点击某个格子：空格提示、可飞则滑出、被挡则碰撞扣失误。"""
        if self.ai_mode:
            return  # AI 演示期间屏蔽手动点击
        value = self.board[r][c]
        if value == EMPTY:
            self.message = f"({r}, {c}) 是空格子"
            return

        arrow = self.arrow_by_id[value]
        if any(a.arrow is arrow for a in self.anims):
            return  # 动画中的箭头锁住，防连点
        if self.mistakes_left <= 0:
            return  # 失误已用完：等动画结束进失败界面

        self.hint_cell = None  # 操作过就清掉提示
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

    # ---------- 扩展功能 ----------
    def show_hint(self):
        """高亮一支可飞的箭头（免费不限次，1.6 秒后自动消失）。"""
        if self.state != STATE_PLAY or self.anims or self.ai_mode:
            return
        pick = greedy_pick(self.board, self.arrows, self.arrow_by_id)
        if pick is None:
            self.message = "没有可飞的箭头了"
            return
        self.hint_cell = pick.head
        self.hint_timer = HINT_SECONDS
        self.message = "提示：高亮的箭头可以飞出去"

    def undo(self):
        """撤销上一步成功飞出的箭头（不限次，只退成功步）。"""
        if self.state != STATE_PLAY or self.ai_mode:
            return
        if self.anims:
            self.message = "等动画结束再撤销"
            return
        if not self.undo_stack:
            self.message = "没有可以撤销的步骤"
            return
        arrow = self.undo_stack.pop()
        arrow.alive = True
        self.board[arrow.head[0]][arrow.head[1]] = arrow.id
        self.hint_cell = None
        self.message = f"已撤销 ({arrow.head[0]}, {arrow.head[1]}) 的飞出"

    def toggle_ai(self):
        """AI 演示开关：开启后按贪心策略自动通关。"""
        if self.state != STATE_PLAY:
            return
        self.ai_mode = not self.ai_mode
        self.ai_timer = 0.0
        self.hint_cell = None
        self.message = "AI 演示中……点击「停止 AI」可接管" if self.ai_mode \
            else "已停止 AI 演示"
        self._build_buttons()

    def _ai_step(self):
        """AI 走一步：优先编号最大的可飞箭头（必胜策略）。"""
        if self.anims:
            return
        pick = greedy_pick(self.board, self.arrows, self.arrow_by_id)
        if pick is None:
            self.ai_mode = False
            self._build_buttons()
            return
        arrow = pick
        self.anims.append(FlyAnim(arrow))
        self.ai_used = True  # 真正走步后才标记（误开开关不影响成绩）
        self.message = "AI 出手！"
    # ---------- 结算 ----------
    def _finish_win(self):
        """通关结算：评星、计分、更新存档与下一关解锁。"""
        total = len(self.arrows)
        stars = stars_for(self.mistakes_left)
        score = score_for(total, self.mistakes_left, self.elapsed)
        best = None
        saved = False
        new_record = False
        if self.is_random():
            self.message = "随机挑战完成！"
        elif self.ai_used:
            self.message = "AI 演示完成（不计入成绩）"
        else:
            key = str(self.level_index + 1)
            best = self.progress["best"].get(key)
            new_record = (best is None or score > best["score"])
            if new_record:
                self.progress["best"][key] = {
                    "stars": stars, "score": score, "time": self.elapsed,
                }
                best = self.progress["best"][key]
            if self.level_index + 1 >= self.progress.get("unlocked", 1):
                self.progress["unlocked"] = min(
                    self.level_index + 2, len(LEVELS)
                )
            saved = save_mod.store(self.progress, self.save_path)
        self.result = {
            "stars": stars, "score": score, "time": self.elapsed,
            "best": best, "random": self.is_random(), "ai": self.ai_used,
            "saved": saved, "new_record": new_record,
        }
        self.ai_mode = False
        self.state = STATE_WIN
        self._build_buttons()

    def _finish_lose(self):
        self.result = {
            "stars": 0, "score": 0, "time": self.elapsed,
            "best": None, "random": self.is_random(), "ai": self.ai_used,
        }
        self.ai_mode = False
        self.state = STATE_LOSE
        self._build_buttons()

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
                    if self.state == STATE_SELECT:
                        self.to_start()
                    else:
                        self.to_start()
                elif event.key == pygame.K_r and self.state == STATE_PLAY:
                    self.restart_level()
                elif event.key == pygame.K_h and self.state == STATE_PLAY:
                    self.show_hint()
                elif event.key == pygame.K_z and self.state == STATE_PLAY:
                    self.undo()
        return True

    def on_click(self, pos):
        for btn in self.buttons:
            if btn.hit(pos):
                btn.callback()
                return
        if self.state == STATE_SELECT:
            for i, rect in enumerate(button_layout.level_card_rects()):
                if rect.collidepoint(pos) and i < self.unlocked_count():
                    self.select_level(i)
                    return
        if self.state == STATE_PLAY:
            cell = self.pixel_to_cell(pos)
            if cell is not None:
                self.try_click(*cell)

    def update(self, dt):
        # 计时（只在可操作的游戏进行中累积）
        if self.state == STATE_PLAY and self.mistakes_left > 0:
            self.elapsed += dt

        # 提示光环倒计时
        if self.hint_timer > 0:
            self.hint_timer = max(0.0, self.hint_timer - dt)
            if self.hint_timer == 0:
                self.hint_cell = None

        # AI 演示：按固定间隔自动走一步
        if self.state == STATE_PLAY and self.ai_mode:
            self.ai_timer += dt
            if self.ai_timer >= AI_STEP_SECONDS:
                self.ai_timer = 0.0
                self._ai_step()

        # 推进动画
        for anim in self.anims:
            anim.update(dt)
        finished = [a for a in self.anims if a.done]
        for anim in finished:
            self.anims.remove(anim)
            if isinstance(anim, FlyAnim):  # 飞完了才把箭头从棋盘移除
                arrow = anim.arrow
                self.board[arrow.head[0]][arrow.head[1]] = EMPTY
                arrow.alive = False
                if not self.ai_mode:  # AI 演示不记入撤销栈
                    self.undo_stack.append(arrow)

        # 动画全部结束、且还在游戏中时，判定胜负
        if self.state == STATE_PLAY and not self.anims:
            if count_arrows(self.arrows) == 0:
                self._finish_win()
            elif self.mistakes_left <= 0:
                self._finish_lose()

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
