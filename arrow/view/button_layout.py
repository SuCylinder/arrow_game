# -*- coding: utf-8 -*-
"""按游戏状态构建按钮列表（含位置和回调绑定），以及关卡卡片布局。"""

import pygame

from arrow.config import (
    BOTTOM_BAR_Y,
    SELECT_CARD_H,
    SELECT_CARD_W,
    SELECT_COLS,
    SELECT_GAP_X,
    SELECT_GAP_Y,
    SELECT_TOP,
    STATE_LOSE,
    STATE_PLAY,
    STATE_SELECT,
    STATE_START,
    STATE_WIN,
    WIDTH,
)
from arrow.levels import LEVELS
from arrow.view.button import Button

# ---------------- 按钮尺寸（分辨率调整时改这里） ----------------
BTN_W, BTN_H = 206, 60          # 开始 / 结果界面的主按钮
BTN_SMALL_W, BTN_SMALL_H = 202, 51   # 开始界面第二行
BTN_BACK_W, BTN_BACK_H = 206, 53     # 选择界面回开始
BTN_HUD_W, BTN_HUD_H = 133, 44       # 游戏界面右上按钮
BTN_BACK2_W = 90                      # 右上「返回」按钮
BTN_GAP = 10                          # 按钮之间的间隙
SIDE_MARGIN = 18                      # 距窗口边缘
BTN_BAR_W, BTN_BAR_H = 110, 47       # 底栏按钮
BTN_AI_W = 126                        # 底栏 AI 按钮（稍宽）
HUD_BTN_Y = 21                        # 右上按钮顶部 y
START_BTN_Y = 519                     # 开始界面主按钮顶部 y
START_ROW2_Y = 597                    # 开始界面第二行按钮顶部 y
SELECT_BACK_Y = 692                   # 选择界面回开始按钮顶部 y
RESULT_BTN_Y = 544                    # 结果界面按钮顶部 y
BAR_X = (21, 139, 258)                # 底栏三个按钮的左边 x


def level_card_rects():
    """关卡选择界面的卡片矩形列表（与绘制共用同一套布局）。"""
    total = len(LEVELS)
    row_w = SELECT_COLS * SELECT_CARD_W + (SELECT_COLS - 1) * SELECT_GAP_X
    x0 = (WIDTH - row_w) // 2
    rects = []
    for i in range(total):
        row, col = divmod(i, SELECT_COLS)
        rects.append(pygame.Rect(
            x0 + col * (SELECT_CARD_W + SELECT_GAP_X),
            SELECT_TOP + row * (SELECT_CARD_H + SELECT_GAP_Y),
            SELECT_CARD_W,
            SELECT_CARD_H,
        ))
    return rects


def build_buttons(game):
    """按 game.state 返回按钮列表，回调绑定到 game 的方法。"""
    buttons = []
    if game.state == STATE_START:
        if game.has_progress():
            label, callback = f"继续第 {game.unlocked_count()} 关", game.continue_level
        else:
            label, callback = "开始游戏", game.start_game
        buttons.append(
            Button(
                (WIDTH // 2 - BTN_W // 2, START_BTN_Y, BTN_W, BTN_H),
                label,
                callback,
                primary=True,
            )
        )
        gap = 14
        pair_w = BTN_SMALL_W * 2 + gap
        x0 = (WIDTH - pair_w) // 2
        buttons.append(
            Button((x0, START_ROW2_Y, BTN_SMALL_W, BTN_SMALL_H),
                   "选择关卡", game.to_select)
        )
        buttons.append(
            Button((x0 + BTN_SMALL_W + gap, START_ROW2_Y, BTN_SMALL_W, BTN_SMALL_H),
                   "随机挑战", game.random_level)
        )
    elif game.state == STATE_SELECT:
        buttons.append(Button(
            (WIDTH // 2 - BTN_BACK_W // 2, SELECT_BACK_Y, BTN_BACK_W, BTN_BACK_H),
            "回开始", game.to_start,
        ))
    elif game.state == STATE_PLAY:
        buttons.append(
            Button(
                (WIDTH - SIDE_MARGIN - BTN_HUD_W, HUD_BTN_Y,
                 BTN_HUD_W, BTN_HUD_H),
                "重开本关",
                game.restart_level,
                primary=True,
            )
        )
        buttons.append(
            Button((WIDTH - SIDE_MARGIN - BTN_HUD_W - BTN_GAP - BTN_BACK2_W,
                    HUD_BTN_Y, BTN_BACK2_W, BTN_HUD_H),
                   "返回", game.to_start)
        )
        # 底栏：提示 / 撤销 / AI 演示
        buttons.append(Button((BAR_X[0], BOTTOM_BAR_Y, BTN_BAR_W, BTN_BAR_H),
                              "提示", game.show_hint))
        buttons.append(Button((BAR_X[1], BOTTOM_BAR_Y, BTN_BAR_W, BTN_BAR_H),
                              "撤销", game.undo))
        label = "停止 AI" if game.ai_mode else "AI 演示"
        buttons.append(Button((BAR_X[2], BOTTOM_BAR_Y, BTN_AI_W, BTN_BAR_H),
                              label, game.toggle_ai))
    elif game.state == STATE_WIN:
        right_x = WIDTH // 2 + 11
        left_x = WIDTH // 2 - 256
        if game.is_random():
            buttons.append(
                Button((right_x, RESULT_BTN_Y, BTN_W, BTN_H), "换一关",
                       game.random_level, primary=True)
            )
            buttons.append(
                Button((left_x, RESULT_BTN_Y, BTN_W, BTN_H), "回开始",
                       game.to_start)
            )
        else:
            if game.level_index + 1 < len(LEVELS):
                buttons.append(
                    Button((right_x, RESULT_BTN_Y, BTN_W, BTN_H), "下一关",
                           game.next_level, primary=True)
                )
            else:
                buttons.append(
                    Button((right_x, RESULT_BTN_Y, BTN_W, BTN_H), "回开始",
                           game.to_start, primary=True)
                )
            buttons.append(
                Button((left_x, RESULT_BTN_Y, BTN_W, BTN_H), "重开本关",
                       game.restart_level)
            )
    elif game.state == STATE_LOSE:
        buttons.append(
            Button((WIDTH // 2 + 11, RESULT_BTN_Y, BTN_W, BTN_H), "重开本关",
                   game.restart_level, primary=True)
        )
        buttons.append(
            Button((WIDTH // 2 - 256, RESULT_BTN_Y, BTN_W, BTN_H), "回开始",
                   game.to_start)
        )
    return buttons
