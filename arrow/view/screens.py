# -*- coding: utf-8 -*-
"""各界面绘制：开始界面、关卡选择、游戏界面、结果界面。

函数统一接收 Game 实例（鸭子类型），只读取它的状态与字体字段，不修改状态。
布局坐标统一取自 arrow.config.layout 的锚点常量，调整分辨率只改配置。
"""

import pygame
import pygame.gfxdraw

from arrow.config import (
    ARROW_COLORS,
    CELL,
    CELL_BG,
    CELL_LINE,
    DIM,
    DOWN,
    GOLD,
    GREEN,
    GRID_FRAME,
    GRID_W,
    GRID_X,
    GRID_Y,
    HINT,
    HUD_DOT_R,
    HUD_DOT_STEP,
    HUD_DOT_X,
    HUD_PANEL,
    HUD_TEXT_X,
    HUD_TEXT_Y,
    LEFT,
    MSG_Y,
    N,
    PANEL_LINE,
    PILL,
    RED,
    RESULT_BADGE_R,
    RESULT_BADGE_Y,
    RESULT_HINT_Y,
    RESULT_NOTE_Y,
    RESULT_PANEL,
    RESULT_SCORE_Y,
    RESULT_STARS_Y,
    RESULT_SUB_Y,
    RESULT_TITLE_Y,
    RIGHT,
    SELECT_SUB_Y,
    SELECT_TITLE_Y,
    START_DECO_GAP,
    START_DECO_SIZE,
    START_DECO_Y,
    START_RULES_CENTER,
    START_TITLE_Y,
    STATE_LOSE,
    STATE_PLAY,
    STATE_SELECT,
    STATE_START,
    STATE_WIN,
    TEXT,
    TIMER_POS,
    UP,
    WIDTH,
)
from arrow.core.logic import count_arrows
from arrow.core.scoring import format_time
from arrow.levels import LEVELS
from arrow.view import button_layout
from arrow.view.animations import FlyAnim
from arrow.view.ui import (
    draw_arrow_head,
    draw_panel,
    draw_text_shadowed,
    make_gradient_bg,
)


def draw(game, mouse_pos):
    """按当前状态分发到对应界面。"""
    game.screen.blit(make_gradient_bg(game.screen.get_size()), (0, 0))
    if game.state == STATE_START:
        draw_start(game, mouse_pos)
    elif game.state == STATE_SELECT:
        draw_select(game, mouse_pos)
    elif game.state == STATE_PLAY:
        draw_play(game, mouse_pos)
    elif game.state == STATE_WIN:
        draw_result(game, mouse_pos, "win")
    else:
        draw_result(game, mouse_pos, "lose")


