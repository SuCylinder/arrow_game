# -*- coding: utf-8 -*-
"""按钮控件。"""

import pygame

from arrow.config import (
    BTN,
    BTN_HOVER,
    BTN_LINE,
    BTN_PRIMARY,
    BTN_PRIMARY_HOVER,
    BTN_PRIMARY_LINE,
    SHADOW,
    TEXT,
)


class Button:
    """矩形按钮：圆角 + 底部投影 + 1px 描边，带 hover 高亮和回调。"""

    def __init__(self, rect, label, callback, primary=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.primary = primary
        self.hovered = False

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface, font, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.primary:
            color = BTN_PRIMARY_HOVER if self.hovered else BTN_PRIMARY
            line = BTN_PRIMARY_LINE
        else:
            color = BTN_HOVER if self.hovered else BTN
            line = BTN_LINE
        # 底部投影（不改变按钮本身的命中区域与位置）
        shadow = self.rect.move(0, 3)
        pygame.draw.rect(surface, SHADOW, shadow, border_radius=10)
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, line, self.rect, 1, border_radius=10)
        text = font.render(self.label, True, TEXT)
        surface.blit(text, text.get_rect(center=self.rect.center))
