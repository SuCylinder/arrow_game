# -*- coding: utf-8 -*-
"""箭头消除游戏测试（无头运行，不需要真实窗口和显示器）。

覆盖：
  A 通关与状态机      参考解法逐关通关、按钮/Esc/R、下一关/回开始
  B 点击与路径检测    can_fly 行/列阻挡与边界、空盘、点空格、非法定义校验
  C 飞出/碰撞动画     中途可见、结束完全出界、无空转；碰撞晃动变色、扣失误
  D 渲染             箭头朝向、HUD、按钮、结果界面
  E 关卡数据性质      定义合法、支数 6/8/10、参考解覆盖、倒序摆盘、开局可飞
  F 失败窗口          失误归零后锁操作、不误判通关、连点锁定
  G 模糊测试          随机点击+按键 6000 步的不变量检查、随机乱点必达终局
  H 真实入口          main.main() 线程跑主循环，注入事件后干净退出

运行：uv run python test_smoke.py
"""

import os
import random
import sys
import tempfile
import threading
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import main  # noqa: E402
from arrow import config as cfg  # noqa: E402
from arrow import levels  # noqa: E402
from arrow.core import generator, logic, save as save_mod, scoring, solver  # noqa: E402
from arrow.game import Game  # noqa: E402
from arrow.view import button_layout  # noqa: E402
from arrow.view.animations import FlyAnim, ShakeAnim  # noqa: E402
from arrow.view.ui import make_font  # noqa: E402

N = cfg.N
CELL = cfg.CELL
GX, GY, GW = cfg.GRID_X, cfg.GRID_Y, cfg.GRID_W

# 各关参考通关顺序（与 arrow/levels/levelN.py 注释一致）
ORDERS = [
    [(4, 3), (2, 3), (2, 0), (1, 3), (1, 1), (1, 2)],
    [(4, 1), (3, 0), (4, 3), (3, 1), (3, 2), (4, 2), (3, 4), (2, 1)],
    [(4, 1), (0, 0), (0, 4), (2, 1), (1, 4), (1, 1), (4, 2), (3, 2), (3, 4), (2, 0)],
    [(0, 4), (4, 1), (0, 3), (3, 1), (0, 1), (1, 4),
     (2, 1), (3, 3), (3, 0), (2, 4), (4, 3), (4, 4)],
    [(0, 0), (4, 3), (0, 1), (1, 1), (1, 4), (3, 1), (4, 1),
     (3, 3), (3, 2), (1, 0), (2, 2), (0, 3), (4, 0), (0, 4)],
    [(2, 3), (0, 4), (3, 1), (0, 3), (0, 0), (4, 4), (1, 4), (0, 2),
     (0, 1), (1, 3), (3, 0), (4, 3), (4, 2), (4, 0), (2, 2), (4, 1)],
]

EXPECTED_COUNTS = [6, 8, 10, 12, 14, 16]

FAILURES = []
CHECKS = 0


def check(name, cond):
    global CHECKS
    CHECKS += 1
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILURES.append(name)


def near(c1, c2, tol=30):
    """两个 RGB 是否接近。"""
    return all(abs(a - b) <= tol for a, b in zip(c1[:3], c2[:3]))


def empty_board():
    return [[cfg.EMPTY] * N for _ in range(N)]


def click_event(pos):
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": pos}))
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"button": 1, "pos": pos}))


def key_event(k):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": k}))


