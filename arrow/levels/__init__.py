# -*- coding: utf-8 -*-
"""关卡数据包。

每关是箭头定义列表，一支箭头写成一个元组：(方向, 行, 列)。
箭头都是单格，方向分上、下、左、右四种；点击后沿它的方向检查
同一行或同一列、箭头与边界之间是否还有其它箭头。

制作方式：从空盘开始按「点击顺序的倒序」逐支摆放（每摆一支，要求它
此刻的前方没有其它箭头）。这样构造出的盘面恒可通过：摆放第 k 支时
只校验了前 k-1 支的阻挡，所以任何时刻「最后摆放的那支存活箭头」必然
可以飞出去——按编号从大到小贪心点击即可清空整关，不会出现死局。
（注意：不能简单说「移走箭头只会让路径更空旷」——两支互指的箭头
可以互相挡死；上面的「最大编号恒可飞」才是可通关性的真正来源。）
"""

from arrow.levels.level1 import LEVEL as LEVEL_1
from arrow.levels.level2 import LEVEL as LEVEL_2
from arrow.levels.level3 import LEVEL as LEVEL_3
from arrow.levels.level4 import LEVEL as LEVEL_4
from arrow.levels.level5 import LEVEL as LEVEL_5
from arrow.levels.level6 import LEVEL as LEVEL_6

LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5, LEVEL_6]

__all__ = ["LEVELS"]
