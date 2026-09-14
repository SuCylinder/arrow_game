# -*- coding: utf-8 -*-
"""箭头消除小游戏入口。

玩法：点击棋盘上的箭头，若它指向的方向到棋盘边界之间没有其它箭头，
它就从那个方向飞出棋盘消失；否则算碰撞，箭头原地晃动变红并扣一次失误。
清空全部箭头过关，进入下一关；失误用完失败，可以重开本关。

箭头分上、下、左、右四种方向，各占一个格子；路径检测只看同一行或
同一列、箭头与边界之间是否还有其它箭头。
"""

import pygame

from arrow.game import Game


def main():
    pygame.init()
    try:
        Game().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
