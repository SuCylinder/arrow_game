# -*- coding: utf-8 -*-
"""游戏主体：状态机、事件处理、更新与渲染编排。"""

import pygame

from arrow.animations import FlyAnim, ShakeAnim
from arrow.button import Button
from arrow.config import (
    ARROW_COLORS,
    BG,
    CELL,
    CELL_BG,
    CELL_LINE,
    DIM,
    EMPTY,
    FPS,
    GRID_W,
    GRID_X,
    GRID_Y,
    HEIGHT,
    MISTAKES_PER_LEVEL,
    N,
    RED,
    STATE_LOSE,
    STATE_PLAY,
    STATE_START,
    STATE_WIN,
    TEXT,
    WIDTH,
)
from arrow.levels import LEVELS
from arrow.logic import build_arrows, can_fly, count_arrows, fly_distance
from arrow.ui import draw_arrow_full, make_font
from arrow.utils import darken


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
        """按当前状态重建按钮列表。"""
        self.buttons = []
        if self.state == STATE_START:
            self.buttons.append(
                Button(
                    (WIDTH // 2 - 90, 430, 180, 52),
                    "开始游戏",
                    self.start_game,
                    primary=True,
                )
            )
        elif self.state == STATE_PLAY:
            self.buttons.append(
                Button(
                    (WIDTH - 140, 18, 116, 38),
                    "重开本关",
                    self.restart_level,
                    primary=True,
                )
            )
            self.buttons.append(Button((WIDTH - 226, 18, 78, 38), "返回", self.to_start))
        elif self.state == STATE_WIN:
            if self.level_index + 1 < len(LEVELS):
                self.buttons.append(
                    Button(
                        (WIDTH // 2 + 8, 430, 180, 52),
                        "下一关",
                        self.next_level,
                        primary=True,
                    )
                )
            else:
                self.buttons.append(
                    Button(
                        (WIDTH // 2 + 8, 430, 180, 52),
                        "回开始",
                        self.to_start,
                        primary=True,
                    )
                )
            self.buttons.append(
                Button((WIDTH // 2 - 188, 430, 180, 52), "重开本关", self.restart_level)
            )
        elif self.state == STATE_LOSE:
            self.buttons.append(
                Button(
                    (WIDTH // 2 + 8, 430, 180, 52),
                    "重开本关",
                    self.restart_level,
                    primary=True,
                )
            )
            self.buttons.append(
                Button((WIDTH // 2 - 188, 430, 180, 52), "回开始", self.to_start)
            )

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

    def fly_distance(self, arrow):
        """滑出动画的位移（格数）。"""
        return fly_distance(arrow)

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
            self.anims.append(FlyAnim(arrow, self.fly_distance(arrow)))
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
        self.screen.fill(BG)
        mouse_pos = pygame.mouse.get_pos()
        if self.state == STATE_START:
            self.draw_start(mouse_pos)
        elif self.state == STATE_PLAY:
            self.draw_play(mouse_pos)
        elif self.state == STATE_WIN:
            self.draw_result(
                mouse_pos,
                (
                    "全部通关！"
                    if self.level_index + 1 >= len(LEVELS)
                    else f"第 {self.level_index + 1} 关通关！"
                ),
                (
                    "点击「下一关」继续挑战"
                    if self.level_index + 1 < len(LEVELS)
                    else "你已经清空了所有关卡"
                ),
            )
        else:
            self.draw_result(
                mouse_pos,
                "游戏失败",
                f"第 {self.level_index + 1} 关失误用完了，重来一次吧",
            )

    def draw_start(self, mouse_pos):
        title = self.font_title.render("箭头消除", True, TEXT)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 170)))
        rules = [
            "点击箭头头部：它指向的方向到边界之间没有其它箭头，就会飞出去",
            "被挡住则算碰撞：箭头不动，失误 -1",
            "箭头有身体（1~4 格），只有头部能点，身体同样会挡路",
            "清空全部箭头过关，失误用完失败",
        ]
        for i, line in enumerate(rules):
            text = self.font_msg.render(line, True, DIM)
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 268 + i * 38)))
        for btn in self.buttons:
            btn.draw(self.screen, self.font_btn, mouse_pos)

    def draw_play(self, mouse_pos):
        # HUD：关卡 / 剩余箭头 / 剩余失误
        hud = self.font_hud.render(
            f"第 {self.level_index + 1} / {len(LEVELS)} 关", True, TEXT
        )
        self.screen.blit(hud, hud.get_rect(midleft=(24, 37)))
        arrows = self.font_hud.render(f"剩余箭头 {count_arrows(self.arrows)}", True, TEXT)
        self.screen.blit(arrows, arrows.get_rect(midleft=(170, 37)))
        color = RED if self.mistakes_left <= 1 else TEXT
        mistakes = self.font_hud.render(f"剩余失误 {self.mistakes_left}", True, color)
        self.screen.blit(mistakes, mistakes.get_rect(midleft=(300, 37)))

        for btn in self.buttons:
            btn.draw(self.screen, self.font_btn, mouse_pos)

        # 提示信息
        msg = self.font_msg.render(self.message, True, DIM)
        self.screen.blit(msg, msg.get_rect(center=(WIDTH // 2, 112)))

        # 棋盘
        for r in range(N):
            for c in range(N):
                rect = pygame.Rect(GRID_X + c * CELL, GRID_Y + r * CELL, CELL, CELL)
                pygame.draw.rect(
                    self.screen, CELL_BG, rect.inflate(-6, -6), border_radius=10
                )
                pygame.draw.rect(
                    self.screen, CELL_LINE, rect.inflate(-6, -6), 2, border_radius=10
                )

        # 静态箭头（整支一起画）
        animated_ids = {a.arrow.id for a in self.anims}
        for arrow in self.arrows:
            if not arrow.alive or arrow.id in animated_ids:
                continue
            cx = GRID_X + arrow.head[1] * CELL + CELL // 2
            cy = GRID_Y + arrow.head[0] * CELL + CELL // 2
            color = ARROW_COLORS[arrow.direction]
            draw_arrow_full(
                self.screen, cx, cy, arrow.direction, arrow.length, color, darken(color)
            )

        # 动画中的箭头（飞出时裁到棋盘范围内，看起来像滑出棋盘）
        for anim in self.anims:
            cx = GRID_X + anim.c * CELL + CELL // 2 + anim.offset[0]
            cy = GRID_Y + anim.r * CELL + CELL // 2 + anim.offset[1]
            if isinstance(anim, FlyAnim):
                self.screen.set_clip(pygame.Rect(GRID_X, GRID_Y, GRID_W, GRID_W))
            draw_arrow_full(
                self.screen,
                cx,
                cy,
                anim.direction,
                anim.arrow.length,
                anim.head_color(),
                anim.body_color(),
            )
            self.screen.set_clip(None)

        hint = self.font_small.render("R 重开本关    Esc 返回开始", True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 622)))

    def draw_result(self, mouse_pos, title_text, sub_text):
        title = self.font_big.render(title_text, True, TEXT)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 250)))
        sub = self.font_msg.render(sub_text, True, DIM)
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 330)))
        for btn in self.buttons:
            btn.draw(self.screen, self.font_btn, mouse_pos)

    # ---------- 主循环 ----------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
