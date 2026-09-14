# -*- coding: utf-8 -*-
"""求解与提示：找可飞箭头、贪心求解整关。不依赖 pygame。

倒序摆盘（见 generator）保证「编号最大的存活箭头恒可飞」，
因此按编号从大到小贪心点击必胜，无需搜索回溯。
"""

from arrow.config import EMPTY
from arrow.core.logic import build_arrows, can_fly


def flyable_arrows(board, arrows, arrow_by_id):
    """当前所有可以飞出去的箭头（按编号从小到大）。"""
    return [a for a in arrows if a.alive and can_fly(board, arrow_by_id, *a.head)]


def greedy_pick(board, arrows, arrow_by_id):
    """贪心选一支可飞箭头（优先编号最大者，保证必胜）；没有则返回 None。

    用于「提示」高亮与「AI 演示」自动点选。
    """
    flyable = flyable_arrows(board, arrows, arrow_by_id)
    if not flyable:
        return None
    return max(flyable, key=lambda a: a.id)


def solve_sequence(defs):
    """返回一条完整通关顺序（头部坐标列表）；无法通关时返回 None。

    纯逻辑、不改动传入数据，供测试与关卡校验使用。
    """
    board, arrows = build_arrows(defs)
    arrow_by_id = {a.id: a for a in arrows}
    seq = []
    while any(a.alive for a in arrows):
        pick = greedy_pick(board, arrows, arrow_by_id)
        if pick is None:
            return None
        board[pick.head[0]][pick.head[1]] = EMPTY
        pick.alive = False
        seq.append(pick.head)
    return seq
