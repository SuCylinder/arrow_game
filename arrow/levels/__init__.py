# -*- coding: utf-8 -*-
"""关卡数据包。

每关是箭头定义列表，一支箭头写成一个元组：(方向, 长度, 头行, 头列)
头在箭头最前端，身体沿「头的反方向」延伸：
比如 (UP, 3, 1, 0) 表示头在 (1,0)，身体占 (2,0)、(3,0)，整支朝上。
三关的箭头都带身体（长度 2~4），没有单格短箭头。

制作方式：从空盘开始按「点击顺序的倒序」逐支摆放，每摆一支都要求此刻
能飞出去，因此每关天然存在一条通关顺序（各关文件注释里的参考解）。
"""

from arrow.levels.level1 import LEVEL as LEVEL_1
from arrow.levels.level2 import LEVEL as LEVEL_2
from arrow.levels.level3 import LEVEL as LEVEL_3

LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3]

__all__ = ["LEVELS"]
