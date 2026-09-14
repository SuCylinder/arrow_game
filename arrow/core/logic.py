# -*- coding: utf-8 -*-
"""核心数据模型与规则：箭头、盘面构建、路径检测。不依赖 pygame。"""

from arrow.config import (
    BODY_R,
    DIRS,
    DOWN,
    EMPTY,
    FLY_MARGIN,
    HEAD_BASE,
    LEFT,
    MAX_LENGTH,
    MIN_LENGTH,
    N,
    TAIL_EXT,
    UP,
)


class Arrow:
    """一支箭头：头部格子 + 身体格子路径（显式列出，可以弯折）。

    cells[0] 是头部；cells[1] 是「脖子」，必须紧贴头的正后方；
    之后每一格都与前一格四方向相邻，因此身体可以拐弯（蛇形）。
    length 是总格数（含头）。direction 是头的指向，也是整支飞行的方向。
    """

    def __init__(self, aid, direction, cells):
        self.id = aid
        self.direction = direction
        self.cells = [(r, c) for (r, c) in cells]
        self.head = self.cells[0]
        self.length = len(self.cells)
        self.alive = True


def _check_shape(i, direction, cells):
    """校验单支箭头的形状：方向、长度、邻接、脖子。"""
    if direction not in DIRS:
        raise ValueError(f"箭头 {i} 方向非法：{direction}")
    if not cells:
        raise ValueError(f"箭头 {i} 路径为空")
    length = len(cells)
    if not MIN_LENGTH <= length <= MAX_LENGTH:
        raise ValueError(f"箭头 {i} 长度非法：{length}")
    if len(set(cells)) != length:
        raise ValueError(f"箭头 {i} 路径有重复格子：{cells}")

    hr, hc = cells[0]
    dr, dc = DIRS[direction]
    if length >= 2 and cells[1] != (hr - dr, hc - dc):
        raise ValueError(f"箭头 {i} 第 2 格必须是头正后方（脖子）：{cells[1]}")

    for k in range(2, length):
        pr, pc = cells[k - 1]
        r, c = cells[k]
        if abs(r - pr) + abs(c - pc) != 1:
            raise ValueError(f"箭头 {i} 身体不连续：{cells[k - 1]} → {cells[k]}")


def build_arrows(defs):
    """把箭头定义列表展开成 (board, arrows)。

    定义格式：(方向, [(头行, 头列), (身体格1), ...])
    头是字段 0，脖子（字段 1）必须在头正后方，其余身体格四方向相邻，
    因此身体可以拐弯；整支飞行方向始终是头的指向。
    board[r][c] 存箭头 id（从 1 开始）或 EMPTY；定义非法时抛 ValueError。
    """
    board = [[EMPTY] * N for _ in range(N)]
    arrows = []
    for i, (direction, cells) in enumerate(defs, start=1):
        _check_shape(i, direction, cells)
        arrow = Arrow(i, direction, cells)
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
    """路径检测：找到 (r,c) 所属箭头，检查它整支「平移出去」会不会撞到别人。

    整支箭头沿头部方向刚性平移，因此身上每一格都会扫出一条前进走廊；
    只要任何一条走廊被「别的箭头」的格子挡住，就算碰撞。
    自己的格子不算阻挡（所有格子一起平移，不会自己撞自己，
    哪怕身体弯到了头部前方也一样）。
    一路扫到越界说明畅通，返回 True。
    """
    value = board[r][c]
    if value == EMPTY:
        return False
    arrow = arrow_by_id[value]
    dr, dc = DIRS[arrow.direction]
    for (cr, cc) in arrow.cells:  # 每一格都扫一遍自己的前进走廊
        nr, nc = cr + dr, cc + dc
        while 0 <= nr < N and 0 <= nc < N:  # 先判边界，保证不越界索引
            v = board[nr][nc]
            if v != EMPTY and v != arrow.id:  # 别人的格子挡路 → 碰撞
                return False
            nr += dr
            nc += dc
    return True  # 所有格子的走廊都畅通 → 可以飞


def fly_track(arrow):
    """蛇形飞出的轨道与总位移（供动画使用）。

    轨道从「尾巴延伸端」出发，经身体各格（尾 → 头），再沿飞行方向出界；
    出界部分不显式列出，动画按飞行方向线性外推。返回 (points, total)：
      points：网格坐标 (行, 列) 的点列，float，索引 0 是尾端、-1 是头；
      total：让整支箭头（含尾端圆头）完全滑出棋盘的滑行距离（格数）。

    头到边界的距离（span）+ 伸直后的身体长度（length-1）+ 尾巴延伸
    （TAIL_EXT 格，仅多格箭头）+ 末端圆头半径 + 安全余量。
    """
    cells = arrow.cells
    if arrow.length == 1:
        hr, hc = cells[0]
        points = [(float(hr), float(hc))]
        base = 0.0
    else:
        (tr, tc), (pr, pc) = cells[-1], cells[-2]
        dr, dc = tr - pr, tc - pc
        points = [(tr + dr * TAIL_EXT, tc + dc * TAIL_EXT)]
        points += [(float(r), float(c)) for (r, c) in reversed(cells)]
        base = TAIL_EXT + (arrow.length - 1)

    hr, hc = arrow.head
    if arrow.direction == UP:
        span = hr + 0.5
    elif arrow.direction == DOWN:
        span = N - hr - 0.5
    elif arrow.direction == LEFT:
        span = hc + 0.5
    else:  # RIGHT
        span = N - hc - 0.5
    rear = HEAD_BASE if arrow.length == 1 else BODY_R
    return points, base + span + rear + FLY_MARGIN
