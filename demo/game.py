#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal FPV - 基于 tv.py 的终端第一人称视角游戏
====================================================
控制:
    W / ↑     - 前进
    S / ↓     - 后退
    A         - 左平移
    D         - 右平移
    ← / →     - 转向
    Q         - 退出
"""

import math
import sys
import time
import os

# =====================================================================
# 1. TV.PY 集成层
# =====================================================================
HAS_TV = False

try:
    sys.path.append("./../")
    from tv import *
    HAS_TV = True
except:
    HAS_TV = False

if not HAS_TV:
    # 内联 tv.py v0.0.2 最小兼容实现（当 tv.py 缺失时自动降级）
    _char = "▄"
    def transform(ur, ug, ub, lr, lg, lb, char=_char):
        return "\033[38;2;{0};{1};{2};48;2;{3};{4};{5}m{6}".format(lr, lg, lb, ur, ug, ub, char)
    def parse(lst, char=_char):
        code = ''
        for i in lst:
            for l in i:
                code += transform(*l, char)
            code += "\033[0m\n"
        return code.removesuffix("\n")
    def myprint(text):
        sys.stdout.write(text)
        sys.stdout.flush()

# =====================================================================
# 2. 输入处理层
# =====================================================================
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

def get_key():
    """非阻塞读取单个按键（支持方向键）"""
    if HAS_MSVCRT:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b'\x00', b'\xe0'):
                key2 = msvcrt.getch()
                arrow_map = {b'H': 'UP', b'P': 'DOWN', b'K': 'LEFT', b'M': 'RIGHT'}
                return arrow_map.get(key2, key2.decode('latin-1', errors='ignore'))
            return key.decode('latin-1', errors='ignore') if isinstance(key, bytes) else key
    else:
        import select
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
    return None

# =====================================================================
# 3. 游戏引擎核心
# =====================================================================

# 终端尺寸自适应
try:
    ts = os.get_terminal_size()
    SCREEN_WIDTH = min(120, ts.columns - 2)
    SCREEN_HEIGHT = min(60, (ts.lines - 4) * 2)
except Exception:
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 40

# 确保高度为偶数（2像素合1字符）
if SCREEN_HEIGHT % 2:
    SCREEN_HEIGHT -= 1

# 视野与速度
FOV = math.pi / 3.0
FOV_HALF = FOV / 2.0
ANGLE_STEP = FOV / SCREEN_WIDTH
MOVE_SPEED = 0.055
ROT_SPEED = 0.045

# 世界地图 (1=砖墙, 2=冰墙, 3=紫墙, 0=空地)
WORLD_MAP = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,2,2,0,0,1,1,1,0,0,0,0,0,0,1,1,1,0,0,2,2,0,1],
    [1,0,2,0,0,0,1,0,0,0,0,3,3,0,0,0,0,1,0,0,0,2,0,1],
    [1,0,0,0,0,0,1,0,1,1,1,0,0,1,1,1,0,1,0,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,0,1,1,0,3,3,0,0,3,3,0,1,1,0,1,0,1,0,1],
    [1,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,1,0,1,0,1,0,0,2,2,0,0,1,0,1,0,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,0,1,0,1,0,0,2,2,0,0,1,0,1,0,1,1,1,0,1],
    [1,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,0,1,0,1,1,0,3,3,0,0,3,3,0,1,1,0,1,0,1,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1],
    [1,0,0,0,0,0,1,0,1,1,1,0,0,1,1,1,0,1,0,0,0,0,0,1],
    [1,0,2,0,0,0,1,0,0,0,0,3,3,0,0,0,0,1,0,0,0,2,0,1],
    [1,0,2,2,0,0,1,1,1,0,0,0,0,0,0,1,1,1,0,0,2,2,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]
MAP_H = len(WORLD_MAP)
MAP_W = len(WORLD_MAP[0])

# 材质颜色表
WALL_COLORS = {
    1: (200, 140, 80),    # 砖墙 - 暖橙棕
    2: (70, 130, 180),    # 冰墙 - 冷钢蓝
    3: (140, 70, 140),    # 紫墙 - 神秘紫
}

# 环境渐变色
CEILING_TOP = (18, 22, 35)
CEILING_BOT = (40, 45, 65)
FLOOR_TOP   = (55, 50, 40)
FLOOR_BOT   = (28, 25, 20)

# 玩家初始状态
px, py = 1.5, 1.5
p_angle = math.pi / 4.0

# =====================================================================
# 4. 射线投射渲染器
# =====================================================================

def cast_ray(angle):
    """DDA 射线投射，返回 (垂直距离, 墙壁类型, 侧面)"""
    sin_a = math.sin(angle)
    cos_a = math.cos(angle)

    # 防除零
    if abs(cos_a) < 1e-6:
        cos_a = 1e-6 if cos_a >= 0 else -1e-6
    if abs(sin_a) < 1e-6:
        sin_a = 1e-6 if sin_a >= 0 else -1e-6

    map_x, map_y = int(px), int(py)
    delta_x = abs(1.0 / cos_a)
    delta_y = abs(1.0 / sin_a)

    if cos_a < 0:
        step_x = -1
        side_x = (px - map_x) * delta_x
    else:
        step_x = 1
        side_x = (map_x + 1.0 - px) * delta_x

    if sin_a < 0:
        step_y = -1
        side_y = (py - map_y) * delta_y
    else:
        step_y = 1
        side_y = (map_y + 1.0 - py) * delta_y

    hit = 0
    side = 0
    for _ in range(64):
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            side = 0
        else:
            side_y += delta_y
            map_y += step_y
            side = 1

        if not (0 <= map_x < MAP_W and 0 <= map_y < MAP_H):
            return (1e30, 0, 0)

        hit = WORLD_MAP[map_y][map_x]
        if hit:
            break

    if not hit:
        return (1e30, 0, 0)

    # 垂直距离（消除鱼眼）
    if side == 0:
        perp = (map_x - px + (1 - step_x) / 2.0) / cos_a
    else:
        perp = (map_y - py + (1 - step_y) / 2.0) / sin_a

    return (perp, hit, side)


def shade_color(base, dist, side):
    """根据距离和侧面计算最终颜色（雾化+阴影）"""
    # 侧面变暗
    if side == 1:
        base = (int(base[0] * 0.62), int(base[1] * 0.62), int(base[2] * 0.62))
    # 距离雾化
    fog = min(1.0, dist / 14.0)
    return (
        max(0, min(255, int(base[0] * (1.0 - fog) + 12 * fog))),
        max(0, min(255, int(base[1] * (1.0 - fog) + 12 * fog))),
        max(0, min(255, int(base[2] * (1.0 - fog) + 12 * fog))),
    )


def get_pixel(pixel_y, wall_h, dist, wtype, side):
    """确定单个像素的颜色"""
    half = SCREEN_HEIGHT // 2
    top = half - wall_h // 2
    bot = top + wall_h

    if pixel_y < top:
        # 天花板渐变
        t = pixel_y / top if top > 0 else 0.0
        return (
            int(CEILING_TOP[0] + (CEILING_BOT[0] - CEILING_TOP[0]) * t),
            int(CEILING_TOP[1] + (CEILING_BOT[1] - CEILING_TOP[1]) * t),
            int(CEILING_TOP[2] + (CEILING_BOT[2] - CEILING_TOP[2]) * t),
        )
    elif pixel_y < bot:
        # 墙壁
        base = WALL_COLORS.get(wtype, (150, 150, 150))
        return shade_color(base, dist, side)
    else:
        # 地板渐变
        t = (pixel_y - bot) / (SCREEN_HEIGHT - bot) if SCREEN_HEIGHT > bot else 0.0
        return (
            int(FLOOR_TOP[0] + (FLOOR_BOT[0] - FLOOR_TOP[0]) * t),
            int(FLOOR_TOP[1] + (FLOOR_BOT[1] - FLOOR_TOP[1]) * t),
            int(FLOOR_TOP[2] + (FLOOR_BOT[2] - FLOOR_TOP[2]) * t),
        )


def render_frame():
    """渲染一帧，返回 tv.py 标准格式: tuple[tuple[tuple[int*6]]]"""
    # 预计算每列射线
    rays = []
    for x in range(SCREEN_WIDTH):
        ang = p_angle - FOV_HALF + x * ANGLE_STEP
        dist, wtype, side = cast_ray(ang)
        if dist > 0.001:
            wh = int(SCREEN_HEIGHT / (dist * 0.72))
        else:
            wh = SCREEN_HEIGHT
        wh = max(1, min(wh, SCREEN_HEIGHT))
        rays.append((dist, wtype, side, wh))

    # 组装像素帧（每终端行 = 2 像素行）
    frame = []
    for row in range(SCREEN_HEIGHT // 2):
        y1 = row * 2
        y2 = y1 + 1
        line = []
        for x in range(SCREEN_WIDTH):
            dist, wtype, side, wh = rays[x]
            c1 = get_pixel(y1, wh, dist, wtype, side)
            c2 = get_pixel(y2, wh, dist, wtype, side)
            line.append((c1[0], c1[1], c1[2], c2[0], c2[1], c2[2]))
        frame.append(tuple(line))

    return tuple(frame)


# =====================================================================
# 5. HUD & 小地图
# =====================================================================

def draw_minimap():
    """生成小地图文本行"""
    mw, mh = 10, 8
    sy = max(0, int(py) - mh // 2)
    sx = max(0, int(px) - mw // 2)
    lines = []
    for y in range(sy, min(MAP_H, sy + mh)):
        ln = ""
        for x in range(sx, min(MAP_W, sx + mw)):
            if int(px) == x and int(py) == y:
                ln += "\033[93mP\033[0m"  # 黄色玩家
            elif WORLD_MAP[y][x] == 1:
                ln += "\033[91m#\033[0m"  # 红色砖墙
            elif WORLD_MAP[y][x] == 2:
                ln += "\033[94m#\033[0m"  # 蓝色冰墙
            elif WORLD_MAP[y][x] == 3:
                ln += "\033[95m#\033[0m"  # 紫色墙
            else:
                ln += "."
        lines.append(ln)
    return lines


# =====================================================================
# 6. 主循环
# =====================================================================

def main():
    global px, py, p_angle

    # 进入备用屏幕，隐藏光标
    myprint('\033[?1049h\033[?25l')

    try:
        last_time = time.time()
        frames = 0
        fps = 0.0

        while True:
            t0 = time.time()

            # ---- 渲染 ----
            frame_data = render_frame()
            frame_str = parse(frame_data) + '\033[0m'

            # ---- 绘制 ----
            myprint('\033[H' + frame_str)

            # ---- HUD ----
            hud_base = SCREEN_HEIGHT // 2 + 1
            hud_lines = [
                ("=" * SCREEN_WIDTH)[:SCREEN_WIDTH],
                (f"[TERMINAL FPV]  坐标: ({px:.2f}, {py:.2f})  朝向: {math.degrees(p_angle) % 360:.0f}°  FPS: {fps:.0f}")[:SCREEN_WIDTH].ljust(SCREEN_WIDTH),
                ("控制: W/S=前后  A/D=平移  ←/→=转向  Q=退出")[:SCREEN_WIDTH].ljust(SCREEN_WIDTH),
            ]
            for i, hl in enumerate(hud_lines):
                myprint(f"\033[0m\033[{hud_base + i};1H{hl}")

            # ---- 小地图 ----
            minimap = draw_minimap()
            for i, ml in enumerate(minimap):
                myprint(f"\033[{hud_base + 1 + i};{SCREEN_WIDTH - 14}H{ml.ljust(14)}")

            # ---- FPS 统计 ----
            frames += 1
            now = time.time()
            if now - last_time >= 1.0:
                fps = frames / (now - last_time)
                frames = 0
                last_time = now

            # ---- 输入处理 ----
            key = get_key()
            if key:
                k = key.upper()

                if k == 'Q':
                    break
                elif k == 'W' or k == 'UP':
                    nx = px + math.cos(p_angle) * MOVE_SPEED
                    ny = py + math.sin(p_angle) * MOVE_SPEED
                    if WORLD_MAP[int(ny)][int(nx)] == 0:
                        px, py = nx, ny
                elif k == 'S' or k == 'DOWN':
                    nx = px - math.cos(p_angle) * MOVE_SPEED
                    ny = py - math.sin(p_angle) * MOVE_SPEED
                    if WORLD_MAP[int(ny)][int(nx)] == 0:
                        px, py = nx, ny
                elif k == 'A':
                    nx = px + math.cos(p_angle - math.pi / 2) * MOVE_SPEED
                    ny = py + math.sin(p_angle - math.pi / 2) * MOVE_SPEED
                    if WORLD_MAP[int(ny)][int(nx)] == 0:
                        px, py = nx, ny
                elif k == 'D':
                    nx = px + math.cos(p_angle + math.pi / 2) * MOVE_SPEED
                    ny = py + math.sin(p_angle + math.pi / 2) * MOVE_SPEED
                    if WORLD_MAP[int(ny)][int(nx)] == 0:
                        px, py = nx, ny
                elif k == 'LEFT' or k == 'K':
                    p_angle -= ROT_SPEED
                elif k == 'RIGHT' or k == 'M':
                    p_angle += ROT_SPEED

            # 帧率限制 (~60 FPS)
            elapsed = time.time() - t0
            if elapsed < 0.016:
                time.sleep(0.016 - elapsed)

    except KeyboardInterrupt:
        pass
    finally:
        # 恢复主屏幕，显示光标
        myprint('\033[?1049l\033[?25h')
        print("\n感谢游玩 Terminal FPV!")


if __name__ == "__main__":
    main()
