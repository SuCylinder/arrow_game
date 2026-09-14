# -*- coding: utf-8 -*-
"""箭头消除小游戏入口。

玩法：点击箭头的「头部」格子，若它指向的方向到棋盘边界之间没有其它箭头，
整支箭头就沿该方向滑出棋盘消失；否则算碰撞，箭头原地晃动并扣一次失误。
清空全部箭头过关，进入下一关；失误用完失败，可以重开本关。

箭头有身体：长度 1~4 格，身体沿「头的反方向」延伸（朝上的箭头，身体在
头的下方）。只有头部格子能点，身体格子点了不生效；身体同样会挡住别的箭头。
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
