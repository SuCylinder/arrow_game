# -*- coding: utf-8 -*-
"""随机关卡生成器：保证生成的关卡可以通关（不会出现死局）。不依赖 pygame。

原理：从空盘开始，按「点击顺序的倒序」逐个摆放箭头，每摆一支都要求
此刻它可以飞出去（它前方没有别的箭头）。这样构造出的盘面有一条必然
存在的通关顺序——每次都能找到「编号最大的存活箭头」可飞（摆放它时
比它晚放的箭头都还没摆上），因此贪心求解必胜。

生成后仍会做一次贪心验证，异常情况直接判失败并重试，双保险。
"""

import random

from arrow.config import DIRS, EMPTY, N, RANDOM_ARROW_COUNT

from arrow.core.logic import build_arrows, can_fly


def _place_level(rng, count):
    """倒序摆盘，返回箭头定义列表；途中无解时返回 None。"""
    board = [[EMPTY] * N for _ in range(N)]
    placed = []
    for aid in range(1, count + 1):
        candidates = []
        for r in range(N):
            for c in range(N):
                if board[r][c] != EMPTY:
                    continue
                for direction in DIRS:
                    # 试摆：此刻（只含已摆放的箭头）它能飞出去吗？
                    found = False
                    dr, dc = DIRS[direction]
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < N and 0 <= nc < N:
                        if board[nr][nc] != EMPTY:
                            break
                        nr += dr
                        nc += dc
                    else:
                        found = True
                    if found:
                        candidates.append((direction, r, c, aid))
        if not candidates:
            return None
        direction, r, c, aid = rng.choice(candidates)
        board[r][c] = aid
        placed.append((direction, r, c))
    return placed


def _greedy_ok(defs):
    """用「每次点编号最大者可飞」的贪心策略验证能清空。"""
    board, arrows = build_arrows(defs)
    arrow_by_id = {a.id: a for a in arrows}
    while arrows:
        alive = [a for a in arrows if a.alive]
        pick = None
        for a in sorted(alive, key=lambda x: -x.id):  # 编号从大到小
            if can_fly(board, arrow_by_id, *a.head):
                pick = a
                break
        if pick is None:
            return False
        board[pick.head[0]][pick.head[1]] = EMPTY
        pick.alive = False
        arrows = [a for a in arrows if a.alive]
    return True


def _is_balanced(board):
    """四方向齐全、至少占 3 行 3 列，避免过于集中的无聊盘面。"""
    cells = [(r, c) for r in range(N) for c in range(N) if board[r][c] != EMPTY]
    if not cells:
        return False
    ids = {board[r][c] for r, c in cells}
    if len(ids) < 4:
        return False
    if len({r for r, _ in cells}) < 3 or len({c for _, c in cells}) < 3:
        return False
    return True


def generate_level(rng=None, count=None):
    """生成一关随机箭头定义，返回 (方向, 行, 列) 列表。

    rng 可传 random.Random(seed) 以获得可复现结果；
    count 缺省时在 RANDOM_ARROW_COUNT 范围内随机取。
    """
    if rng is None:
        rng = random.Random()
    if count is None:
        lo, hi = RANDOM_ARROW_COUNT
        count = rng.randint(lo, hi)
    for _ in range(2000):
        placed = _place_level(rng, count)
        if placed is None:
            continue
        defs = [(d, r, c) for (d, r, c) in placed]
        board, _ = build_arrows(defs)
        if not _is_balanced(board):
            continue
        if not _greedy_ok(defs):
            continue
        return defs
    raise RuntimeError("随机关卡生成失败（重试次数用尽）")
