# -*- coding: utf-8 -*-
"""箭头消除小游戏（Pygame 单文件原型）。

玩法：点击箭头的「头部」格子，若它指向的方向到棋盘边界之间没有其它箭头，
整支箭头就沿该方向滑出棋盘消失；否则算碰撞，箭头原地晃动并扣一次失误。
清空全部箭头过关，进入下一关；失误用完失败，可以重开本关。

箭头有身体：长度 1~4 格，身体沿「头的反方向」延伸（朝上的箭头，身体在
头的下方）。只有头部格子能点，身体格子点了不生效；身体同样会挡住别的箭头。
"""

import math

import pygame

# ---------------- 基础常量 ----------------
WIDTH, HEIGHT = 640, 680  # 窗口尺寸
FPS = 60

N = 5  # N×N 网格
CELL = 88  # 单格像素
GRID_W = CELL * N
GRID_X = (WIDTH - GRID_W) // 2
GRID_Y = 150  # 棋盘左上角

EMPTY, UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3, 4
DIRS = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}  # (行增量, 列增量)

MISTAKES_PER_LEVEL = 3  # 每关失误次数
MIN_LENGTH, MAX_LENGTH = 1, 4  # 箭头长度（含身体）范围

# 颜色
BG = (24, 26, 38)
CELL_BG = (46, 51, 72)
CELL_LINE = (60, 66, 94)
TEXT = (232, 236, 248)
DIM = (150, 158, 184)
RED = (231, 76, 76)
BTN = (58, 64, 90)
BTN_HOVER = (78, 86, 120)
BTN_PRIMARY = (52, 120, 210)
BTN_PRIMARY_HOVER = (74, 146, 238)
BODY_DARKEN = 0.78  # 身体颜色压暗比例，用来区分头（亮）和身体（暗）
ARROW_COLORS = {
    UP: (92, 158, 255),
    DOWN: (88, 201, 129),
    LEFT: (247, 168, 71),
    RIGHT: (186, 122, 243),
}

# 状态机
STATE_START = "start"
STATE_PLAY = "play"
STATE_WIN = "win"
STATE_LOSE = "lose"

# ---------------- 关卡数据 ----------------
# 每关是箭头定义列表，一支箭头写成一个元组：(方向, 长度, 头行, 头列)
# 头在箭头最前端，身体沿「头的反方向」延伸：
# 比如 (UP, 3, 1, 0) 表示头在 (1,0)，身体占 (2,0)、(3,0)，整支朝上。
# 三关的箭头都带身体（长度 2~4），没有单格短箭头。
# 制作方式：从空盘开始按「点击顺序的倒序」逐支摆放，每摆一支都要求此刻
# 能飞出去，因此每关天然存在一条通关顺序（下面注释里的参考解）。
LEVELS = [
    # 第 1 关（5 支，长度 2~3）
    # 参考通关顺序：(4,4)右2 → (4,2)下3 → (0,1)左3 → (2,3)上2 → (1,0)左2
    [
        (RIGHT, 2, 4, 4),  # 头 (4,4)，身体 (4,3)
        (DOWN, 3, 4, 2),  # 头 (4,2)，身体 (3,2)、(2,2)
        (LEFT, 3, 0, 1),  # 头 (0,1)，身体 (0,2)、(0,3)
        (UP, 2, 2, 3),  # 头 (2,3)，身体 (3,3)
        (LEFT, 2, 1, 0),  # 头 (1,0)，身体 (1,1)
    ],
    # 第 2 关（7 支，长度 2~4，含一支长 4）
    # 参考通关顺序：(3,4)右2 → (0,2)上4 → (2,3)下2 → (4,0)左3
    #               → (2,4)下3 → (0,0)左2 → (2,1)下2
    [
        (RIGHT, 2, 3, 4),  # 头 (3,4)，身体 (3,3)
        (UP, 4, 0, 2),  # 头 (0,2)，身体 (1,2)、(2,2)、(3,2)
        (DOWN, 2, 2, 3),  # 头 (2,3)，身体 (1,3)
        (LEFT, 3, 4, 0),  # 头 (4,0)，身体 (4,1)、(4,2)
        (DOWN, 3, 2, 4),  # 头 (2,4)，身体 (1,4)、(0,4)
        (LEFT, 2, 0, 0),  # 头 (0,0)，身体 (0,1)
        (DOWN, 2, 2, 1),  # 头 (2,1)，身体 (1,1)
    ],
    # 第 3 关（8 支，长度 2~4，含一支长 4）
    # 参考通关顺序：(4,4)右2 → (0,4)上2 → (2,4)上2 → (4,2)右2
    #               → (1,2)下2 → (0,0)左2 → (1,0)上3 → (0,3)上4
    [
        (RIGHT, 2, 4, 4),  # 头 (4,4)，身体 (4,3)
        (UP, 2, 0, 4),  # 头 (0,4)，身体 (1,4)
        (UP, 2, 2, 4),  # 头 (2,4)，身体 (3,4)
        (RIGHT, 2, 4, 2),  # 头 (4,2)，身体 (4,1)
        (DOWN, 2, 1, 2),  # 头 (1,2)，身体 (0,2)
        (LEFT, 2, 0, 0),  # 头 (0,0)，身体 (0,1)
        (UP, 3, 1, 0),  # 头 (1,0)，身体 (2,0)、(3,0)
        (UP, 4, 0, 3),  # 头 (0,3)，身体 (1,3)、(2,3)、(3,3)
    ],
]


