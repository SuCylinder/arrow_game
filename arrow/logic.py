# -*- coding: utf-8 -*-
"""核心数据模型与规则：箭头、盘面构建、路径检测。不依赖 pygame。"""

from arrow.config import DIRS, DOWN, EMPTY, LEFT, MAX_LENGTH, MIN_LENGTH, N, UP


class Arrow:
    """一支箭头：头部坐标 + 长度，身体沿头的反方向延伸。"""

    def __init__(self, aid, direction, length, head):
        self.id = aid
        self.direction = direction
        self.length = length
        self.head = (head[0], head[1])
        dr, dc = DIRS[direction]
        # cells[0] 是头，之后依次是身体各格（都在头的后方）
        self.cells = [
            (self.head[0] - dr * k, self.head[1] - dc * k) for k in range(length)
        ]
        self.alive = True


def build_arrows(defs):
    """把箭头定义列表展开成 (board, arrows)。

    board[r][c] 存箭头 id（从 1 开始）或 EMPTY；定义越界/重叠/长度非法时抛 ValueError。
    """
    board = [[EMPTY] * N for _ in range(N)]
    arrows = []
    for i, (direction, length, hr, hc) in enumerate(defs, start=1):
        if direction not in DIRS:
            raise ValueError(f"非法方向：{direction}")
        if not MIN_LENGTH <= length <= MAX_LENGTH:
            raise ValueError(f"箭头 {i} 长度非法：{length}")
        arrow = Arrow(i, direction, length, (hr, hc))
        for r, c in arrow.cells:
            if not (0 <= r < N and 0 <= c < N):
                raise ValueError(f"箭头 {i} 越界：({r}, {c})")
            if board[r][c] != EMPTY:
                raise ValueError(f"箭头 {i} 与其它箭头重叠：({r}, {c})")
            board[r][c] = i
        arrows.append(arrow)
    return board, arrows


def count_arrows(arrows):
    """统计还活着的箭头支数（不是格子数）。"""
    return sum(1 for a in arrows if a.alive)


def can_fly(board, arrow_by_id, r, c):
    """路径检测：找到 (r,c) 所属箭头，从它的头部沿方向逐格扫到边界。

    碰到任何箭头格子（别人的头或身体）都算阻挡，返回 False；
    一路扫到越界说明畅通，返回 True。自己身体在头的后方，不会被扫到。
    """
    value = board[r][c]
    if value == EMPTY:
        return False
    arrow = arrow_by_id[value]
    dr, dc = DIRS[arrow.direction]
    hr, hc = arrow.head
    nr, nc = hr + dr, hc + dc
    while 0 <= nr < N and 0 <= nc < N:  # 先判边界，保证不越界索引
        if board[nr][nc] != EMPTY:  # 有箭头挡路 → 碰撞
            return False
        nr += dr
        nc += dc
    return True  # 一路扫到出界 → 可以飞


def fly_distance(arrow):
    """滑出动画的位移（格数）：让整支箭头（含尾巴）完全滑出棋盘。

    头中心到棋盘边缘 = 整格数 + 0.5 格；
    箭尾还要额外多出：单格箭头取三角形的底边（0.216 格），
    多格箭头取身体 (length-1) + 0.56 格（到尾巴格远边缘再盖住格缝）；
    最后加 0.04 格（约 3.5px）安全余量，保证动画结束时刚好滑干净。
    """
    hr, hc = arrow.head
    if arrow.direction == UP:
        span = hr
    elif arrow.direction == DOWN:
        span = N - 1 - hr
    elif arrow.direction == LEFT:
        span = hc
    else:  # RIGHT
        span = N - 1 - hc
    if arrow.length == 1:
        tail = 0.216
    else:
        tail = (arrow.length - 1) + 0.56
    return span + 0.5 + tail + 0.04