def draw_start(game, mouse_pos):
    draw_text_shadowed(
        game.screen, game.font_title, "箭头消除", TEXT,
        center=(WIDTH // 2, START_TITLE_Y),
    )
    # 四色小箭头装饰：上下左右各一支
    for i, direction in enumerate((UP, DOWN, LEFT, RIGHT)):
        draw_arrow_head(game.screen,
                        WIDTH // 2 + (i - 1.5) * START_DECO_GAP, START_DECO_Y,
                        direction, ARROW_COLORS[direction], size=START_DECO_SIZE)

    rules = [
        "点击箭头：它到边界之间没有其它箭头，就会飞出去",
        "被挡住则算碰撞：箭头晃动变红，失误 -1",
        "清空全部箭头过关，失误用完失败",
        "提示 H    撤销 Z    重开 R    Esc 返回",
    ]
    font = game.font_msg
    line_h = round(font.get_linesize() * 1.45)   # 规则行距
    pad_y = round(line_h * 0.35)
    box_w = max(font.size(line)[0] for line in rules) + 88
    box_h = len(rules) * line_h + pad_y * 2
    box = pygame.Rect(0, 0, box_w, box_h)
    box.center = START_RULES_CENTER
    draw_panel(game.screen, box, radius=15)

    for i, line in enumerate(rules):
        y = box.top + pad_y + line_h // 2 + i * line_h
        direction = (UP, LEFT, DOWN, RIGHT)[i]
        draw_arrow_head(game.screen, box.left + 37, y, direction,
                        ARROW_COLORS[direction], size=10)
        text = font.render(line, True, DIM)
        game.screen.blit(text, text.get_rect(midleft=(box.left + 60, y)))

    for btn in game.buttons:
        btn.draw(game.screen, game.font_btn, mouse_pos)


def draw_select(game, mouse_pos):
    draw_text_shadowed(
        game.screen, game.font_big, "选择关卡", TEXT,
        center=(WIDTH // 2, SELECT_TITLE_Y),
    )
    unlocked = game.unlocked_count()
    total = len(LEVELS)
    sub = game.font_msg.render(
        f"已解锁 {unlocked} / {total} 关（通关后自动解锁下一关）", True, DIM
    )
    game.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, SELECT_SUB_Y)))

    for i, rect in enumerate(button_layout.level_card_rects()):
        locked = i >= unlocked
        draw_panel(game.screen, rect, alpha=255 if not locked else 210)
        hovered = rect.collidepoint(mouse_pos) and not locked
        if hovered:
            pygame.draw.rect(game.screen, PILL, rect, border_radius=16)
            pygame.draw.rect(game.screen, TEXT, rect, 2, border_radius=16)

        num_color = DIM if locked else TEXT
        num = game.font_hud.render(f"第 {i + 1} 关", True, num_color)
        game.screen.blit(num, num.get_rect(center=(rect.centerx, rect.top + 46)))

        best = game.progress["best"].get(str(i + 1))
        if locked:
            lock = game.font_hud.render("未解锁", True, PANEL_LINE)
            game.screen.blit(lock, lock.get_rect(center=(rect.centerx, rect.centery + 12)))
        elif best:
            stars = game.font_star.render(
                "★" * best["stars"] + "☆" * (3 - best["stars"]), True, GOLD
            )
            game.screen.blit(stars, stars.get_rect(center=(rect.centerx, rect.centery + 11)))
            info = game.font_small.render(
                f"{best['score']} 分  {format_time(best['time'])}", True, DIM
            )
            game.screen.blit(info, info.get_rect(center=(rect.centerx, rect.bottom - 30)))
        else:
            todo = game.font_small.render("尚未挑战", True, PANEL_LINE)
            game.screen.blit(todo, todo.get_rect(center=(rect.centerx, rect.centery + 12)))

    for btn in game.buttons:
        btn.draw(game.screen, game.font_btn, mouse_pos)


