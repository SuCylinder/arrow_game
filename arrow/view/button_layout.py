# -*- coding: utf-8 -*-
"""按游戏状态构建按钮列表（含位置和回调绑定）。"""

from arrow.config import STATE_LOSE, STATE_PLAY, STATE_START, STATE_WIN, WIDTH
from arrow.levels import LEVELS
from arrow.view.button import Button


def build_buttons(game):
    """按 game.state 返回按钮列表，回调绑定到 game 的方法。"""
    buttons = []
    if game.state == STATE_START:
        buttons.append(
            Button(
                (WIDTH // 2 - 90, 430, 180, 52),
                "开始游戏",
                game.start_game,
                primary=True,
            )
        )
    elif game.state == STATE_PLAY:
        buttons.append(
            Button(
                (WIDTH - 140, 18, 116, 38),
                "重开本关",
                game.restart_level,
                primary=True,
            )
        )
        buttons.append(Button((WIDTH - 226, 18, 78, 38), "返回", game.to_start))
    elif game.state == STATE_WIN:
        if game.level_index + 1 < len(LEVELS):
            buttons.append(
                Button(
                    (WIDTH // 2 + 8, 430, 180, 52),
                    "下一关",
                    game.next_level,
                    primary=True,
                )
            )
        else:
            buttons.append(
                Button(
                    (WIDTH // 2 + 8, 430, 180, 52),
                    "回开始",
                    game.to_start,
                    primary=True,
                )
            )
        buttons.append(
            Button((WIDTH // 2 - 188, 430, 180, 52), "重开本关", game.restart_level)
        )
    elif game.state == STATE_LOSE:
        buttons.append(
            Button(
                (WIDTH // 2 + 8, 430, 180, 52),
                "重开本关",
                game.restart_level,
                primary=True,
            )
        )
        buttons.append(
            Button((WIDTH // 2 - 188, 430, 180, 52), "回开始", game.to_start)
        )
    return buttons
