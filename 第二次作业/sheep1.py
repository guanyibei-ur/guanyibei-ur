import pgzrun
import pygame
import random
from pgzero.actor import Actor
from pgzero.builtins import Rect
import numpy as np

pygame.mixer.init()

# 定义游戏相关属性
TITLE = '羊了羊'
WIDTH = 600
HEIGHT = 720

# 自定义游戏常量
T_WIDTH = 60
T_HEIGHT = 66

# 下方牌堆的位置
DOCK = Rect((85, 580), (T_WIDTH * 7, T_HEIGHT))

# 初始化全局变量
tiles = []
docks = []
history = []  # 用于存储操作历史 (牌, 原始位置, 原始层)
layout_type = "normal"  # 布局类型，默认为 normal
countdown = 10800    # 默认倒计时时间
should_countdown = True

# 撤回按钮
undo_button = Rect((DOCK.right + 10, DOCK.y), (100, 50))  # 撤回按钮的位置和大小

def show_difficulty_window():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("选择难度")

    font = pygame.font.SysFont("SimHei", 32)

    easy_button = pygame.Rect(100, 50, 200, 50)
    normal_button = pygame.Rect(100, 130, 200, 50)
    hard_button = pygame.Rect(100, 210, 200, 50)

    while True:
        screen.fill((30, 30, 30))  # 背景颜色

        pygame.draw.rect(screen, (100, 200, 100), easy_button)
        pygame.draw.rect(screen, (100, 100, 200), normal_button)
        pygame.draw.rect(screen, (200, 100, 100), hard_button)

        easy_text = font.render("简单", True, (255, 255, 255))
        normal_text = font.render("一般", True, (255, 255, 255))
        hard_text = font.render("困难", True, (255, 255, 255))
        screen.blit(easy_text, (150, 60))
        screen.blit(normal_text, (150, 140))
        screen.blit(hard_text, (150, 220))

        pygame.display.flip()  # 更新屏幕

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_button.collidepoint(event.pos):
                    return "diamond"
                elif normal_button.collidepoint(event.pos):
                    return "circle"
                elif hard_button.collidepoint(event.pos):
                    return "normal"

def set_layout(difficulty):
    global layout_type
    layout_type = difficulty

def init_game():
    global tiles, docks, countdown, should_countdown, history
    ts = list(range(1, 13)) * 12
    random.shuffle(ts)
    n = 0
    tiles = []
    docks = []
    history = []

    if layout_type == "normal":
        # 原始布局
        for k in range(7):
            for i in range(7 - k):
                for j in range(7 - k):
                    t = ts[n]
                    n += 1
                    tile = Actor(f'tile{t}')
                    tile.pos = 120 + (k * 0.5 + j) * tile.width, 100 + (k * 0.5 + i) * tile.height * 0.9
                    tile.tag = t
                    tile.layer = k
                    tile.status = 1 if k == 6 else 0
                    tiles.append(tile)
    elif layout_type == "diamond":
        # 菱形布局
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        layers = 7  # 层数
        for layer in range(layers):
            for i in range(layer * 2 + 1):
                t = ts[n]
                n += 1
                tile = Actor(f'tile{t}')
                tile.pos = center_x + (i - layer) * tile.width, center_y + (layer - layers // 2) * tile.height * 0.9
                tile.tag = t
                tile.layer = layer
                tile.status = 1 if layer == layers - 1 else 0
                tiles.append(tile)
    elif layout_type == "circle":
        # 圆形布局
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        radius = 200  # 圆的半径
        layers = 6  # 层数
        for layer in range(layers):
            count = (layer + 1) * 6  # 每层的数量
            for i in range(count):
                t = ts[n]
                n += 1
                angle = 2 * np.pi * i / count
                x = center_x + np.cos(angle) * radius * (layer / layers)
                y = center_y + np.sin(angle) * radius * (layer / layers)
                tile = Actor(f'tile{t}')
                tile.pos = x, y
                tile.tag = t
                tile.layer = layer
                tile.status = 1 if layer == layers - 1 else 0
                tiles.append(tile)

    # 下方 4 个牌
    for i in range(4):
        t = ts[n]
        n += 1
        tile = Actor(f'tile{t}')
        tile.pos = 210 + i * tile.width, 516
        tile.tag = t
        tile.layer = 0
        tile.status = 1
        tiles.append(tile)
    should_countdown = True

def draw():
    screen.clear()
    screen.blit('back', (0, 0))
    for tile in tiles:
        tile.draw()
        if tile.status == 0:
            screen.blit('mask', tile.topleft)
    for i, tile in enumerate(docks):
        tile.left = (DOCK.x + i * T_WIDTH)
        tile.top = DOCK.y
        tile.draw()

    screen.draw.filled_rect(undo_button, (180, 180, 180))
    screen.draw.text("撤回", center=(undo_button.center), fontsize=30, color=(0, 0, 0))

    if (countdown <= 0 and len(tiles) > 0) or len(docks) >= 7:
        screen.blit('end', (0, 0))
        stop_countdown()
    if len(tiles) == 0:
        screen.blit('win', (0, 0))

    minutes = countdown // 60
    seconds = countdown % 60
    screen.draw.text(f"Time Left: {minutes:02d}:{seconds:02d}", (10, HEIGHT - 30), color=(255, 255, 255))

def undo_last_move():
    global docks, tiles, history
    if history:
        last_tile, original_pos, original_layer = history.pop()
        docks.remove(last_tile)
        last_tile.pos = original_pos
        last_tile.layer = original_layer
        last_tile.status = 1
        tiles.append(last_tile)

def on_mouse_down(pos):
    global docks, countdown, should_countdown, history
    if undo_button.collidepoint(pos):
        undo_last_move()
        return
    if len(docks) >= 7 or len(tiles) == 0 or countdown <= 0 or not should_countdown:
        return
    for tile in reversed(tiles):
        if tile.status == 1 and tile.collidepoint(pos):
            history.append((tile, tile.pos, tile.layer))
            tile.status = 2
            tiles.remove(tile)
            diff = [t for t in docks if t.tag != tile.tag]
            if len(docks) - len(diff) < 2:
                docks.append(tile)
            else:
                docks = diff
            for down in tiles:
                if down.layer == tile.layer - 1 and down.colliderect(tile):
                    for up in tiles:
                        if up.layer == down.layer + 1 and up.colliderect(down):
                            break
                    else:
                        down.status = 1
            return

def update():
    global countdown
    if should_countdown:
        countdown -= 1

def stop_countdown():
    global should_countdown
    should_countdown = False

difficulty = show_difficulty_window()
set_layout(difficulty)
init_game()
music.play('bgm')
pgzrun.go()