def draw_play(game, mouse_pos):
    # HUD：圆角面板 + 关卡 / 剩余箭头 / 剩余失误（图标式）
    draw_panel(game.screen, HUD_PANEL, radius=16)
    if game.is_random():
        title = "随机挑战"
    else:
        title = f"第 {game.level_index + 1} / {len(LEVELS)} 关"
    hud = game.font_hud.render(title, True, TEXT)
    game.screen.blit(hud, hud.get_rect(midleft=(HUD_TEXT_X[0], HUD_TEXT_Y)))
    arrows = game.font_hud.render(f"剩余箭头 {count_arrows(game.arrows)}", True, TEXT)
    game.screen.blit(arrows, arrows.get_rect(midleft=(HUD_TEXT_X[1], HUD_TEXT_Y)))
    color = RED if game.mistakes_left <= 1 else TEXT
    mistakes = game.font_hud.render("剩余失误", True, color)
    game.screen.blit(mistakes, mistakes.get_rect(midleft=(HUD_TEXT_X[2], HUD_TEXT_Y)))
    # 失误圆点：剩余几颗填实，用尽显示空心
    for k in range(3):
        cx = HUD_DOT_X + k * HUD_DOT_STEP
        if k < game.mistakes_left:
            pygame.draw.circle(game.screen, color, (cx, HUD_TEXT_Y), HUD_DOT_R)
        else:
            pygame.draw.circle(game.screen, PANEL_LINE, (cx, HUD_TEXT_Y),
                               HUD_DOT_R, 2)

    for btn in game.buttons:
        btn.draw(game.screen, game.font_btn, mouse_pos)

    # 提示信息（胶囊底）
    msg = game.font_msg.render(game.message, True, DIM)
    msg_rect = msg.get_rect(center=(WIDTH // 2, MSG_Y))
    pill = msg_rect.inflate(49, 22)
    pygame.draw.rect(game.screen, PILL, pill, border_radius=pill.height // 2)
    pygame.draw.rect(game.screen, PANEL_LINE, pill, 1,
                     border_radius=pill.height // 2)
    game.screen.blit(msg, msg_rect)

    # 棋盘：外框 + 单元格（尺寸随 CELL 缩放）
    fm = round(CELL * 0.12)   # 外框留白
    ci = round(CELL * 0.07)   # 单元格内缩
    frame = pygame.Rect(GRID_X - fm, GRID_Y - fm, GRID_W + fm * 2, GRID_W + fm * 2)
    pygame.draw.rect(game.screen, GRID_FRAME, frame, border_radius=round(CELL * 0.18))
    pygame.draw.rect(game.screen, CELL_LINE, frame, 1, border_radius=round(CELL * 0.18))
    for r in range(N):
        for c in range(N):
            rect = pygame.Rect(GRID_X + c * CELL, GRID_Y + r * CELL, CELL, CELL)
            pygame.draw.rect(game.screen, CELL_BG, rect.inflate(-ci * 2, -ci * 2),
                             border_radius=round(CELL * 0.12))
            pygame.draw.rect(
                game.screen, CELL_LINE, rect.inflate(-ci * 2, -ci * 2), 2,
                border_radius=round(CELL * 0.12)
            )

    # 提示光环（在箭头下方画一圈脉冲圆环）
    if game.hint_cell is not None:
        hr, hc = game.hint_cell
        cx = GRID_X + hc * CELL + CELL // 2
        cy = GRID_Y + hr * CELL + CELL // 2
        base = round(CELL * 0.34)          # 基础半径（略大于头部顶点）
        pulse = base + 4 * (game.hint_timer % 0.4) / 0.4
        ring_r = base + 8
        ring = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
        pygame.gfxdraw.aacircle(ring, ring_r, ring_r, int(pulse), HINT)
        pygame.gfxdraw.filled_circle(ring, ring_r, ring_r, int(pulse), (*HINT, 40))
        pygame.gfxdraw.aacircle(ring, ring_r, ring_r, int(pulse), (*HINT, 160))
        game.screen.blit(ring, ring.get_rect(center=(cx, cy)))

    # 静态箭头（带轻投影）
    animated_ids = {a.arrow.id for a in game.anims}
    for arrow in game.arrows:
        if not arrow.alive or arrow.id in animated_ids:
            continue
        cx = GRID_X + arrow.head[1] * CELL + CELL // 2
        cy = GRID_Y + arrow.head[0] * CELL + CELL // 2
        draw_arrow_head(game.screen, cx, cy, arrow.direction,
                        ARROW_COLORS[arrow.direction], shadow=True)

    # 动画中的箭头（飞出时裁到棋盘范围内，看起来像滑出棋盘）
    for anim in game.anims:
        cx = GRID_X + anim.c * CELL + CELL // 2 + anim.offset[0]
        cy = GRID_Y + anim.r * CELL + CELL // 2 + anim.offset[1]
        if isinstance(anim, FlyAnim):
            game.screen.set_clip(pygame.Rect(GRID_X, GRID_Y, GRID_W, GRID_W))
        draw_arrow_head(game.screen, cx, cy, anim.direction, anim.head_color())
        game.screen.set_clip(None)

    # 底栏右侧：计时
    timer = game.font_hud.render(f"用时 {format_time(game.elapsed)}", True, DIM)
    game.screen.blit(timer, timer.get_rect(midleft=TIMER_POS))
    if game.ai_mode:
        tag = game.font_small.render("AI 演示中（不计成绩）", True, GOLD)
        game.screen.blit(tag, tag.get_rect(midright=(WIDTH - 27, TIMER_POS[1])))


def draw_stars(game, cx, cy, stars):
    """画三颗星（实心=已获得），空心用面板描边色。"""
    font = game.font_star
    gap = 8
    widths = [font.size("★")[0]] * 3
    total = sum(widths) + gap * 2
    x = cx - total // 2
    for i in range(3):
        char = "★" if i < stars else "☆"
        color = GOLD if i < stars else PANEL_LINE
        text = font.render(char, True, color)
        game.screen.blit(text, text.get_rect(midleft=(x, cy)))
        x += widths[i] + gap


def _draw_badge(surface, center, kind):
    """画通关/失败徽章：kind 为 "win" 时绿圈对勾，否则红圈叉。"""
    color = GREEN if kind == "win" else RED
    r = RESULT_BADGE_R
    size = r * 2 + 7
    mid = size // 2
    badge = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.gfxdraw.filled_circle(badge, mid, mid, r, color)
    pygame.gfxdraw.aacircle(badge, mid, mid, r, color)
    pygame.draw.circle(badge, (0, 0, 0, 0), (mid, mid), int(r * 0.80))  # 挖空
    width = max(5, int(r * 0.20))
    if kind == "win":
        pygame.draw.lines(badge, color, False,
                          [(int(r * 0.72), int(r * 1.22)),
                           (int(r * 1.04), int(r * 1.54)),
                           (int(r * 1.65), int(r * 0.83))], width)
    else:
        pygame.draw.line(badge, color, (int(r * 0.80), int(r * 0.80)),
                         (int(r * 1.57), int(r * 1.57)), width)
        pygame.draw.line(badge, color, (int(r * 1.57), int(r * 0.80)),
                         (int(r * 0.80), int(r * 1.57)), width)
    surface.blit(badge, badge.get_rect(center=center))


def draw_result(game, mouse_pos, kind):
    """结果界面：徽章 + 标题 + 星级/得分/用时 + 按钮。"""
    result = game.result or {}
    draw_panel(game.screen, RESULT_PANEL, radius=22)
    _draw_badge(game.screen, (WIDTH // 2, RESULT_BADGE_Y), kind)

    if kind == "win":
        if result.get("random"):
            title = "随机挑战完成！"
        elif game.level_index + 1 >= len(LEVELS):
            title = "全部通关！"
        else:
            title = f"第 {game.level_index + 1} 关通关！"
    else:
        title = "随机挑战失败" if result.get("random") else "游戏失败"
    draw_text_shadowed(
        game.screen, game.font_big, title, TEXT,
        center=(WIDTH // 2, RESULT_TITLE_Y),
    )

    if kind == "win":
        if result.get("ai"):
            note = game.font_msg.render("AI 演示结果（不计入成绩）", True, GOLD)
            game.screen.blit(note, note.get_rect(center=(WIDTH // 2, RESULT_NOTE_Y)))
        else:
            draw_stars(game, WIDTH // 2, RESULT_STARS_Y, result.get("stars", 0))
            score_text = game.font_msg.render(
                f"得分 {result.get('score', 0)}    用时 {format_time(result.get('time', 0))}",
                True, DIM,
            )
            game.screen.blit(
                score_text, score_text.get_rect(center=(WIDTH // 2, RESULT_SCORE_Y))
            )
            if result.get("best") and result.get("stars", 0) < 3:
                hint = game.font_small.render("用更少失误可以拿到三星", True, PANEL_LINE)
                game.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, RESULT_HINT_Y)))
    else:
        sub = game.font_msg.render(
            ("随机关卡失误用完了，换一关试试吧" if result.get("random")
             else f"第 {game.level_index + 1} 关失误用完了，重来一次吧"),
            True, DIM,
        )
        game.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, RESULT_SUB_Y)))

    for btn in game.buttons:
        btn.draw(game.screen, game.font_btn, mouse_pos)
