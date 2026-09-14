# -*- coding: utf-8 -*-
"""各界面绘制：开始界面、游戏界面、结果界面。

函数统一接收 Game 实例（鸭子类型），只读取它的状态与字体字段，不修改状态。
"""

import pygame

from arrow.config import (
    ARROW_COLORS,
    BG,
    CELL,
    CELL_BG,
    CELL_LINE,
    DIM,
    GRID_W,
    GRID_X,
    GRID_Y,
    N,
    RED,
    STATE_LOSE,
    STATE_PLAY,
    STATE_START,
    STATE_WIN,
    TEXT,
    WIDTH,
)
from arrow.core.logic import count_arrows
from arrow.core.utils import darken
from arrow.levels import LEVELS
from arrow.view.animations import FlyAnim
from arrow.view.ui import draw_arrow_full, draw_arrow_polyline


def draw(game, mouse_pos):
    """按当前状态分发到对应界面。"""
    game.screen.fill(BG)
    if game.state == STATE_START:
        draw_start(game, mouse_pos)
    elif game.state == STATE_PLAY:
        draw_play(game, mouse_pos)
    elif game.state == STATE_WIN:
        draw_result(
            game,
            mouse_pos,
            (
                "全部通关！"
                if game.level_index + 1 >= len(LEVELS)
                else f"第 {game.level_index + 1} 关通关！"
            ),
            (
                "点击「下一关」继续挑战"
                if game.level_index + 1 < len(LEVELS)
                else "你已经清空了所有关卡"
            ),
        )
    else:
        draw_result(
            game,
            mouse_pos,
            "游戏失败",
            f"第 {game.level_index + 1} 关失误用完了，重来一次吧",
        )


def draw_start(game, mouse_pos):
    title = game.font_title.render("箭头消除", True, TEXT)
    game.screen.blit(title, title.get_rect(center=(WIDTH // 2, 170)))
    rules = [
        "点击箭头头部：它指向的方向到边界之间没有其它箭头，就会飞出去",
        "被挡住则算碰撞：箭头不动，失误 -1",
        "箭头有身体（1~4 格），只有头部能点，身体同样会挡路",
        "清空全部箭头过关，失误用完失败",
    ]
    for i, line in enumerate(rules):
        text = game.font_msg.render(line, True, DIM)
        game.screen.blit(text, text.get_rect(center=(WIDTH // 2, 268 + i * 38)))
    for btn in game.buttons:
        btn.draw(game.screen, game.font_btn, mouse_pos)


def draw_play(game, mouse_pos):
    # HUD：关卡 / 剩余箭头 / 剩余失误
    hud = game.font_hud.render(
        f"第 {game.level_index + 1} / {len(LEVELS)} 关", True, TEXT
    )
    game.screen.blit(hud, hud.get_rect(midleft=(24, 37)))
    arrows = game.font_hud.render(f"剩余箭头 {count_arrows(game.arrows)}", True, TEXT)
    game.screen.blit(arrows, arrows.get_rect(midleft=(170, 37)))
    color = RED if game.mistakes_left <= 1 else TEXT
    mistakes = game.font_hud.render(f"剩余失误 {game.mistakes_left}", True, color)
    game.screen.blit(mistakes, mistakes.get_rect(midleft=(300, 37)))

    for btn in game.buttons:
        btn.draw(game.screen, game.font_btn, mouse_pos)

    # 提示信息
    msg = game.font_msg.render(game.message, True, DIM)
    game.screen.blit(msg, msg.get_rect(center=(WIDTH // 2, 112)))

    # 棋盘
    for r in range(N):
        for c in range(N):
            rect = pygame.Rect(GRID_X + c * CELL, GRID_Y + r * CELL, CELL, CELL)
            pygame.draw.rect(game.screen, CELL_BG, rect.inflate(-6, -6), border_radius=10)
            pygame.draw.rect(
                game.screen, CELL_LINE, rect.inflate(-6, -6), 2, border_radius=10
            )

    # 静态箭头（整支一起画）
    animated_ids = {a.arrow.id for a in game.anims}
    for arrow in game.arrows:
        if not arrow.alive or arrow.id in animated_ids:
            continue
        cx = GRID_X + arrow.head[1] * CELL + CELL // 2
        cy = GRID_Y + arrow.head[0] * CELL + CELL // 2
        color = ARROW_COLORS[arrow.direction]
        draw_arrow_full(game.screen, cx, cy, arrow, color, darken(color))

    # 动画中的箭头（飞出时裁到棋盘范围内，看起来像滑出棋盘）
    for anim in game.anims:
        if isinstance(anim, FlyAnim):
            game.screen.set_clip(pygame.Rect(GRID_X, GRID_Y, GRID_W, GRID_W))
            draw_arrow_polyline(
                game.screen,
                anim.points(),
                anim.direction,
                anim.head_color(),
                anim.body_color(),
            )
        else:
            cx = GRID_X + anim.c * CELL + CELL // 2 + anim.offset[0]
            cy = GRID_Y + anim.r * CELL + CELL // 2 + anim.offset[1]
            draw_arrow_full(
                game.screen,
                cx,
                cy,
                anim.arrow,
                anim.head_color(),
                anim.body_color(),
            )
        game.screen.set_clip(None)

    hint = game.font_small.render("R 重开本关    Esc 返回开始", True, DIM)
    game.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 622)))


def draw_result(game, mouse_pos, title_text, sub_text):
    title = game.font_big.render(title_text, True, TEXT)
    game.screen.blit(title, title.get_rect(center=(WIDTH // 2, 250)))
    sub = game.font_msg.render(sub_text, True, DIM)
    game.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 330)))
    for btn in game.buttons:
        btn.draw(game.screen, game.font_btn, mouse_pos)