# ---------------- 数据模型 ----------------
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


# ---------------- 小工具 ----------------
def count_arrows(arrows):
    """统计还活着的箭头支数（不是格子数）。"""
    return sum(1 for a in arrows if a.alive)


def darken(color, factor=BODY_DARKEN):
    """把颜色压暗，用来画身体（和头部区分）。"""
    return tuple(int(v * factor) for v in color)


def lerp_color(c1, c2, t):
    """颜色线性插值，t 取 0~1。"""
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def make_font(size, bold=False):
    """优先选带中文字形的字体，找不到再退回默认字体。"""
    names = "microsoftyahei,microsoftyaheiui,simhei,notosanscjksc,arialunicodems"
    try:
        return pygame.font.SysFont(names, size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)


def draw_arrow_head(surface, cx, cy, direction, color):
    """在 (cx, cy) 处画一个指向 direction 的三角箭头（头部）。"""
    s = CELL * 0.30
    pts = [(0.0, -s), (s * 0.9, s * 0.72), (-s * 0.9, s * 0.72)]  # 基础形状朝上
    if direction == UP:
        rot = lambda x, y: (x, y)  # noqa: E731
    elif direction == DOWN:
        rot = lambda x, y: (-x, -y)  # noqa: E731
    elif direction == LEFT:
        rot = lambda x, y: (y, -x)  # noqa: E731
    else:
        rot = lambda x, y: (-y, x)  # noqa: E731
    poly = [(cx + rot(x, y)[0], cy + rot(x, y)[1]) for x, y in pts]
    pygame.draw.polygon(surface, color, poly)


def draw_arrow_full(surface, head_cx, head_cy, direction, length, color, body_color):
    """画一支完整箭头：长度 ≥2 先画身体长条，再叠上头部三角形。

    几何约定（都相对头中心）：
      身体从头中心向后延伸到「尾巴格的远边缘」再多冒 0.06 格（盖住格子
      之间约 6px 的缝隙），即总长 (length-1) + 0.56 格；身体半宽 0.22 格，
      比头部三角形底座（0.27 格）略窄，这样能看出箭头尖。
    """
    if length > 1:
        dr, dc = DIRS[direction]
        ax, ay = dc, dr  # 屏幕坐标下的前进方向（x, y）
        bx, by = -ax, -ay  # 反方向（身体延伸的方向）
        tail_cx = head_cx + bx * (length - 1) * CELL
        tail_cy = head_cy + by * (length - 1) * CELL
        end_cx = tail_cx + bx * CELL * 0.56
        end_cy = tail_cy + by * CELL * 0.56
        px, py = -by, bx  # 身体宽度方向（与前进方向垂直）
        half = CELL * 0.22
        corners = [
            (head_cx + px * half, head_cy + py * half),
            (head_cx - px * half, head_cy - py * half),
            (end_cx - px * half, end_cy - py * half),
            (end_cx + px * half, end_cy + py * half),
        ]
        pygame.draw.polygon(surface, body_color, corners)
    draw_arrow_head(surface, head_cx, head_cy, direction, color)


# ---------------- 按钮 ----------------
class Button:
    """矩形按钮：带 hover 高亮和回调。"""

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
        else:
            color = BTN_HOVER if self.hovered else BTN
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        text = font.render(self.label, True, TEXT)
        surface.blit(text, text.get_rect(center=self.rect.center))


