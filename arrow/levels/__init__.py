# -*- coding: utf-8 -*-
"""关卡数据包。

每关是箭头定义列表，一支箭头写成一个元组：(方向, 行, 列)。
箭头都是单格，方向分上、下、左、右四种；点击后沿它的方向检查
同一行或同一列、箭头与边界之间是否还有其它箭头。

制作方式：从空盘开始按「点击顺序的倒序」逐支摆放，每摆一支都要求此刻
能飞出去，因此每关天然存在一条通关顺序（各关文件注释里的参考解）。
又因为移走箭头只会让路径更空旷，初始只要有一支可飞，就不会出现死局。
"""

from arrow.levels.level1 import LEVEL as LEVEL_1
from arrow.levels.level2 import LEVEL as LEVEL_2
from arrow.levels.level3 import LEVEL as LEVEL_3

LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3]

__all__ = ["LEVELS"]
