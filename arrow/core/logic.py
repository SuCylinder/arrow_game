# -*- coding: utf-8 -*-
"""核心数据模型与规则：箭头、盘面构建、路径检测。不依赖 pygame。

作业基础版规则：箭头的方向分上、下、左、右四种，全部占一个格子。
点击某支箭头后，检查它前进方向上的路径（同一行或同一列、箭头与边界
之间）是否还有其它箭头：没有就能飞出棋盘，有就算碰撞。
"""

from arrow.config import DIRS, DOWN, EMPTY, FLY_MARGIN, HEAD_BASE, LEFT, N, UP


class Arrow:
    """一支单格箭头：占一个格子，有一个指向（也是它飞出的方向）。"""

    def __init__(self, aid, direction, r, c):
        self.id = aid
        self.direction = direction
        self.head = (r, c)  # 单格箭头：头就是它自己所在的格子
        self.alive = True


def build_arrows(defs):
    """把箭头定义列表展开成 (board, arrows)。

    定义格式：(方向, 行, 列)。board[r][c] 存箭头 id（从 1 开始）或 EMPTY；
    方向非法、越界、重叠时抛 ValueError。
    """
    board = [[EMPTY] * N for _ in range(N)]
    arrows = []
    for i, (direction, r, c) in enumerate(defs, start=1):
        if direction not in DIRS:
            raise ValueError(f"箭头 {i} 方向非法：{direction}")
        if not (0 <= r < N and 0 <= c < N):
            raise ValueError(f"箭头 {i} 越界：({r}, {c})")
        if board[r][c] != EMPTY:
            raise ValueError(f"箭头 {i} 与其它箭头重叠：({r}, {c})")
        board[r][c] = i
        arrows.append(Arrow(i, direction, r, c))
    return board, arrows


def count_arrows(arrows):
    """统计还活着的箭头支数。"""
    return sum(1 for a in arrows if a.alive)


def can_fly(board, arrow_by_id, r, c):
    """路径检测：从箭头所在格沿它的方向逐格扫到边界。

    碰到任何其它箭头（不论朝向）都算阻挡，返回 False；
    一路扫到越界说明畅通，返回 True。空格的格子返回 False。
    """
    value = board[r][c]
    if value == EMPTY:
        return False
    arrow = arrow_by_id[value]
    dr, dc = DIRS[arrow.direction]
    nr, nc = r + dr, c + dc
    while 0 <= nr < N and 0 <= nc < N:  # 先判边界，保证不越界索引
        if board[nr][nc] != EMPTY:  # 路径上有别的箭头 → 碰撞
            return False
        nr += dr
        nc += dc
    return True  # 一路扫到出界 → 可以飞


def fly_distance(arrow):
    """滑出动画的位移（格数）：让整支箭头（含头部三角形）完全滑出棋盘。

    头中心到棋盘边缘 = 整格数 + 0.5 格（span）；
    箭尾还要多出三角形底边（HEAD_BASE 格）；
    最后加 FLY_MARGIN 格安全余量，保证动画结束时刚好滑干净。
    """
    hr, hc = arrow.head
    if arrow.direction == UP:
        span = hr + 0.5
    elif arrow.direction == DOWN:
        span = N - hr - 0.5
    elif arrow.direction == LEFT:
        span = hc + 0.5
    else:  # RIGHT
        span = N - hc - 0.5
    return span + HEAD_BASE + FLY_MARGIN