# ---------------- 动画 ----------------
class FlyAnim:
    """滑出动画：整支箭头（头+身体）一起沿方向滑出棋盘。"""

    def __init__(self, arrow, distance):
        self.arrow = arrow
        self.r, self.c = arrow.head
        self.direction = arrow.direction
        self.distance = distance  # 需要滑出的格数（含安全余量）
        self.elapsed = 0.0
        dr, dc = DIRS[arrow.direction]
        self.axis = (dc, dr)  # 像素偏移方向（x, y）
        self.duration = 0.18 + 0.04 * distance
        self.offset = (0.0, 0.0)  # 像素偏移
        self.done = False

    def update(self, dt):
        self.elapsed = min(self.elapsed + dt, self.duration)
        p = self.elapsed / self.duration
        ease = 1 - (1 - p) ** 3  # ease-out，先快后慢
        d = self.distance * ease * CELL
        self.offset = (self.axis[0] * d, self.axis[1] * d)
        if p >= 1.0:
            self.done = True

    def head_color(self):
        return ARROW_COLORS[self.direction]

    def body_color(self):
        return darken(ARROW_COLORS[self.direction])


class ShakeAnim:
    """碰撞动画：整支箭头原地晃动，颜色脉冲变红，结束后回到原样。"""

    def __init__(self, arrow):
        self.arrow = arrow
        self.r, self.c = arrow.head
        self.direction = arrow.direction
        self.duration = 0.5
        self.elapsed = 0.0
        dr, dc = DIRS[arrow.direction]
        self.axis = (dc, dr)
        self.offset = (0.0, 0.0)
        self.done = False
        self.mix = 0.0

    def update(self, dt):
        self.elapsed = min(self.elapsed + dt, self.duration)
        p = self.elapsed / self.duration
        amp = math.sin(self.elapsed * 34) * 8 * (1 - p)  # 振幅随时间衰减
        self.offset = (self.axis[0] * amp, self.axis[1] * amp)
        self.mix = math.sin(math.pi * p)  # 0 → 1 → 0 的脉冲
        if p >= 1.0:
            self.done = True

    def head_color(self):
        return lerp_color(ARROW_COLORS[self.direction], RED, self.mix)

    def body_color(self):
        return darken(self.head_color())