def cell_center(r, c):
    return (GX + c * CELL + CELL // 2, GY + r * CELL + CELL // 2)


pygame.init()
check("main.py 复用 arrow.game.Game", main.Game is Game)
# 测试用独立存档路径，避免污染仓库里的 save.json
_tmpdir = tempfile.mkdtemp(prefix="arrow_test_")
SAVE_PATH = os.path.join(_tmpdir, "save.json")
game = Game(save_path=SAVE_PATH)


# ---------------- A. 通关与状态机 ----------------
for idx, order in enumerate(ORDERS):
    game.level_index = idx
    game.load_level()
    check(f"第{idx + 1}关载入后为 PLAY", game.state == cfg.STATE_PLAY)
    n_arrows = logic.count_arrows(game.arrows)
    check(f"第{idx + 1}关箭头支数 {n_arrows}（期望 {EXPECTED_COUNTS[idx]}）",
          n_arrows == EXPECTED_COUNTS[idx])
    heads = [a.head for a in game.arrows]
    check(f"第{idx + 1}关参考解覆盖全部 {n_arrows} 支箭头",
          sorted(order) == sorted(heads))
    base = game.mistakes_left
    for step, (r, c) in enumerate(order):
        arrow = game.arrow_by_id[game.board[r][c]]
        check(f"第{idx + 1}关第{step + 1}步 ({r},{c}) 处可飞",
              arrow.head == (r, c) and game.can_fly(r, c))
        game.try_click(r, c)
        game.update(1.0)
    check(f"第{idx + 1}关按参考顺序清空", logic.count_arrows(game.arrows) == 0)
    check(f"第{idx + 1}关进入 WIN", game.state == cfg.STATE_WIN)
    check(f"第{idx + 1}关未扣失误", game.mistakes_left == base)
    check(f"第{idx + 1}关所有箭头 alive 为 False",
          all(not a.alive for a in game.arrows))

# 开始界面 → 开始游戏（先清空进度，验证全新开局路径）
game.progress = save_mod.default_data()
game.to_start()
check("返回开始界面", game.state == cfg.STATE_START)
start_btn = next(b for b in game.buttons if b.label == "开始游戏")
game.on_click(start_btn.rect.center)
check("点「开始游戏」进第 1 关",
      game.state == cfg.STATE_PLAY and game.level_index == 0)

# 重开本关按钮 / R 键
game.mistakes_left = 1
restart_btn = next(b for b in game.buttons if b.label == "重开本关")
game.on_click(restart_btn.rect.center)
check("点「重开本关」失误回满", game.mistakes_left == cfg.MISTAKES_PER_LEVEL)
game.mistakes_left = 1
key_event(pygame.K_r)
game.handle_events()
check("按 R 重开本关", game.mistakes_left == cfg.MISTAKES_PER_LEVEL)
key_event(pygame.K_ESCAPE)
game.handle_events()
check("按 Esc 回开始界面", game.state == cfg.STATE_START)

# 非最后一关：下一关按钮
game.level_index = 0
game.load_level()
game.board = empty_board()
for a in game.arrows:
    a.alive = False
game.update(0.016)
check("非最后一关清空后进入 WIN", game.state == cfg.STATE_WIN)
check("非最后一关按钮为「下一关」",
      any(b.label == "下一关" for b in game.buttons))
game.on_click(next(b for b in game.buttons if b.label == "下一关").rect.center)
check("点「下一关」进第 2 关",
      game.state == cfg.STATE_PLAY and game.level_index == 1)

# 最后一关：回开始按钮
game.level_index = len(levels.LEVELS) - 1
game.load_level()
game.board = empty_board()
for a in game.arrows:
    a.alive = False
game.update(0.016)
check("最后一关清空后进入 WIN", game.state == cfg.STATE_WIN)
check("最后一关按钮为「回开始」",
      any(b.label == "回开始" for b in game.buttons))
game.on_click(next(b for b in game.buttons if b.label == "回开始").rect.center)
check("点「回开始」回开始界面", game.state == cfg.STATE_START)


# ---------------- B. 点击与路径检测 ----------------
def set_board(defs):
    board, arrows = logic.build_arrows(defs)
    game.board, game.arrows = board, arrows
    game.arrow_by_id = {a.id: a for a in arrows}
    game.anims.clear()
    game.state = cfg.STATE_PLAY
    game.mistakes_left = cfg.MISTAKES_PER_LEVEL


# 四角朝外均可飞（边界不越界）
set_board([
    (cfg.UP, 0, 0), (cfg.RIGHT, 0, 4),
    (cfg.LEFT, 4, 0), (cfg.DOWN, 4, 4),
])
check("四角朝外均可飞（边界不越界）",
      all(game.can_fly(r, c) for r, c in [(0, 0), (0, 4), (4, 0), (4, 4)]))

# 同一行有阻挡：朝右的 (2,0) 被 (2,3) 挡住
set_board([(cfg.RIGHT, 2, 0), (cfg.UP, 2, 3)])
check("同行中间有阻挡 → 不可飞", not game.can_fly(2, 0))
check("被挡箭头右侧确实有别人", game.can_fly(2, 3))

# 同一列有阻挡：朝下的 (1,1) 被 (4,1) 挡住
set_board([(cfg.DOWN, 1, 1), (cfg.UP, 4, 1)])
check("同列最远端有阻挡 → 不可飞", not game.can_fly(1, 1))

# 相邻阻挡：朝右的 (2,2) 紧挨 (2,3) 的箭头 → 不可飞
set_board([(cfg.RIGHT, 2, 2), (cfg.LEFT, 2, 3)])
check("相邻格阻挡 → 不可飞", not game.can_fly(2, 2))
check("相邻反向互相阻挡（(2,3) 朝左也被 (2,2) 挡住）",
      not game.can_fly(2, 3))

# 路径上全是空格 → 可飞
set_board([(cfg.RIGHT, 2, 1), (cfg.UP, 4, 4)])
check("路径全空 → 可飞", game.can_fly(2, 1))

# 同行反向但不相邻：朝右的 (2,0) 与朝左的 (2,4)，互相挡在对方路径上
set_board([(cfg.RIGHT, 2, 0), (cfg.LEFT, 2, 4)])
check("不相邻反向：朝右被 (2,4) 挡", not game.can_fly(2, 0))
check("不相邻反向：朝左被 (2,0) 挡", not game.can_fly(2, 4))

# 点空格：提示且不扣失误
set_board([(cfg.UP, 0, 0)])
game.try_click(3, 3)
check("点空格提示且不扣失误",
      game.mistakes_left == cfg.MISTAKES_PER_LEVEL and "空格" in game.message)
check("点空格不产生动画", not game.anims)

# 合法定义构建
board, arrows = logic.build_arrows([(cfg.RIGHT, 0, 0), (cfg.UP, 4, 4)])
check("build_arrows 正确铺设棋盘",
      board[0][0] == 1 and board[4][4] == 2 and board[2][2] == cfg.EMPTY)
check("Arrow 记录方向与位置",
      arrows[0].direction == cfg.RIGHT and arrows[0].head == (0, 0)
      and arrows[1].head == (4, 4))

# 非法定义校验
bad_defs = [
    ("方向非法", [(99, 0, 0)]),
    ("行越界", [(cfg.UP, -1, 0)]),
    ("列越界", [(cfg.UP, 0, 5)]),
    ("重叠", [(cfg.UP, 0, 0), (cfg.DOWN, 0, 0)]),
]
for label, defs in bad_defs:
    try:
        logic.build_arrows(defs)
        check(f"非法定义抛 ValueError：{label}", False)
    except ValueError:
        check(f"非法定义抛 ValueError：{label}", True)

# 空盘点击返回 False
board = empty_board()
game.board, game.arrows, game.arrow_by_id = board, [], {}
check("空盘 can_fly 返回 False", not game.can_fly(0, 0))
check("空盘统计支数为 0", logic.count_arrows(game.arrows) == 0)


# ---------------- C. 飞出 / 碰撞动画 ----------------
def arrow_pixels(colors, step=6):
    """扫描棋盘区域，统计属于这些颜色的像素数。"""
    count = 0
    for x in range(GX, GX + GW, step):
        for y in range(GY, GY + GW, step):
            p = game.screen.get_at((x, y))
            for color in colors:
                if near(p, color, 30):
                    count += 1
                    break
    return count


# 飞出动画：方向 × 位置的全覆盖
fly_cases = []
for c in range(N):
    fly_cases.append((cfg.UP, (0, c)))
    fly_cases.append((cfg.DOWN, (4, c)))
for r in range(N):
    fly_cases.append((cfg.LEFT, (r, 0)))
    fly_cases.append((cfg.RIGHT, (r, 4)))
fly_cases += [(cfg.UP, (2, 2)), (cfg.DOWN, (2, 2)), (cfg.LEFT, (2, 2)),
              (cfg.RIGHT, (2, 2))]

mid_visible = 0
fully_out = 0
no_spin = 0
bad = []
for (d, (r, c)) in fly_cases:
    set_board([(d, r, c)])
    if not game.can_fly(r, c):
        bad.append(("不可飞", d, r, c))
        continue
    game.try_click(r, c)
    anim = game.anims[0]
    colors = [cfg.ARROW_COLORS[d]]

    game.update(anim.duration * 0.5)           # 中途：应仍可见
    game.draw()
    if arrow_pixels(colors) > 0:
        mid_visible += 1

    game.update(anim.duration * 0.45)          # 95%：应已基本滑出
    game.draw()
    px95 = arrow_pixels(colors)

    # 99.9%：应完全出界（仍在 PLAY 画面，避免结果界面的徽章/按钮色干扰）
    game.update(anim.duration * 0.999 - anim.elapsed)
    game.draw()
    if arrow_pixels(colors) == 0:
        fully_out += 1

    # 100%：动画结束、棋盘数据清除
    game.update(anim.duration - anim.elapsed)
    if px95 <= 10:
        no_spin += 1
    if game.board[r][c] != cfg.EMPTY:
        bad.append(("结束未清除", d, r, c))

total = len(fly_cases)
check(f"飞出用例全部可飞（{total} 例）", not bad)
check(f"飞出动画中途仍可见（{mid_visible}/{total}）", mid_visible == total)
check(f"飞出动画结束完全出界（{fully_out}/{total}）", fully_out == total)
check(f"飞出动画无末尾空转（{no_spin}/{total}）", no_spin >= int(total * 0.9))
for item in bad[:5]:
    print("  BAD:", item)

# 飞出方向正确：中途时箭头中心应沿方向偏移
for d, (dr, dc) in cfg.DIRS.items():
    set_board([(d, 2, 2)])
    game.try_click(2, 2)
    anim = game.anims[0]
    game.update(anim.duration * 0.4)
    check(f"方向 {d} 的飞出偏移方向正确",
          anim.offset[0] * dc + anim.offset[1] * dr > 0)

# 碰撞：晃动 + 变色 + 扣失误
set_board([(cfg.RIGHT, 2, 2), (cfg.LEFT, 2, 4)])
game.try_click(2, 2)
check("碰撞后失误 3→2", game.mistakes_left == 2)
check("碰撞生成晃动动画",
      len(game.anims) == 1 and isinstance(game.anims[0], ShakeAnim))
check("碰撞后箭头仍在原地", game.board[2][2] != cfg.EMPTY)
game.update(0.25)
check("晃动中途颜色变红",
      game.anims[0].head_color() != cfg.ARROW_COLORS[cfg.RIGHT])
check("晃动幅度非零（确实在动）", game.anims[0].offset != (0.0, 0.0))
game.update(0.5)
check("晃动结束箭头不消失", game.board[2][2] != cfg.EMPTY)
check("晃动结束仍在 PLAY", game.state == cfg.STATE_PLAY)
check("晃动结束颜色复位",
      game.anims == [] or game.anims[0].head_color() == cfg.ARROW_COLORS[cfg.RIGHT])


# ---------------- D. 渲染 ----------------
game.start_game()
game.draw()
DIRS = cfg.DIRS

# 头部朝向：顶点一侧应有箭头色
dir_checked = 0
for arrow in game.arrows:
    r, c = arrow.head
    d = arrow.direction
    dr, dc = DIRS[d]
    tip = game.screen.get_at((GX + c * CELL + CELL // 2 + dc * int(CELL * 0.30),
                              GY + r * CELL + CELL // 2 + dr * int(CELL * 0.30)))
    check(f"({r},{c}) 头部朝向正确（顶点一侧有箭头色）",
          near(tip, cfg.ARROW_COLORS[d]))
    dir_checked += 1
check(f"头部朝向检查已覆盖（{dir_checked} 支）", dir_checked >= 6)

# 头部格中心应是头部色（三角覆盖中心）
head_checked = 0
for arrow in game.arrows:
    hr, hc = arrow.head
    center = game.screen.get_at(cell_center(hr, hc))
    check(f"({hr},{hc}) 头部格中心为箭头色",
          near(center, cfg.ARROW_COLORS[arrow.direction]))
    head_checked += 1
check(f"箭头渲染已覆盖（{head_checked} 支）", head_checked >= 6)

# 四方向颜色互不相同
check("四方向颜色互不相同",
      len(set(cfg.ARROW_COLORS.values())) == 4)

# 抗锯齿：三角形边缘应存在过渡色（既不纯箭头色也不纯背景）
aa_hits = 0
for arrow in game.arrows:
    r, c = arrow.head
    color = cfg.ARROW_COLORS[arrow.direction]
    for x in range(GX + c * CELL + CELL // 2 - 26,
                   GX + c * CELL + CELL // 2 + 26):
        for y in range(GY + r * CELL + CELL // 2 - 26,
                       GY + r * CELL + CELL // 2 + 26):
            p = game.screen.get_at((x, y))
            if not near(p, color, 10) and not near(p, cfg.CELL_BG, 10) \
                    and not near(p, cfg.CELL_LINE, 10):
                aa_hits += 1
check(f"三角形边缘有抗锯齿过渡色（{aa_hits} 像素）", aa_hits > 0)


def region_has_text(x0, y0, w, h):
    for x in range(x0, x0 + w, 3):
        for y in range(y0, y0 + h, 3):
            if not near(game.screen.get_at((x, y)), cfg.BG, 12):
                return True
    return False


_hud_x = cfg.HUD_TEXT_X
_hud_y = cfg.HUD_TEXT_Y
check("HUD 关卡文字已绘制",
      region_has_text(_hud_x[0], _hud_y - 18, 170, 36))
check("HUD 剩余箭头已绘制",
      region_has_text(_hud_x[1], _hud_y - 18, 160, 36))
check("HUD 剩余失误已绘制",
      region_has_text(_hud_x[2], _hud_y - 18, 130, 36))

# HUD 面板：左边框应为面板描边色，面板外（右侧）不应是描边色
panel_edge = game.screen.get_at((cfg.HUD_PANEL[0], _hud_y))[:3]
outside = game.screen.get_at((cfg.HUD_PANEL[0] + cfg.HUD_PANEL[2] + 12, _hud_y))[:3]
check("HUD 圆角面板已绘制",
      near(panel_edge, cfg.PANEL_LINE, 20) and not near(outside, cfg.PANEL_LINE, 20))

# 失误圆点：剩余 3 时应能在面板内找到 3 个填实圆点（红/文本色）
def dots_color():
    return cfg.RED if game.mistakes_left <= 1 else cfg.TEXT


dot_hits = 0
for k in range(3):
    cx = cfg.HUD_DOT_X + k * cfg.HUD_DOT_STEP
    if near(game.screen.get_at((cx, _hud_y)), dots_color(), 40):
        dot_hits += 1
check(f"失误圆点已绘制（3 颗中命中 {dot_hits}）", dot_hits == 3)
check("提示信息已绘制",
      region_has_text(cfg.WIDTH // 2 - 220, cfg.MSG_Y - 18, 440, 36))
check("底栏计时已绘制",
      region_has_text(cfg.TIMER_POS[0], cfg.TIMER_POS[1] - 16, 220, 32))
for btn in game.buttons:
    probe = game.screen.get_at((btn.rect.x + 5, btn.rect.centery))
    check(f"按钮「{btn.label}」已绘制",
          any(near(probe, c, 60) for c in
              (cfg.BTN, cfg.BTN_HOVER, cfg.BTN_PRIMARY, cfg.BTN_PRIMARY_HOVER)))
check("底栏含提示/撤销/AI 演示按钮",
      all(any(b.label == name for b in game.buttons)
          for name in ("提示", "撤销", "AI 演示")))

# AI 演示标签：移到 HUD 第二行，且不得再与底栏计时重叠
game.toggle_ai()
game.draw()
check("AI 演示标签已绘制在 HUD 第二行",
      region_has_text(cfg.HUD_AI_TAG_POS[0], cfg.HUD_AI_TAG_POS[1] - 16, 230, 32))
bar_has_gold = any(
    near(game.screen.get_at((x, y)), cfg.GOLD, 30)
    for x in range(cfg.TIMER_POS[0], cfg.TIMER_POS[0] + 220, 2)
    for y in range(cfg.TIMER_POS[1] - 16, cfg.TIMER_POS[1] + 16, 2)
)
check("AI 演示标签不再与底栏计时重叠（计时区无金色像素）", not bar_has_gold)
game.toggle_ai()
game.draw()

for st, tag in [(cfg.STATE_LOSE, "失败"), (cfg.STATE_WIN, "通关")]:
    game.state = st
    game._build_buttons()
    game.draw()
    check(f"{tag}界面标题已绘制",
          region_has_text(cfg.WIDTH // 2 - 250, cfg.RESULT_TITLE_Y - 38, 500, 76))
    check(f"{tag}界面提示已绘制",
          region_has_text(cfg.WIDTH // 2 - 250, cfg.RESULT_SUB_Y - 20, 500, 40))

# 开始界面文字
game.to_start()
game.draw()
check("开始界面标题已绘制",
      region_has_text(cfg.WIDTH // 2 - 250, cfg.START_TITLE_Y - 45, 500, 90))
check("开始界面规则已绘制",
      region_has_text(cfg.START_RULES_CENTER[0] - 350,
                      cfg.START_RULES_CENTER[1] - 120, 700, 240))

# 开始界面四色装饰箭头（标题下方一排）
deco_hits = 0
for i, d in enumerate((cfg.UP, cfg.DOWN, cfg.LEFT, cfg.RIGHT)):
    cx = cfg.WIDTH // 2 + (i - 1.5) * cfg.START_DECO_GAP
    if near(game.screen.get_at((int(cx), cfg.START_DECO_Y)),
            cfg.ARROW_COLORS[d], 40):
        deco_hits += 1
check(f"开始界面四色装饰箭头已绘制（{deco_hits}/4）", deco_hits == 4)

# 结果界面徽章：通关绿 / 失败红（探针取圆环带）
_badge_y = cfg.RESULT_BADGE_Y
_badge_r = cfg.RESULT_BADGE_R - 4
game.state = cfg.STATE_WIN
game._build_buttons()
game.draw()
win_badge = any(
    near(game.screen.get_at((cfg.WIDTH // 2 + dx, _badge_y + dy)), cfg.GREEN, 20)
    for dx, dy in ((0, -_badge_r), (_badge_r, 0), (-_badge_r, 0), (0, _badge_r))
)
game.state = cfg.STATE_LOSE
game._build_buttons()
game.draw()
lose_badge = any(
    near(game.screen.get_at((cfg.WIDTH // 2 + dx, _badge_y + dy)), cfg.RED, 20)
    for dx, dy in ((0, -_badge_r), (_badge_r, 0), (-_badge_r, 0), (0, _badge_r))
)
check("通关界面绿色徽章已绘制", win_badge)
check("失败界面红色徽章已绘制", lose_badge)

# 通关界面：星级与得分文字
game.state = cfg.STATE_WIN
game.result = {"stars": 3, "score": 1770, "time": 6.0,
               "best": {"stars": 3, "score": 1770, "time": 6.0},
               "random": False, "ai": False}
game._build_buttons()
game.draw()
check("通关界面星级已绘制",
      region_has_text(cfg.WIDTH // 2 - 120, cfg.RESULT_STARS_Y - 26, 240, 52))
check("通关界面得分用时已绘制",
      region_has_text(cfg.WIDTH // 2 - 220, cfg.RESULT_SCORE_Y - 20, 440, 40))

# 开始界面：三个按钮（此时存档已有第 1 关成绩 → 主按钮为继续）
game.to_start()
game.draw()
check("开始界面主按钮按存档显示 继续/开始",
      any(b.label.startswith(("开始游戏", "继续第")) for b in game.buttons))
check("开始界面含 选择关卡 / 随机挑战",
      all(any(b.label == name for b in game.buttons)
          for name in ("选择关卡", "随机挑战")))
check("开始界面显示存档进度摘要",
      region_has_text(cfg.WIDTH // 2 - 230, cfg.START_PROGRESS_Y - 16, 460, 32))

# 关卡选择界面：标题、卡片、锁定与解锁样式
game.progress["unlocked"] = 2
game.progress["best"]["1"] = {"stars": 3, "score": 1770, "time": 6.0}
game.to_select()
game.draw()
check("选择界面标题已绘制",
      region_has_text(cfg.WIDTH // 2 - 160, cfg.SELECT_TITLE_Y - 42, 320, 84))
cards = button_layout.level_card_rects()
check("第一张卡片中心有文字（第 1 关）",
      region_has_text(cards[0].x + 20, cards[0].y + 20,
                      cards[0].width - 40, 40))
star_pixels = 0
for x in range(cards[0].x, cards[0].right, 2):
    for y in range(cards[0].centery - 18, cards[0].centery + 26, 2):
        if near(game.screen.get_at((x, y)), cfg.GOLD, 30):
            star_pixels += 1
check(f"第 1 关卡片显示金色星级（{star_pixels} 像素）", star_pixels > 5)
check("未解锁卡片显示灰色遮罩（无金色星）",
      not any(near(game.screen.get_at((x, y)), cfg.GOLD, 30)
              for x in range(cards[5].x, cards[5].right, 3)
              for y in range(cards[5].y, cards[5].bottom, 3)))
game.to_start()


# ---------------- E. 关卡数据性质 ----------------
check("每关都是箭头定义列表且非空",
      all(isinstance(lv, list) and lv for lv in levels.LEVELS))
check(f"共 6 个关卡", len(levels.LEVELS) == 6)

for idx, defs in enumerate(levels.LEVELS):
    board, arrows = logic.build_arrows(defs)       # 非法定义会抛异常
    check(f"第{idx + 1}关定义合法（不越界不重叠）", True)
    check(f"第{idx + 1}关箭头支数 = {EXPECTED_COUNTS[idx]}",
          len(arrows) == EXPECTED_COUNTS[idx])
    check(f"第{idx + 1}关全部单格箭头（head 即所在格）",
          all(board[a.head[0]][a.head[1]] == a.id for a in arrows))
    check(f"第{idx + 1}关四方向齐全",
          len({a.direction for a in arrows}) == 4)
    cells = [a.head for a in arrows]
    check(f"第{idx + 1}关至少占 3 行 3 列（分布不集中）",
          len({r for r, _ in cells}) >= 3 and len({c for _, c in cells}) >= 3)
    # 参考解覆盖全部箭头，且倒序摆盘每步可飞
    game.board = empty_board()
    game.arrow_by_id = {}
    reverse_ok = True
    real_board, real_arrows = logic.build_arrows(defs)
    for (r, c) in reversed(ORDERS[idx]):
        a = next(x for x in real_arrows if x.id == real_board[r][c])
        game.board[r][c] = a.id
        game.arrow_by_id[a.id] = a
        if not game.can_fly(r, c):
            reverse_ok = False
            break
    check(f"第{idx + 1}关倒序摆盘每步可飞（制作方式成立）", reverse_ok)
    # 参考解前向复验：逐步可飞直到清空
    board2, arrows2 = logic.build_arrows(defs)
    game.board, game.arrows = board2, arrows2
    game.arrow_by_id = {a.id: a for a in arrows2}
    forward_ok = True
    for (r, c) in ORDERS[idx]:
        if game.board[r][c] == cfg.EMPTY or not game.can_fly(r, c):
            forward_ok = False
            break
        game.board[r][c] = cfg.EMPTY
    check(f"第{idx + 1}关参考解逐步可飞直到清空", forward_ok)
    # 开局存在可飞箭头（不会开局死局）
    board3, arrows3 = logic.build_arrows(defs)
    game.board, game.arrows = board3, arrows3
    game.arrow_by_id = {a.id: a for a in arrows3}
    n_flyable = sum(1 for a in game.arrows if game.can_fly(*a.head))
    check(f"第{idx + 1}关开局存在可飞箭头（{n_flyable} 支）", n_flyable >= 1)

check("每关失误次数为 3", cfg.MISTAKES_PER_LEVEL == 3)

for size, sample in [(cfg.FONT_TITLE, "箭头消除"),
                     (cfg.FONT_HUD, "第关剩余失误飞出去了重开本"),
                     (cfg.FONT_BTN, "开始游戏下一关回"),
                     (cfg.FONT_SMALL, "按提示撤销"),
                     (cfg.FONT_STAR, "★☆")]:
    font = make_font(size)
    metrics = font.metrics(sample)
    check(f"{size}px 字体覆盖「{sample}」",
          metrics is not None and all(m is not None for m in metrics))


# ---------------- F. 失败窗口 ----------------
set_board([(cfg.RIGHT, 2, 2), (cfg.LEFT, 2, 4), (cfg.UP, 0, 0)])
game.mistakes_left = 1
game.try_click(2, 2)
check("失误归零时停在 PLAY（等动画）",
      game.state == cfg.STATE_PLAY and game.mistakes_left == 0)
before = sum(1 for a in game.arrows if a.alive)
game.try_click(0, 0)                  # 另一支本来可飞的箭头也应被锁住
check("失误归零后的点击被拦截",
      sum(1 for a in game.arrows if a.alive) == before
      and len(game.anims) == 1 and game.mistakes_left == 0)
game.update(1.0)
check("晃动结束进入 LOSE", game.state == cfg.STATE_LOSE)
check("失败时箭头未被清空（不会误判通关）",
      sum(1 for a in game.arrows if a.alive) > 0)
check("失败界面按钮为「重开本关」/「回开始」",
      any(b.label == "重开本关" for b in game.buttons)
      and any(b.label == "回开始" for b in game.buttons))

# 同一支箭头动画期间连点锁定
set_board([(cfg.RIGHT, 2, 2)])
game.try_click(2, 2)
game.try_click(2, 2)
check("飞出动画期间连点被锁", len(game.anims) == 1)
game.update(1.0)
check("飞出结束后数据清除", game.board[2][2] == cfg.EMPTY)

# 重开本关恢复初始状态
game.level_index = 0
game.load_level()
game.board[0][0] = cfg.EMPTY          # 人为破坏一盘
game.restart_level()
check("重开本关恢复初始棋盘",
      game.board == logic.build_arrows(levels.LEVELS[0])[0])
check("重开本关失误回满", game.mistakes_left == cfg.MISTAKES_PER_LEVEL)


# ---------------- G. 扩展功能 ----------------
# --- 提示 ---
game.start_game()
game.show_hint()
check("提示高亮一个可飞格", game.hint_cell is not None
      and game.can_fly(*game.hint_cell))
check("提示计时已启动", game.hint_timer > 0)
game.update(cfg.HINT_SECONDS + 0.1)
check("提示超时后自动清除", game.hint_cell is None)
game.show_hint()
check("再次提示可高亮", game.hint_cell is not None)
game.try_click(*game.hint_cell)      # 操作后提示立即清除
check("点击操作后提示清除", game.hint_cell is None)
game.update(1.0)

# --- 撤销 ---
game.load_level()
snapshot = [row[:] for row in game.board]
alive_before = logic.count_arrows(game.arrows)
pick = solver.greedy_pick(game.board, game.arrows, game.arrow_by_id)
game.try_click(*pick.head)
game.update(1.0)
check("撤销前成功飞走",
      game.board[pick.head[0]][pick.head[1]] == cfg.EMPTY
      and logic.count_arrows(game.arrows) == alive_before - 1)
check("成功步进入撤销栈", len(game.undo_stack) == 1)
game.undo()
check("撤销后棋盘恢复原样", game.board == snapshot)
check("撤销后箭头复活", logic.count_arrows(game.arrows) == alive_before
      and game.arrow_by_id[snapshot[pick.head[0]][pick.head[1]]].alive)
game.undo()
check("撤销栈空时给出提示", "没有可以撤销" in game.message)
# 碰撞（未成功）不进撤销栈
game.load_level()
blocked = next(a for a in game.arrows if not game.can_fly(*a.head))
game.try_click(*blocked.head)
game.update(1.0)
check("碰撞不进入撤销栈", not game.undo_stack)
check("碰撞后失误已扣", game.mistakes_left == cfg.MISTAKES_PER_LEVEL - 1)
game.undo()
check("碰撞后不能撤销（无成功步）", "没有可以撤销" in game.message)

# --- AI 演示（独立存档，避免与其它用例互相影响）---
ai_path = os.path.join(_tmpdir, "ai_save.json")
ai_game = Game(save_path=ai_path)
ai_game.start_game()
ai_game.toggle_ai()
check("AI 演示已开启", ai_game.ai_mode)
check("仅打开开关尚未标记已使用（误开不影响成绩）", not ai_game.ai_used)
# 手动点击在 AI 模式下被屏蔽（棋盘不变）
arrow_before = next(a for a in ai_game.arrows if a.alive)
board_before = [row[:] for row in ai_game.board]
ai_game.try_click(*arrow_before.head)
check("AI 演示期间手动点击被屏蔽", ai_game.board == board_before)
for _ in range(600):
    ai_game.update(0.1)
    if ai_game.state != cfg.STATE_PLAY:
        break
check("AI 演示自动通关第 1 关", ai_game.state == cfg.STATE_WIN)
check("AI 演示结果带 ai 标记", ai_game.result.get("ai") is True)
check("AI 演示不写最好成绩", ai_game.progress["best"].get("1") is None)
check("AI 演示不解锁下一关", ai_game.unlocked_count() == 1)

# AI 演示期间：撤销与提示被屏蔽
ai2 = Game(save_path=os.path.join(_tmpdir, "ai2_save.json"))
ai2.start_game()
ai2.toggle_ai()
msg_before = ai2.message
ai2.undo()
check("AI 演示期间撤销被屏蔽（不改消息、不入栈）",
      ai2.message == msg_before and len(ai2.undo_stack) == 0)
ai2.hint_cell = None
ai2.show_hint()
check("AI 演示期间提示被屏蔽", ai2.hint_cell is None)

# 随机挑战失败：标题与提示文案走随机分支
rng_lose = Game(save_path=os.path.join(_tmpdir, "rng_lose.json"))
rng_lose.random_level()
rng_lose.mistakes_left = 0
rng_lose._finish_lose()
check("随机挑战失败带 random 标记", rng_lose.result.get("random") is True)

# --- 对局评星与存档 ---
save_path2 = os.path.join(_tmpdir, "score_save.json")
fresh = Game(save_path=save_path2)
fresh.start_game()
seq = solver.solve_sequence(levels.LEVELS[0])
for (r, c) in seq:
    fresh.try_click(r, c)
    fresh.update(1.0)
check("无失误通关得 3 星", fresh.state == cfg.STATE_WIN
      and fresh.result["stars"] == 3)
check("通关写入存档最好成绩",
      fresh.progress["best"].get("1", {}).get("stars") == 3)
check("通关解锁第 2 关", fresh.unlocked_count() >= 2)
check("存档文件已落盘", os.path.exists(save_path2))
check("通关结果标记新纪录", fresh.result.get("new_record") is True
      and fresh.result.get("saved") is True)
reloaded = Game(save_path=save_path2)
check("存档可被重新读取（解锁与成绩保留）",
      reloaded.unlocked_count() >= 2
      and reloaded.progress["best"].get("1", {}).get("stars") == 3)
check("有存档时开始界面主按钮为「继续第 N 关」",
      reloaded.has_progress()
      and any(b.label.startswith("继续第") for b in reloaded.buttons))
check("存档累计星数统计正确", reloaded.total_stars() == 3)
reloaded.continue_level()
check("「继续」直接进入已解锁的最后一关",
      reloaded.state == cfg.STATE_PLAY
      and reloaded.level_index == reloaded.unlocked_count() - 1)

# --- 关卡选择 ---
reloaded.to_select()
check("进入关卡选择界面", reloaded.state == cfg.STATE_SELECT)
cards = button_layout.level_card_rects()
check("关卡卡片数与总关卡数一致", len(cards) == len(levels.LEVELS))
reloaded.on_click(cards[0].center)
check("点已解锁卡片进入该关", reloaded.state == cfg.STATE_PLAY
      and reloaded.level_index == 0)
reloaded.to_select()
last = len(levels.LEVELS) - 1
check("最后一关在测试存档里仍未解锁", last >= reloaded.unlocked_count())
reloaded.on_click(cards[last].center)
check("点未解锁卡片不进入该关", reloaded.state == cfg.STATE_SELECT)
reloaded.to_start()
check("选择界面可回开始", reloaded.state == cfg.STATE_START)
# Esc 从选择界面回开始
reloaded.to_select()
key_event(pygame.K_ESCAPE)
reloaded.handle_events()
check("选择界面按 Esc 回开始", reloaded.state == cfg.STATE_START)

# --- 随机挑战 ---
rng_game = Game(save_path=os.path.join(_tmpdir, "rng_save.json"))
rng_game.random_level()
check("随机挑战进入 PLAY 且标记为随机",
      rng_game.state == cfg.STATE_PLAY and rng_game.is_random())
check("随机关卡非空", len(rng_game.arrows) >= 1)
check("随机关卡开局有可飞箭头",
      solver.greedy_pick(rng_game.board, rng_game.arrows,
                         rng_game.arrow_by_id) is not None)
best_before = dict(rng_game.progress.get("best", {}))
unlocked_before = rng_game.progress.get("unlocked", 1)
for _ in range(600):
    pick = solver.greedy_pick(rng_game.board, rng_game.arrows,
                              rng_game.arrow_by_id)
    if pick is None:
        break
    rng_game.try_click(*pick.head)
    rng_game.update(1.0)
    if rng_game.state != cfg.STATE_PLAY:
        break
check("随机挑战可被贪心通关", rng_game.state == cfg.STATE_WIN)
check("随机挑战不写入存档",
      rng_game.progress.get("best", {}) == best_before
      and rng_game.progress.get("unlocked", 1) == unlocked_before)
check("随机挑战结算标记 random", rng_game.result.get("random") is True)

# --- 生成器 / 求解器 / 评分 / 存档 纯逻辑 ---
gen_bad = 0
for seed in range(120):
    defs = generator.generate_level(random.Random(seed), 9)
    if solver.solve_sequence(defs) is None:
        gen_bad += 1
check(f"生成器 120 盘全部可解（{gen_bad} 盘异常）", gen_bad == 0)

gen_defs = generator.generate_level(random.Random(1), 12)
board, arrows = logic.build_arrows(gen_defs)
check("生成器盘面合法且四方向齐全",
      len(arrows) == 12 and len({a.direction for a in arrows}) == 4)

check("评分：0 失误 3 星 / 1 失误 2 星 / 2 失误 1 星",
      scoring.stars_for(3) == 3 and scoring.stars_for(2) == 2
      and scoring.stars_for(1) == 1)
check("评分：用时越短分越高（时间奖励单调）",
      scoring.score_for(6, 3, 0) > scoring.score_for(6, 3, 60)
      > scoring.score_for(6, 3, 200))
check("评分：超时后不会反向变高",
      scoring.score_for(6, 3, 300) == scoring.score_for(6, 3, 600))
check("时间格式化", scoring.format_time(0) == "00:00"
      and scoring.format_time(95) == "01:35")

bad_path = os.path.join(_tmpdir, "broken.json")
with open(bad_path, "w", encoding="utf-8") as f:
    f.write("{不是合法 JSON")
check("存档损坏时回退默认值", save_mod.load(bad_path) == save_mod.default_data())
check("存档写入不存在目录时不崩溃",
      save_mod.store({"unlocked": 1, "best": {}},
                     os.path.join(_tmpdir, "no", "such", "dir", "s.json"))
      in (True, False))


# ---------------- G. 模糊测试 ----------------
rng = random.Random(12345)


def random_pos():
    kind = rng.random()
    if kind < 0.75:
        c = rng.randrange(N)
        r = rng.randrange(N)
        dx = rng.choice([2, CELL - 3, CELL // 2])
        dy = rng.choice([2, CELL - 3, CELL // 2])
        return (GX + c * CELL + dx, GY + r * CELL + dy)
    return (rng.randrange(cfg.WIDTH), rng.randrange(cfg.HEIGHT))


game.load_level()
violations = []
for step in range(6000):
    game.on_click(random_pos())
    if rng.random() < 0.7:
        game.update(rng.uniform(0.001, 0.05))
    else:
        game.update(rng.uniform(0.2, 1.5))

    k = rng.random()
    if k < 0.02:
        key_event(pygame.K_r)
    elif k < 0.03:
        key_event(pygame.K_ESCAPE)
    game.handle_events()

    if game.state == cfg.STATE_PLAY:
        if not (0 <= game.mistakes_left <= cfg.MISTAKES_PER_LEVEL):
            violations.append((step, f"失误数越界 {game.mistakes_left}"))
        if game.mistakes_left == 0 and not game.anims:
            violations.append((step, "失误为 0 仍停在 PLAY"))
    if game.state in (cfg.STATE_WIN, cfg.STATE_LOSE) and game.anims:
        violations.append((step, f"{game.state} 状态仍有动画"))
    valid_ids = {a.id for a in game.arrows}
    for row in game.board:
        for v in row:
            if v not in valid_ids and v != cfg.EMPTY:
                violations.append((step, f"非法棋值 {v}"))
    # 死格检查：任何格子的 id 必须属于一支尚未清除的箭头
    for a in game.arrows:
        if not a.alive and game.board[a.head[0]][a.head[1]] == a.id:
            violations.append((step, f"死箭头的格子残留 {a.id}"))
    if any(a.done for a in game.anims):
        violations.append((step, "已完成动画未清理"))
    if len(game.anims) > 25:
        violations.append((step, f"动画泄漏 {len(game.anims)}"))
    if step % 500 == 0:
        game.draw()

check(f"6000 步随机操作零违规（{len(violations)} 处）", not violations)
for v in violations[:5]:
    print("  VIOLATION", v)

# 随机乱点也必须能走到终局（状态机不卡死）
game.level_index = 0
game.load_level()
resolved = False
for _ in range(20000):
    game.on_click(random_pos())
    game.update(0.5)
    if game.state in (cfg.STATE_WIN, cfg.STATE_LOSE):
        resolved = True
        break
check("随机乱点最终到达 WIN/LOSE（状态机不卡死）", resolved)

# 只点合法可飞箭头：必须能真正通关（模拟会玩的玩家）
game.level_index = 0
game.load_level()
won = False
for _ in range(500):
    flyable = [(a.head, a.direction) for a in game.arrows
               if a.alive and game.can_fly(*a.head)]
    if not flyable:
        break
    head, _ = rng.choice(flyable)
    game.try_click(*head)
    game.update(0.5)
    if game.state == cfg.STATE_WIN:
        won = True
        break
check("只点可飞箭头必能通关（无死局）", won)


# ---------------- H. 真实入口（main.main 线程 + 事件 + 退出） ----------------
created = []
real_game_cls = main.Game


class SpyGame(real_game_cls):
    """记录实例，便于从外部断言主循环里的真实状态。"""

    def __init__(self):
        super().__init__(save_path=os.path.join(_tmpdir, "main_save.json"))
        created.append(self)


main.Game = SpyGame
crashed = []


def run_main():
    try:
        main.main()
    except Exception as e:  # noqa: BLE001
        crashed.append(repr(e))


t = threading.Thread(target=run_main, daemon=True)
t.start()
time.sleep(2.0)
check("真实入口：主循环启动", t.is_alive() and bool(created))

live = created[0]
start_btn_rect = next(b.rect for b in live.buttons
                      if b.label in ("开始游戏", "继续第 1 关"))
click_event(start_btn_rect.center)             # 主按钮（按实际布局定位）
time.sleep(0.6)
check("真实入口：点主按钮进入 PLAY",
      live.state == cfg.STATE_PLAY and live.level_index == 0)

click_event(cell_center(4, 3))                 # 第 1 关参考解第一支
time.sleep(0.6)
check("真实入口：点可飞箭头飞出正常", t.is_alive() and not crashed)

key_event(pygame.K_r)                          # 重开
time.sleep(0.4)
live.mistakes_left = cfg.MISTAKES_PER_LEVEL
click_event(cell_center(1, 2))                 # 点被挡的箭头（左侧有 (1,1)）
time.sleep(0.8)
check("真实入口：点被挡箭头触发碰撞反馈",
      t.is_alive() and not crashed and live.mistakes_left == 2)

key_event(pygame.K_ESCAPE)
time.sleep(0.6)
check("真实入口：Esc 回开始界面", live.state == cfg.STATE_START)

main.Game = real_game_cls
pygame.event.post(pygame.event.Event(pygame.QUIT))
t.join(timeout=5.0)
check("真实入口：QUIT 后干净退出", not t.is_alive() and not crashed)
if crashed:
    print("  CRASH:", crashed)


# ---------------- 汇总 ----------------
print("---")
if FAILURES:
    print(f"SMOKE FAIL（{len(FAILURES)}/{CHECKS} 项失败）：")
    for name in FAILURES:
        print("  -", name)
    sys.exit(1)
print(f"SMOKE OK：{CHECKS} 项检查全部通过")
