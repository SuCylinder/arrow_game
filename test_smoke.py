# -*- coding: utf-8 -*-
"""箭头消除游戏测试（无头运行，不需要真实窗口和显示器）。

覆盖：
  A 通关与状态机      参考解法逐关通关（只点头部）、按钮/Esc/R、下一关/回开始
  B 点击与路径检测    can_fly 边界/阻挡、点身体无效、蛇形身体不堵自己、形状校验
  C 滑出动画几何      长度 1~5 × 直/弯 × 各方向：中途可见、结束完全出界、无空转
  D 渲染             箭头朝向、身体压暗色（含拐点）、三段 HUD、按钮、结果界面
  E 关卡数据性质      定义合法、长度 1~5、全部有身体、蛇形占比、参考解、倒序摆盘
  F 碰撞与失败窗口    整支晃动变色、扣失误、归零后锁操作、不误判通关
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
from arrow.core import logic, utils  # noqa: E402
from arrow.game import Game  # noqa: E402
from arrow.view.animations import FlyAnim, ShakeAnim  # noqa: E402
from arrow.view.ui import make_font  # noqa: E402

N = cfg.N
CELL = cfg.CELL
GX, GY, GW = cfg.GRID_X, cfg.GRID_Y, cfg.GRID_W

# 各关参考通关顺序（都是头部坐标，与 arrow/levels/levelN.py 注释一致）
ORDERS = [
    [(1, 2), (4, 1), (3, 3), (1, 0), (1, 4)],
    [(4, 2), (1, 0), (4, 4), (0, 1), (3, 3), (2, 2), (4, 0)],
    [(0, 0), (4, 0), (4, 4), (0, 2), (3, 0), (4, 3), (2, 4), (1, 4)],
]

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


def turns_of(cells):
    """数一条路径的拐弯次数。"""
    t = 0
    for k in range(1, len(cells) - 1):
        d1 = (cells[k][0] - cells[k - 1][0], cells[k][1] - cells[k - 1][1])
        d2 = (cells[k + 1][0] - cells[k][0], cells[k + 1][1] - cells[k][1])
        if d1 != d2:
            t += 1
    return t


pygame.init()
check("main.py 复用 arrow.game.Game", main.Game is Game)
game = Game()


# ---------------- A. 通关与状态机 ----------------
for idx, order in enumerate(ORDERS):
    game.level_index = idx
    game.load_level()
    check(f"第{idx + 1}关载入后为 PLAY", game.state == cfg.STATE_PLAY)
    n_arrows = logic.count_arrows(game.arrows)
    check(f"第{idx + 1}关箭头支数 {n_arrows} 在 5~8", 5 <= n_arrows <= 8)
    heads = [a.head for a in game.arrows]
    check(f"第{idx + 1}关参考解覆盖全部 {n_arrows} 支箭头",
          sorted(order) == sorted(heads))
    base = game.mistakes_left
    for step, (r, c) in enumerate(order):
        arrow = game.arrow_by_id[game.board[r][c]]
        check(f"第{idx + 1}关第{step + 1}步 ({r},{c}) 处是头部且可飞",
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
# 直线朝上：头 (3,2)，身体 (4,2)
board, arrows = logic.build_arrows([(cfg.UP, [(3, 2), (4, 2)])])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
game.state = cfg.STATE_PLAY
game.mistakes_left = cfg.MISTAKES_PER_LEVEL
game.anims.clear()

check("自己身体不挡自己（直身朝上可飞）", game.can_fly(3, 2))

# 点身体格子：不触发动画、不扣失误、提示只能点头部
game.try_click(4, 2)
check("点身体格子无效（无动画）", not game.anims)
check("点身体格子不扣失误", game.mistakes_left == cfg.MISTAKES_PER_LEVEL)
check("点身体格子有提示", "头部" in game.message)

# 点头部正常飞出
game.try_click(3, 2)
check("点头部触发飞出动画", len(game.anims) == 1
      and isinstance(game.anims[0], FlyAnim))
game.update(1.0)
check("整支箭头的所有格都被清除", game.board[3][2] == cfg.EMPTY
      and game.board[4][2] == cfg.EMPTY)
check("箭头活状态置为 False", not arrows[0].alive)

# 别人的身体会挡路：直身朝上的身体 (4,2) 挡住 (4,4) 朝左的箭头
board, arrows = logic.build_arrows([
    (cfg.UP, [(3, 2), (4, 2)]),          # 头 (3,2)，身体 (4,2)
    (cfg.LEFT, [(4, 4)]),                # 头 (4,4)，朝左，路径上会撞到 (4,2)
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
game.anims.clear()
check("别人的身体会挡路（(4,4)左 → 被 (4,2) 身体挡）", not game.can_fly(4, 4))

# 身体在路径上仍会被挡 / 路径不经过身体则可飞
board, arrows = logic.build_arrows([
    (cfg.UP, [(3, 0), (4, 0)]),          # 头 (3,0)，身体 (4,0)
    (cfg.LEFT, [(4, 4)]),                # 朝左，路径 (4,3)(4,2)(4,1)(4,0)
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
game.anims.clear()
check("身体在路径上仍会被挡（(4,0) 身体挡 (4,4)）", not game.can_fly(4, 4))
board, arrows = logic.build_arrows([
    (cfg.UP, [(3, 1), (4, 1)]),          # 头 (3,1)，身体 (4,1)
    (cfg.LEFT, [(2, 3), (2, 4)]),        # 头 (2,3) 朝左，路径 (2,2)(2,1)(2,0) 不经过身体
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
check("路径不经过身体时可飞", game.can_fly(2, 3))

# ---- 蛇形专项 ----
# 蛇身向前拐：头 (3,2) 朝上，身体 (4,2)→(4,1)，(4,1) 在头前方走廊左侧
# 自己不吃自己：整支平移，身体所有格一起走，不互相阻挡
board, arrows = logic.build_arrows([
    (cfg.UP, [(3, 2), (4, 2), (4, 1)]),
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
check("蛇身拐到前方走廊时自己仍可飞", game.can_fly(3, 2))

# 但别人的身体会挡：另一支箭头的身体格 (1,2) 正好在自家走廊里
board, arrows = logic.build_arrows([
    (cfg.UP, [(3, 2), (4, 2), (4, 1)]),  # 头 (3,2)，走廊 (2,2)(1,2)(0,2)
    (cfg.UP, [(0, 2), (1, 2)]),          # 头 (0,2)，身体 (1,2) 挡住走廊
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
game.anims.clear()
check("别人的身体进入自家走廊 → 不可飞", not game.can_fly(3, 2))

# 形状校验：不邻接、重复、脖子不在头正后方、超长
bad_defs = [
    ("方向非法", [(cfg.UP, [(3, 2), (4, 2)])], 99),
    ("脖子不在头正后方", [(cfg.UP, [(3, 2), (3, 3)])], None),
    ("身体不连续", [(cfg.UP, [(3, 2), (4, 2), (4, 4)])], None),
    ("路径重复格", [(cfg.UP, [(3, 2), (4, 2), (4, 2)])], None),
    ("长度超上限", [(cfg.UP, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (4, 1)])], None),
]
for label, defs, bad_dir in bad_defs:
    if bad_dir is not None:
        defs = [(bad_dir, defs[0][1])]
    try:
        logic.build_arrows(defs)
        check(f"非法定义抛 ValueError：{label}", False)
    except ValueError:
        check(f"非法定义抛 ValueError：{label}", True)

# 越界与重叠
try:
    logic.build_arrows([(cfg.UP, [(0, 1), (1, 1), (1, 0), (0, 0), (0, -1)])])
    check("越界定义抛 ValueError", False)
except ValueError:
    check("越界定义抛 ValueError", True)
try:
    logic.build_arrows([(cfg.UP, [(3, 0), (4, 0)]), (cfg.UP, [(4, 0), (4, 1)])])
    check("重叠定义抛 ValueError", False)
except ValueError:
    check("重叠定义抛 ValueError", True)

# 基础 can_fly 边界测试
board, arrows = logic.build_arrows([
    (cfg.UP, [(0, 0)]), (cfg.RIGHT, [(0, 4)]),
    (cfg.LEFT, [(4, 0)]), (cfg.DOWN, [(4, 4)]),
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
check("四角朝外均可飞（边界不越界）",
      all(game.can_fly(r, c) for r, c in [(0, 0), (0, 4), (4, 0), (4, 4)]))

board, arrows = logic.build_arrows([
    (cfg.RIGHT, [(2, 0)]), (cfg.UP, [(2, 3)]),
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
check("同行中间有阻挡 → 不可飞", not game.can_fly(2, 0))

board, arrows = logic.build_arrows([
    (cfg.DOWN, [(1, 1)]), (cfg.UP, [(4, 1)]),
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
check("同列最远端有阻挡 → 不可飞", not game.can_fly(1, 1))

# 最长 5 格箭头（含蛇形）：头朝上，身体向下再折向右
board, arrows = logic.build_arrows([(cfg.UP, [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)])])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
check("长度 5 蛇形箭头构造正确",
      arrows[0].cells == [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)])
check("长度 5 蛇形箭头可飞", game.can_fly(0, 0))


# ---------------- C. 滑出动画几何（像素采样） ----------------
def arrow_pixels(colors, step=6):
    """扫描棋盘区域，统计属于这些颜色的像素数。"""
    count = 0
    for x in range(GX, GX + GW, step):
        for y in range(GY, GY + GW, step):
            p = game.screen.get_at((x, y))
            for color in colors:
                if near(p, color, 12):
                    count += 1
                    break
    return count


# 直线用例：长度 1~5 × 各方向 × 若干头位置
fly_cases = []
for length in (1, 2, 3, 4, 5):
    for r in range(0, N - length + 1):
        fly_cases.append((cfg.UP, [(r + k, 2) for k in range(length)]))
    for r in range(length - 1, N):
        fly_cases.append((cfg.DOWN, [(r - k, 2) for k in range(length)]))
    for c in range(0, N - length + 1):
        fly_cases.append((cfg.LEFT, [(2, c + k) for k in range(length)]))
    for c in range(length - 1, N):
        fly_cases.append((cfg.RIGHT, [(2, c - k) for k in range(length)]))

# 蛇形用例：明显拐弯的几支（脖子必须在头正后方）
fly_cases += [
    (cfg.UP, [(3, 2), (4, 2), (4, 1)]),                  # 拐 1 次
    (cfg.DOWN, [(2, 0), (1, 0), (1, 1), (0, 1)]),        # 拐 2 次
    (cfg.LEFT, [(4, 3), (4, 4), (3, 4)]),                # 拐 1 次
    (cfg.RIGHT, [(0, 1), (0, 0), (1, 0), (1, 1)]),       # 拐 2 次
    (cfg.DOWN, [(2, 4), (1, 4), (1, 3), (0, 3), (0, 2)]),  # 拐 3 次
]

mid_visible = 0
fully_out = 0
order_bad = []
spacing_bad = []
trail_bad = []
bad = []


def inside(pt):
    """格坐标（中心出界口径）是否仍在棋盘内。"""
    r, c = pt
    return -0.5 <= r <= N - 0.5 and -0.5 <= c <= N - 0.5


for (d, cells) in fly_cases:
    board, arrows = logic.build_arrows([(d, cells)])
    game.board, game.arrows = board, arrows
    game.arrow_by_id = {a.id: a for a in arrows}
    game.anims.clear()
    game.state = cfg.STATE_PLAY
    game.mistakes_left = cfg.MISTAKES_PER_LEVEL
    r, c = cells[0]
    if not game.can_fly(r, c):
        bad.append(("不可飞", d, cells))
        continue
    game.try_click(r, c)
    anim = game.anims[0]
    colors = [cfg.ARROW_COLORS[d], utils.darken(cfg.ARROW_COLORS[d])]
    label = (d, cells)
    expected = [cfg.TAIL_EXT] + [1.0] * (len(cells) - 1) if len(cells) > 1 else []

    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    # ① 起始瞬间形状 = 静止形状：间距精确 = TAIL_EXT + 1.0×k
    gp = anim.grid_points()
    for k in range(len(gp) - 1):
        if abs(dist(gp[k], gp[k + 1]) - expected[k]) > 1e-9:
            spacing_bad.append((label, "起始", k))

    # ② 滑行中按时间顺序采样：身体不拉伸（弯折处直线距离只缩不长）
    base = cfg.TAIL_EXT + (len(cells) - 1) if len(cells) > 1 else None
    p_base = None
    checkpoints = [0.25, 0.5, 0.75]
    if base is not None:
        p_base = 1 - (1 - base / anim.total) ** (1 / 3)
        checkpoints.append(p_base)
    for p in sorted(checkpoints):
        game.update(max(0.0, anim.duration * p - anim.elapsed))
        gp = anim.grid_points()
        for k in range(len(gp) - 1):
            if dist(gp[k], gp[k + 1]) > expected[k] + 1e-9:
                spacing_bad.append((label, p, k))
        if p == 0.5:
            game.draw()
            if arrow_pixels(colors) > 0:
                mid_visible += 1
        # ③ 尾巴延伸点滑到头部原格（整段身体流过一次）
        if base is not None and p == p_base:
            if abs(gp[0][0] - r) > 1e-9 or abs(gp[0][1] - c) > 1e-9:
                trail_bad.append((label, gp[0]))

    # ④ 头先出、尾后出：细采样找头中心出界的滑行量
    s_head = None
    for i in range(1, 201):
        s = anim.total * i / 200
        if not inside(anim.nodes(s)[-1]):
            s_head = s
            break
    if s_head is None:
        order_bad.append((label, "头未在时长内出界"))
    else:
        if not all(inside(pt) for pt in anim.nodes(s_head)[:-1]):
            order_bad.append((label, "头出界时身体已有节点出界"))
        if not all(not inside(pt) for pt in anim.nodes(anim.total)):
            order_bad.append((label, "结束时仍有节点未出界"))

    # ⑤ 结束：完全出界 + 棋盘数据清除
    game.update(anim.duration - anim.elapsed)
    game.draw()
    if arrow_pixels(colors) == 0:
        fully_out += 1
    if game.board[r][c] != cfg.EMPTY:
        bad.append(("结束未清除", d, cells))

total = len(fly_cases)
check(f"飞出用例全部可飞（{total} 例）", not bad)
check(f"飞出动画中途仍可见（{mid_visible}/{total}）", mid_visible == total)
check(f"飞出动画结束完全出界（{fully_out}/{total}）", fully_out == total)
check(f"蛇形跟随：起始形状=静止形状，滑行不拉伸（{total} 例）",
      not spacing_bad)
check(f"蛇形跟随：头先出尾后出（{total} 例）", not order_bad)
check(f"蛇形跟随：尾巴延伸点流过头部原格（{total} 例）", not trail_bad)
for item in (bad + spacing_bad + order_bad + trail_bad)[:5]:
    print("  BAD:", item)


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
check(f"头部朝向检查已覆盖（{dir_checked} 支）", dir_checked >= 5)

# 多格箭头：每个身体格中心应是压暗的身体色（含拐点格）
body_checked = 0
for arrow in game.arrows:
    if arrow.length < 2:
        continue
    color = cfg.ARROW_COLORS[arrow.direction]
    body_color = utils.darken(color)
    for (br, bc) in arrow.cells[1:]:
        center = game.screen.get_at(cell_center(br, bc))
        check(f"({br},{bc}) 身体格中心为压暗色", near(center, body_color))
        body_checked += 1
    check(f"箭头身体色与头部色可区分",
          not near(body_color, color, 8))
check(f"多格箭头身体渲染已覆盖（{body_checked} 格）", body_checked >= 5)

# 头部格中心应是头部色（三角覆盖中心）
head_checked = 0
for arrow in game.arrows:
    hr, hc = arrow.head
    center = game.screen.get_at(cell_center(hr, hc))
    check(f"({hr},{hc}) 头部格中心为头部色",
          near(center, cfg.ARROW_COLORS[arrow.direction]))
    head_checked += 1
check(f"头部渲染已覆盖（{head_checked} 支）", head_checked >= 5)

# 拐点渲染：对每支蛇形箭头的拐点格中心采样
turn_pixels = 0
for arrow in game.arrows:
    if arrow.length < 3:
        continue
    cells = arrow.cells
    body_color = utils.darken(cfg.ARROW_COLORS[arrow.direction])
    for k in range(1, len(cells) - 1):
        d1 = (cells[k][0] - cells[k - 1][0], cells[k][1] - cells[k - 1][1])
        d2 = (cells[k + 1][0] - cells[k][0], cells[k + 1][1] - cells[k][1])
        if d1 != d2:  # 拐点
            center = game.screen.get_at(cell_center(*cells[k]))
            check(f"拐点格 {cells[k]} 为身体色（圆角覆盖）",
                  near(center, body_color))
            turn_pixels += 1
check(f"蛇形拐点渲染已覆盖（{turn_pixels} 处）", turn_pixels >= 2)


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


# ---------------- E. 关卡数据性质 ----------------
check("每关都是箭头定义列表且非空",
      all(isinstance(lv, list) and lv for lv in levels.LEVELS))

for idx, defs in enumerate(levels.LEVELS):
    board, arrows = logic.build_arrows(defs)       # 非法定义会抛异常
    check(f"第{idx + 1}关定义合法（不越界不重叠、邻接正确）", True)
    check(f"第{idx + 1}关箭头支数在 5~8", 5 <= len(arrows) <= 8)
    length_list = [a.length for a in arrows]
    check(f"第{idx + 1}关长度都在 {cfg.MIN_LENGTH}~{cfg.MAX_LENGTH}",
          all(cfg.MIN_LENGTH <= x <= cfg.MAX_LENGTH for x in length_list))
    check(f"第{idx + 1}关全部箭头都有身体（长度≥2）",
          all(x >= 2 for x in length_list))
    check(f"第{idx + 1}关长度混合（至少 2 种长度）",
          len(set(length_list)) >= 2)
    turn_list = [turns_of(a.cells) for a in arrows]
    check(f"第{idx + 1}关蛇形箭头 ≥2 支（拐弯数 {turn_list}）",
          sum(1 for t in turn_list if t >= 1) >= 2)
    # 每支箭头的所有格都指向它自己
    id_ok = all(board[r][c] == a.id for a in arrows for (r, c) in a.cells)
    check(f"第{idx + 1}关棋盘 id 与箭头 cells 一致", id_ok)
    # 脖子约束：第 2 格必须在头正后方
    neck_ok = all(
        a.cells[1] == (a.head[0] - DIRS[a.direction][0],
                       a.head[1] - DIRS[a.direction][1])
        for a in arrows if a.length >= 2)
    check(f"第{idx + 1}关脖子（第 2 格）都在头正后方", neck_ok)
    # 参考解覆盖全部箭头，且倒序摆盘每步可飞
    game.board = empty_board()
    game.arrow_by_id = {}
    reverse_ok = True
    real_board, real_arrows = logic.build_arrows(defs)
    for (r, c) in reversed(ORDERS[idx]):
        a = next(x for x in real_arrows if x.id == real_board[r][c])
        for (rr, cc) in a.cells:
            game.board[rr][cc] = a.id
        game.arrow_by_id[a.id] = a
        if not game.can_fly(r, c):
            reverse_ok = False
            break
    check(f"第{idx + 1}关倒序摆盘每步可飞（制作方式成立）", reverse_ok)
    # 开局存在可飞箭头（不会开局死局）
    game.board, game.arrows = logic.build_arrows(defs)
    game.arrow_by_id = {a.id: a for a in game.arrows}
    n_flyable = sum(1 for a in game.arrows if game.can_fly(*a.head))
    check(f"第{idx + 1}关开局存在可飞箭头（{n_flyable} 支）", n_flyable >= 1)

check("每关失误次数为 3", cfg.MISTAKES_PER_LEVEL == 3)

for size, sample in [(60, "箭头消除"), (22, "第关剩余失误飞出去了重开本"),
                     (20, "开始游戏下一关回"), (18, "按")]:
    font = make_font(size)
    metrics = font.metrics(sample)
    check(f"{size}px 字体覆盖「{sample}」",
          metrics is not None and all(m is not None for m in metrics))


# ---------------- F. 碰撞与失败窗口 ----------------
game.level_index = 0
game.load_level()
board, arrows = logic.build_arrows([
    (cfg.RIGHT, [(2, 2), (2, 1)]),     # 头 (2,2)，身体 (2,1)
    (cfg.LEFT, [(2, 4)]),              # 挡在 (2,2) 右侧
])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
game.anims.clear()
game.mistakes_left = 3
game.try_click(2, 2)
check("碰撞后失误 3→2", game.mistakes_left == 2)
check("碰撞生成晃动动画",
      len(game.anims) == 1 and isinstance(game.anims[0], ShakeAnim))
check("碰撞后整支箭头仍在原地", game.board[2][2] != cfg.EMPTY
      and game.board[2][1] != cfg.EMPTY)
game.update(0.25)
check("晃动中途头部颜色变红",
      game.anims[0].head_color() != cfg.ARROW_COLORS[cfg.RIGHT])
check("晃动中途身体颜色跟随变红",
      game.anims[0].body_color()
      != utils.darken(cfg.ARROW_COLORS[cfg.RIGHT]))
game.update(0.5)
check("晃动结束箭头不消失",
      game.board[2][2] != cfg.EMPTY and game.board[2][1] != cfg.EMPTY)
check("晃动结束仍在 PLAY", game.state == cfg.STATE_PLAY)

# 失误归零后的窗口期必须锁住操作，防止误判通关
game.mistakes_left = 1
game.anims.clear()
game.try_click(2, 2)
check("失误归零时停在 PLAY（等动画）",
      game.state == cfg.STATE_PLAY and game.mistakes_left == 0)
before = sum(1 for a in game.arrows if a.alive)
game.try_click(2, 0)
check("失误归零后的点击被拦截",
      sum(1 for a in game.arrows if a.alive) == before
      and len(game.anims) == 1 and game.mistakes_left == 0)
game.update(1.0)
check("晃动结束进入 LOSE", game.state == cfg.STATE_LOSE)
check("失败时箭头未被清空（不会误判通关）",
      sum(1 for a in game.arrows if a.alive) > 0)

# 空格点击不扣失误
game.level_index = 0
game.load_level()
game.board = empty_board()
for a in game.arrows:
    a.alive = True
game.mistakes_left = 3
game.try_click(0, 0)
check("点空格提示且不扣失误", game.mistakes_left == 3 and "空格" in game.message)

# 同一支箭头动画期间连点锁定
board, arrows = logic.build_arrows([(cfg.RIGHT, [(2, 2), (2, 1)])])
game.board, game.arrows = board, arrows
game.arrow_by_id = {a.id: a for a in arrows}
game.anims.clear()
game.try_click(2, 2)
game.try_click(2, 2)
check("飞出动画期间连点被锁", len(game.anims) == 1)
game.update(1.0)
check("飞出结束后整支数据清除",
      game.board[2][2] == cfg.EMPTY and game.board[2][1] == cfg.EMPTY)


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
        if not a.alive:
            for (r, c) in a.cells:
                if game.board[r][c] == a.id:
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

click_event(cell_center(1, 2))                 # 第 1 关 (1,2) 头部（含蛇身）
time.sleep(0.6)
check("真实入口：点蛇形箭头头部运行正常", t.is_alive() and not crashed)

click_event(cell_center(4, 1))                 # 第 1 关 (4,1) 头部（拐 2 次）
time.sleep(0.6)
check("真实入口：点第二条蛇形箭头运行正常", t.is_alive() and not crashed)

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