# ---------------- 游戏主体 ----------------
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("箭头消除")
        self.clock = pygame.time.Clock()

        self.font_title = make_font(60, bold=True)
        self.font_big = make_font(56, bold=True)
        self.font_hud = make_font(22)
        self.font_msg = make_font(22)
        self.font_btn = make_font(20)
        self.font_small = make_font(18)

        self.level_index = 0
        self.board = [[EMPTY] * N for _ in range(N)]
        self.arrows = []
        self.arrow_by_id = {}
        self.mistakes_left = MISTAKES_PER_LEVEL
        self.message = ""
        self.anims = []
        self.state = STATE_START
        self.buttons = []
        self._build_buttons()

    # ---------- 状态切换 ----------
    def _build_buttons(self):
        """按当前状态重建按钮列表。"""
        self.buttons = []
        if self.state == STATE_START:
            self.buttons.append(
                Button(
                    (WIDTH // 2 - 90, 430, 180, 52),
                    "开始游戏",
                    self.start_game,
                    primary=True,
                )
            )
        elif self.state == STATE_PLAY:
            self.buttons.append(
                Button(
                    (WIDTH - 140, 18, 116, 38),
                    "重开本关",
                    self.restart_level,
                    primary=True,
                )
            )
            self.buttons.append(
                Button((WIDTH - 226, 18, 78, 38), "返回", self.to_start)
            )
        elif self.state == STATE_WIN:
            if self.level_index + 1 < len(LEVELS):
                self.buttons.append(
                    Button(
                        (WIDTH // 2 + 8, 430, 180, 52),
                        "下一关",
                        self.next_level,
                        primary=True,
                    )
                )
            else:
                self.buttons.append(
                    Button(
                        (WIDTH // 2 + 8, 430, 180, 52),
                        "回开始",
                        self.to_start,
                        primary=True,
                    )
                )
            self.buttons.append(
                Button((WIDTH // 2 - 188, 430, 180, 52), "重开本关", self.restart_level)
            )
        elif self.state == STATE_LOSE:
            self.buttons.append(
                Button(
                    (WIDTH // 2 + 8, 430, 180, 52),
                    "重开本关",
                    self.restart_level,
                    primary=True,
                )
            )
            self.buttons.append(
                Button((WIDTH // 2 - 188, 430, 180, 52), "回开始", self.to_start)
            )

    def start_game(self):
        """从第 1 关开始新游戏。"""
        self.level_index = 0
        self.load_level()

    def to_start(self):
        self.state = STATE_START
        self.anims.clear()
        self._build_buttons()

    def next_level(self):
        if self.level_index + 1 >= len(LEVELS):
            return  # 已是最后一关，无下一关
        self.level_index += 1
        self.load_level()

    def restart_level(self):
        self.load_level()
        self.message = "已重开本关"

    def load_level(self):
        """载入当前关：按定义重建箭头、还原失误和动画。"""
        self.board, self.arrows = build_arrows(LEVELS[self.level_index])
        self.arrow_by_id = {a.id: a for a in self.arrows}
        self.mistakes_left = MISTAKES_PER_LEVEL
        self.anims.clear()
        self.state = STATE_PLAY
        self.message = f"第 {self.level_index + 1} 关：点箭头头部让它飞出去"
        self._build_buttons()

    # ---------- 核心逻辑 ----------
    def can_fly(self, r, c):
        """路径检测：找到 (r,c) 所属箭头，从它的头部沿方向逐格扫到边界。

        碰到任何箭头格子（别人的头或身体）都算阻挡，返回 False；
        一路扫到越界说明畅通，返回 True。自己身体在头的后方，不会被扫到。
        """
        value = self.board[r][c]
        if value == EMPTY:
            return False
        arrow = self.arrow_by_id[value]
        dr, dc = DIRS[arrow.direction]
        hr, hc = arrow.head
        nr, nc = hr + dr, hc + dc
        while 0 <= nr < N and 0 <= nc < N:  # 先判边界，保证不越界索引
            if self.board[nr][nc] != EMPTY:  # 有箭头挡路 → 碰撞
                return False
            nr += dr
            nc += dc
        return True  # 一路扫到出界 → 可以飞

    def fly_distance(self, arrow):
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
        else:
            span = N - 1 - hc
        if arrow.length == 1:
            tail = 0.216
        else:
            tail = (arrow.length - 1) + 0.56
        return span + 0.5 + tail + 0.04

    def pixel_to_cell(self, pos):
        """屏幕坐标 → 格子坐标，落在棋盘外返回 None。"""
        x, y = pos
        if not (GRID_X <= x < GRID_X + GRID_W and GRID_Y <= y < GRID_Y + GRID_W):
            return None
        return (y - GRID_Y) // CELL, (x - GRID_X) // CELL

    def try_click(self, r, c):
        """点击某个格子：空格提示、身体提示、头部可飞则滑出、被挡则碰撞扣失误。"""
        value = self.board[r][c]
        if value == EMPTY:
            self.message = f"({r}, {c}) 是空格子"
            return

        arrow = self.arrow_by_id[value]
        if any(a.arrow is arrow for a in self.anims):
            return  # 动画中的箭头锁住，防连点
        if (r, c) != arrow.head:
            self.message = "只能点箭头头部（身体点不动）"
            return
        if self.mistakes_left <= 0:
            return  # 失误已用完：等动画结束进失败界面

        if self.can_fly(r, c):
            self.anims.append(FlyAnim(arrow, self.fly_distance(arrow)))
            self.message = "飞出去了！"
        else:
            self.anims.append(ShakeAnim(arrow))
            self.mistakes_left -= 1
            if self.mistakes_left > 0:
                self.message = f"被箭头挡住了，失误 -1（剩 {self.mistakes_left}）"
            else:
                self.message = "失误用完了……"

    # ---------- 事件 / 更新 ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.on_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_START:
                        return False  # 开始界面按 Esc 直接退出
                    self.to_start()
                elif event.key == pygame.K_r and self.state == STATE_PLAY:
                    self.restart_level()
        return True

    def on_click(self, pos):
        for btn in self.buttons:
            if btn.hit(pos):
                btn.callback()
                return
        if self.state == STATE_PLAY:
            cell = self.pixel_to_cell(pos)
            if cell is not None:
                self.try_click(*cell)

    def update(self, dt):
        # 推进动画
        for anim in self.anims:
            anim.update(dt)
        finished = [a for a in self.anims if a.done]
        for anim in finished:
            self.anims.remove(anim)
            if isinstance(anim, FlyAnim):  # 飞完了才把整支箭头从棋盘移除
                arrow = anim.arrow
                for r, c in arrow.cells:
                    self.board[r][c] = EMPTY
                arrow.alive = False

        # 动画全部结束、且还在游戏中时，判定胜负
        if self.state == STATE_PLAY and not self.anims:
            if count_arrows(self.arrows) == 0:
                self.state = STATE_WIN
                self._build_buttons()
            elif self.mistakes_left <= 0:
                self.state = STATE_LOSE
                self._build_buttons()

    # ---------- 绘制 ----------
    def draw(self):
        self.screen.fill(BG)
        mouse_pos = pygame.mouse.get_pos()
        if self.state == STATE_START:
            self.draw_start(mouse_pos)
        elif self.state == STATE_PLAY:
            self.draw_play(mouse_pos)
        elif self.state == STATE_WIN:
            self.draw_result(
                mouse_pos,
                (
                    "全部通关！"
                    if self.level_index + 1 >= len(LEVELS)
                    else f"第 {self.level_index + 1} 关通关！"
                ),
                (
                    "点击「下一关」继续挑战"
                    if self.level_index + 1 < len(LEVELS)
                    else "你已经清空了所有关卡"
                ),
            )
        else:
            self.draw_result(
                mouse_pos,
                "游戏失败",
                f"第 {self.level_index + 1} 关失误用完了，重来一次吧",
            )

    def draw_start(self, mouse_pos):
        title = self.font_title.render("箭头消除", True, TEXT)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 170)))
        rules = [
            "点击箭头头部：它指向的方向到边界之间没有其它箭头，就会飞出去",
            "被挡住则算碰撞：箭头不动，失误 -1",
            "箭头有身体（1~4 格），只有头部能点，身体同样会挡路",
            "清空全部箭头过关，失误用完失败",
        ]
        for i, line in enumerate(rules):
            text = self.font_msg.render(line, True, DIM)
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 268 + i * 38)))
        for btn in self.buttons:
            btn.draw(self.screen, self.font_btn, mouse_pos)

    def draw_play(self, mouse_pos):
        # HUD：关卡 / 剩余箭头 / 剩余失误
        hud = self.font_hud.render(
            f"第 {self.level_index + 1} / {len(LEVELS)} 关", True, TEXT
        )
        self.screen.blit(hud, hud.get_rect(midleft=(24, 37)))
        arrows = self.font_hud.render(
            f"剩余箭头 {count_arrows(self.arrows)}", True, TEXT
        )
        self.screen.blit(arrows, arrows.get_rect(midleft=(170, 37)))
        color = RED if self.mistakes_left <= 1 else TEXT
        mistakes = self.font_hud.render(f"剩余失误 {self.mistakes_left}", True, color)
        self.screen.blit(mistakes, mistakes.get_rect(midleft=(300, 37)))

        for btn in self.buttons:
            btn.draw(self.screen, self.font_btn, mouse_pos)

        # 提示信息
        msg = self.font_msg.render(self.message, True, DIM)
        self.screen.blit(msg, msg.get_rect(center=(WIDTH // 2, 112)))

        # 棋盘
        for r in range(N):
            for c in range(N):
                rect = pygame.Rect(GRID_X + c * CELL, GRID_Y + r * CELL, CELL, CELL)
                pygame.draw.rect(
                    self.screen, CELL_BG, rect.inflate(-6, -6), border_radius=10
                )
                pygame.draw.rect(
                    self.screen, CELL_LINE, rect.inflate(-6, -6), 2, border_radius=10
                )

        # 静态箭头（整支一起画）
        animated_ids = {a.arrow.id for a in self.anims}
        for arrow in self.arrows:
            if not arrow.alive or arrow.id in animated_ids:
                continue
            cx = GRID_X + arrow.head[1] * CELL + CELL // 2
            cy = GRID_Y + arrow.head[0] * CELL + CELL // 2
            color = ARROW_COLORS[arrow.direction]
            draw_arrow_full(
                self.screen, cx, cy, arrow.direction, arrow.length, color, darken(color)
            )

        # 动画中的箭头（飞出时裁到棋盘范围内，看起来像滑出棋盘）
        for anim in self.anims:
            cx = GRID_X + anim.c * CELL + CELL // 2 + anim.offset[0]
            cy = GRID_Y + anim.r * CELL + CELL // 2 + anim.offset[1]
            if isinstance(anim, FlyAnim):
                self.screen.set_clip(pygame.Rect(GRID_X, GRID_Y, GRID_W, GRID_W))
            draw_arrow_full(
                self.screen,
                cx,
                cy,
                anim.direction,
                anim.arrow.length,
                anim.head_color(),
                anim.body_color(),
            )
            self.screen.set_clip(None)

        hint = self.font_small.render("R 重开本关    Esc 返回开始", True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 622)))

    def draw_result(self, mouse_pos, title_text, sub_text):
        title = self.font_big.render(title_text, True, TEXT)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 250)))
        sub = self.font_msg.render(sub_text, True, DIM)
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 330)))
        for btn in self.buttons:
            btn.draw(self.screen, self.font_btn, mouse_pos)

    # ---------- 主循环 ----------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()


def main():
    pygame.init()
    try:
        Game().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
