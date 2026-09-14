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
import threading
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import main  # noqa: E402
from arrow import config as cfg  # noqa: E402
from arrow import levels  # noqa: E402
from arrow.core import logic  # noqa: E402
from arrow.game import Game  # noqa: E402
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
]

EXPECTED_COUNTS = [6, 8, 10]

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
game = Game()


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

# 开始界面 → 开始游戏
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

    game.update(anim.duration * 0.05)          # 100%：应完全出界
    game.draw()
    if arrow_pixels(colors) == 0:
        fully_out += 1
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


check("HUD 关卡文字已绘制", region_has_text(24, 25, 130, 26))
check("HUD 剩余箭头已绘制", region_has_text(170, 25, 120, 26))
check("HUD 剩余失误已绘制", region_has_text(300, 25, 120, 26))
check("提示信息已绘制", region_has_text(cfg.WIDTH // 2 - 160, 100, 320, 26))
check("底部快捷键提示已绘制",
      region_has_text(cfg.WIDTH // 2 - 120, 610, 240, 26))
for btn in game.buttons:
    probe = game.screen.get_at((btn.rect.x + 5, btn.rect.centery))
    check(f"按钮「{btn.label}」已绘制",
          any(near(probe, c, 60) for c in
              (cfg.BTN, cfg.BTN_HOVER, cfg.BTN_PRIMARY, cfg.BTN_PRIMARY_HOVER)))

for st, tag in [(cfg.STATE_LOSE, "失败"), (cfg.STATE_WIN, "通关")]:
    game.state = st
    game._build_buttons()
    game.draw()
    check(f"{tag}界面标题已绘制",
          region_has_text(cfg.WIDTH // 2 - 200, 220, 400, 60))
    check(f"{tag}界面提示已绘制",
          region_has_text(cfg.WIDTH // 2 - 200, 310, 400, 40))

# 开始界面文字
game.to_start()
game.draw()
check("开始界面标题已绘制",
      region_has_text(cfg.WIDTH // 2 - 200, 140, 400, 60))
check("开始界面规则已绘制",
      region_has_text(cfg.WIDTH // 2 - 260, 250, 520, 130))


# ---------------- E. 关卡数据性质 ----------------
check("每关都是箭头定义列表且非空",
      all(isinstance(lv, list) and lv for lv in levels.LEVELS))
check(f"共 3 个关卡", len(levels.LEVELS) == 3)

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

for size, sample in [(60, "箭头消除"), (22, "第关剩余失误飞出去了重开本"),
                     (20, "开始游戏下一关回"), (18, "按")]:
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
        super().__init__()
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
click_event((cfg.WIDTH // 2, 430 + 26))        # 开始游戏按钮
time.sleep(0.6)
check("真实入口：点「开始游戏」进入 PLAY",
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
