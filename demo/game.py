import sys
import os
import math
import time
import random
import shutil

sys.path.append("./../")
import tv

# --------------------- 参数设置 ---------------------
MAX_ANGLE = math.radians(45)
PITCH_RATE = 55
ROLL_RATE = 110
ACCEL = 22.0
SPEED_MIN = 10.0
SPEED_MAX = 50.0
BLOCK = 100.0                  # 街区尺寸
ROAD_W = 24.0                  # 道路宽度
GREENBELT_W = 6.0              # 绿化带宽度（沿道路两侧）
CLOUD_Z = 380.0
FOV_V = 75

BUILDING_COLORS = [
    (160, 160, 170),   # 浅灰
    (180, 150, 130),   # 米黄
    (130, 140, 160),   # 蓝灰
    (140, 160, 150),   # 灰绿
    (170, 160, 140),   # 浅棕
    (150, 155, 165),   # 中灰
    (120, 120, 135),   # 深灰
    (190, 180, 160),   # 浅黄
]

WINDOW_DARK = (35, 40, 50)
WINDOW_LIGHT = (180, 200, 210)

# 窗户世界空间参数（米）
WINDOW_SPACING_H = 3.0      # 水平周期
WINDOW_WIDTH_H = 1.2        # 窗户水平宽度
WINDOW_SPACING_V = 3.5      # 垂直周期
WINDOW_HEIGHT_V = 1.8       # 窗户垂直高度
WALL_MARGIN = 0.4           # 建筑边缘留白（米）


# --------------------- 工具函数 ---------------------
def clamp(x, a, b):
    if x < a:
        return a
    if x > b:
        return b
    return x


def mix_color(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def darken(color, factor=0.7):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


# --------------------- 世界生成 ---------------------
def get_objects(cx, cy, radius=500):
    """生成楼房和树木，建筑类型多样。"""
    objs = []
    i0 = int(math.floor((cx - radius) / BLOCK))
    i1 = int(math.floor((cx + radius) / BLOCK))
    j0 = int(math.floor((cy - radius) / BLOCK))
    j1 = int(math.floor((cy + radius) / BLOCK))

    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            seed = (i * 73856093) ^ (j * 19349663)
            rnd = random.Random(seed)

            # 随机建筑类型
            btype = rnd.random()
            if btype < 0.25:
                # 摩天楼
                bh = rnd.uniform(80, 120)
                bw = rnd.uniform(15, 25)
            elif btype < 0.55:
                # 写字楼
                bh = rnd.uniform(50, 80)
                bw = rnd.uniform(12, 20)
            elif btype < 0.85:
                # 住宅楼
                bh = rnd.uniform(30, 50)
                bw = rnd.uniform(10, 15)
            else:
                # 矮楼
                bh = rnd.uniform(15, 30)
                bw = rnd.uniform(8, 12)

            bx = (i + 0.5) * BLOCK + rnd.uniform(-BLOCK * 0.28, BLOCK * 0.28)
            by = (j + 0.5) * BLOCK + rnd.uniform(-BLOCK * 0.28, BLOCK * 0.28)
            color = BUILDING_COLORS[rnd.randint(0, len(BUILDING_COLORS) - 1)]
            objs.append({
                'type': 'building',
                'x': bx,
                'y': by,
                'w': bw,
                'h': bh,
                'color': color,
            })

            # 两棵树，沿道路附近
            for _ in range(2):
                tx = (i + 0.5) * BLOCK + rnd.uniform(-BLOCK * 0.35, BLOCK * 0.35)
                ty = (j + 0.5) * BLOCK + rnd.uniform(-BLOCK * 0.35, BLOCK * 0.35)
                th = rnd.uniform(6, 10)
                objs.append({
                    'type': 'tree',
                    'x': tx,
                    'y': ty,
                    'w': 5.0,
                    'h': th,
                    'color': (90, 140, 70),
                })
    return objs


def get_clouds(cx, cy, radius=1600):
    clouds = []
    cell = 550.0
    i0 = int(math.floor((cx - radius) / cell))
    i1 = int(math.floor((cx + radius) / cell))
    j0 = int(math.floor((cy - radius) / cell))
    j1 = int(math.floor((cy + radius) / cell))

    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            seed = (i * 90001) ^ (j * 1000003)
            rnd = random.Random(seed)
            wx = i * cell + rnd.uniform(0, cell)
            wy = j * cell + rnd.uniform(0, cell)
            wr = rnd.uniform(100, 200)
            clouds.append((wx, wy, wr))
    return clouds


# --------------------- 渲染 ---------------------
def render_frame(state, W, H, halfW, halfH, f, inv_f):
    px = state['x']
    py = state['y']
    pz = state['z']
    yaw = state['yaw']
    pitch = state['pitch']
    roll = state['roll']

    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cy = math.cos(yaw)
    sy = math.sin(yaw)

    Fx = sy * cp
    Fy = cy * cp
    Fz = sp
    R0x = cy
    R0y = -sy
    R0z = 0.0
    U0x = -sy * sp
    U0y = -cy * sp
    U0z = cp

    horizon_v = halfH + math.tan(pitch) * f

    img = [[(135, 180, 230)] * W for _ in range(H)]

    # ---------- 背景：天空/地面 ----------
    for v in range(H):
        ny = (halfH - v) * inv_f
        dz_row = ny * U0z + Fz
        row = img[v]

        if v < horizon_v:
            sky_mix = clamp(dz_row * 1.2, 0.0, 1.0)
            horizon_color = (185, 215, 240)
            zenith_color = (60, 110, 210)
            sky_r, sky_g, sky_b = mix_color(horizon_color, zenith_color, sky_mix)
            for u in range(W):
                row[u] = (sky_r, sky_g, sky_b)
        else:
            base_x = ny * U0x + Fx
            base_y = ny * U0y + Fy
            for u in range(W):
                nx = (u - halfW) * inv_f
                dx = nx * R0x + base_x
                dy = nx * R0y + base_y
                dz = dz_row

                if abs(dz) < 1e-9:
                    r, g, b = mix_color((150, 150, 150), (185, 215, 240), 0.75)
                    row[u] = (r, g, b)
                    continue

                t = -pz / dz
                wx = px + dx * t
                wy = py + dy * t

                rx = wx % BLOCK
                ry = wy % BLOCK
                if rx < 0:
                    rx += BLOCK
                if ry < 0:
                    ry += BLOCK
                dxr = min(rx, BLOCK - rx)
                dyr = min(ry, BLOCK - ry)

                if dxr < ROAD_W * 0.5 or dyr < ROAD_W * 0.5:
                    br, bg, bb = 88, 88, 94
                elif dxr < ROAD_W * 0.5 + GREENBELT_W or dyr < ROAD_W * 0.5 + GREENBELT_W:
                    br, bg, bb = 90, 130, 80
                else:
                    br, bg, bb = 150, 150, 150

                fog = clamp(t / 550.0, 0.0, 1.0)
                r, g, b = mix_color((br, bg, bb), (185, 215, 240), fog * 0.75)
                row[u] = (r, g, b)

    # ---------- 云朵 ----------
    clouds = get_clouds(px, py)
    for wx, wy, wr in clouds:
        vx = wx - px
        vy = wy - py
        vz = CLOUD_Z - pz
        cam_x = vx * R0x + vy * R0y
        cam_y = vx * U0x + vy * U0y + vz * U0z
        cam_z = vx * Fx + vy * Fy + vz * Fz
        if cam_z < 20:
            continue

        inv_z = 1.0 / cam_z
        u0 = halfW + cam_x * inv_z * f
        v0 = halfH - cam_y * inv_z * f
        rx = wr * inv_z * f
        ry = rx * 0.45

        left = int(u0 - rx)
        right = int(u0 + rx)
        top = int(v0 - ry)
        bottom = int(v0 + ry)

        if right < 0 or left >= W or bottom < 0 or top >= H:
            continue

        for cy in range(max(top, 0), min(bottom, H - 1) + 1):
            if cy >= horizon_v:
                continue
            dy_n = (cy - v0) / ry if ry > 1 else 0.0
            row = img[cy]
            for cx in range(max(left, 0), min(right, W - 1) + 1):
                dx_n = (cx - u0) / rx if rx > 1 else 0.0
                d2 = dx_n * dx_n + dy_n * dy_n
                if d2 <= 1.0:
                    alpha = 0.30 + 0.30 * (1.0 - d2)
                    old = row[cx]
                    cloud_color = (225, 228, 235)
                    r, g, b = mix_color(old, cloud_color, alpha)
                    row[cx] = (r, g, b)

    # ---------- 楼房/树木 ----------
    objects = get_objects(px, py)
    draw_list = []
    for obj in objects:
        vx = obj['x'] - px
        vy = obj['y'] - py
        vz = -pz
        cam_z = vx * Fx + vy * Fy + vz * Fz
        if cam_z > 2.0:
            draw_list.append((cam_z, obj))

    draw_list.sort(key=lambda x: x[0], reverse=True)

    for _, obj in draw_list:
        vx = obj['x'] - px
        vy = obj['y'] - py
        vz_bottom = -pz

        cam_x = vx * R0x + vy * R0y
        cam_y_bottom = vx * U0x + vy * U0y + vz_bottom * U0z
        cam_z_bottom = vx * Fx + vy * Fy + vz_bottom * Fz
        if cam_z_bottom < 1.0:
            continue

        inv_z_bottom = 1.0 / cam_z_bottom
        u0 = halfW + cam_x * inv_z_bottom * f
        v_bottom = halfH - cam_y_bottom * inv_z_bottom * f
        sw = obj['w'] * inv_z_bottom * f
        if sw < 0.4:
            sw = 0.4

        vz_top = obj['h'] - pz
        cam_y_top = vx * U0x + vy * U0y + vz_top * U0z
        cam_z_top = vx * Fx + vy * Fy + vz_top * Fz
        if cam_z_top < 1.0:
            continue
        inv_z_top = 1.0 / cam_z_top
        v_top = halfH - cam_y_top * inv_z_top * f

        left = int(round(u0 - sw * 0.5))
        right = int(round(u0 + sw * 0.5))
        top = int(round(min(v_bottom, v_top)))
        bottom = int(round(max(v_bottom, v_top)))

        if right < 0 or left >= W or bottom < 0 or top >= H:
            continue

        side_dark_right = (cam_x > 0)
        screen_width = right - left + 1
        screen_height = bottom - top + 1

        for vy_p in range(top, bottom + 1):
            if vy_p < 0 or vy_p >= H:
                continue
            row = img[vy_p]

            for vx_p in range(left, right + 1):
                if vx_p < 0 or vx_p >= W:
                    continue

                if obj['type'] == 'tree':
                    # 树冠：上部椭圆形
                    vnorm = (vy_p - top) / screen_height if screen_height > 1 else 0
                    if vnorm < 0.6:
                        xnorm = (vx_p - u0) / (sw * 0.5) if sw > 0.5 else 0.0
                        ynorm = vnorm / 0.6
                        cx = 0.0
                        cy = 0.5
                        rx_ell = 0.7
                        ry_ell = 0.5
                        d2 = ((xnorm - cx) / rx_ell) ** 2 + ((ynorm - cy) / ry_ell) ** 2
                        if d2 <= 1.0:
                            if xnorm > 0:
                                row[vx_p] = darken((80, 140, 70), 0.9)
                            else:
                                row[vx_p] = (80, 140, 70)
                    elif vnorm >= 0.6:
                        xnorm = (vx_p - u0) / (sw * 0.5) if sw > 0.5 else 0.0
                        if abs(xnorm) < 0.3:
                            row[vx_p] = (110, 80, 50)
                    # 其他像素保持背景
                else:
                    # 楼房：基于世界坐标的窗户布局，保证窗户数量和位置不受终端尺寸影响
                    base_color = obj['color']

                    # 计算当前像素对应的建筑表面世界坐标（相对左边缘和地面）
                    world_u = (vx_p - left) / screen_width * obj['w'] if screen_width > 0 else 0
                    world_v = (bottom - vy_p) / screen_height * obj['h'] if screen_height > 0 else 0

                    # 判断是否在窗户区域（考虑边缘留白）
                    in_window = False
                    if (WALL_MARGIN <= world_u < obj['w'] - WALL_MARGIN and
                        WALL_MARGIN <= world_v < obj['h'] - WALL_MARGIN):
                        u_mod = (world_u - WALL_MARGIN) % WINDOW_SPACING_H
                        v_mod = (world_v - WALL_MARGIN) % WINDOW_SPACING_V
                        if u_mod < WINDOW_WIDTH_H and v_mod < WINDOW_HEIGHT_V:
                            in_window = True

                    if in_window:
                        if side_dark_right:
                            if vx_p > u0:
                                color = darken(WINDOW_DARK, 0.8)
                            else:
                                color = WINDOW_LIGHT
                        else:
                            if vx_p < u0:
                                color = darken(WINDOW_DARK, 0.8)
                            else:
                                color = WINDOW_LIGHT
                    else:
                        if side_dark_right:
                            if vx_p > u0:
                                color = darken(base_color, 0.65)
                            else:
                                color = base_color
                        else:
                            if vx_p < u0:
                                color = darken(base_color, 0.65)
                            else:
                                color = base_color

                    row[vx_p] = color

    # ---------- 滚转采样 ----------
    roll_c = math.cos(roll)
    roll_s = math.sin(roll)

    frame_rows = []
    scene_char_rows = H // 2
    for char_row in range(scene_char_rows):
        chars = []
        v_top = 2 * char_row
        v_bot = v_top + 1

        for u in range(W):
            du = u - halfW
            dv = v_top - halfH
            du0 = du * roll_c + dv * roll_s
            dv0 = -du * roll_s + dv * roll_c
            u0i = clamp(int(round(halfW + du0)), 0, W - 1)
            v0i = clamp(int(round(halfH + dv0)), 0, H - 1)
            r1, g1, b1 = img[v0i][u0i]

            dv = v_bot - halfH
            du0 = du * roll_c + dv * roll_s
            dv0 = -du * roll_s + dv * roll_c
            u0i = clamp(int(round(halfW + du0)), 0, W - 1)
            v0i = clamp(int(round(halfH + dv0)), 0, H - 1)
            r2, g2, b2 = img[v0i][u0i]

            chars.append((r1, g1, b1, r2, g2, b2))

        frame_rows.append(tuple(chars))

    return tuple(frame_rows)


# --------------------- 输入 ---------------------
def read_keys():
    keys = []
    if os.name == 'nt':
        import msvcrt
        while msvcrt.kbhit():
            ch = msvcrt.getch()
            try:
                k = ch.decode('utf-8').lower()
                keys.append(k)
            except Exception:
                pass
    else:
        import select
        while True:
            if select.select([sys.stdin], [], [], 0)[0]:
                ch = os.read(sys.stdin.fileno(), 1)
                if ch:
                    try:
                        k = ch.decode('utf-8').lower()
                        keys.append(k)
                    except Exception:
                        pass
                else:
                    break
            else:
                break
    return keys


def build_hud(state, width):
    speed = state['speed']
    alt = state['z']
    pitch_deg = math.degrees(state['pitch'])
    roll_deg = math.degrees(state['roll'])

    txt = (
        f" SPD {speed:5.1f} m/s | ALT {alt:5.1f} m | "
        f"PCH {pitch_deg:+6.1f} deg | ROL {roll_deg:+6.1f} deg | "
        f"Z/X speed  W/S pitch  A/D roll  Q quit"
    )

    if len(txt) > width:
        txt = txt[:width]
    else:
        txt = txt.ljust(width)

    return "\033[38;2;255;255;255;48;2;20;25;45m" + txt + "\033[0m"


# --------------------- 物理更新 ---------------------
def update(state, keys, dt):
    pitch_vel = 0.0
    roll_vel = 0.0
    accel = 0.0

    for k in keys:
        if k == 'w':
            pitch_vel -= PITCH_RATE
        elif k == 's':
            pitch_vel += PITCH_RATE
        elif k == 'a':
            roll_vel -= ROLL_RATE
        elif k == 'd':
            roll_vel += ROLL_RATE
        elif k == 'z':
            accel += ACCEL
        elif k == 'x':
            accel -= ACCEL

    state['pitch'] += math.radians(pitch_vel) * dt
    state['roll'] += math.radians(roll_vel) * dt

    state['pitch'] = clamp(state['pitch'], -MAX_ANGLE, MAX_ANGLE)
    state['roll'] = clamp(state['roll'], -MAX_ANGLE, MAX_ANGLE)

    state['yaw'] += 2.0 * state['roll'] * dt

    state['speed'] += accel * dt
    state['speed'] = clamp(state['speed'], SPEED_MIN, SPEED_MAX)

    cp = math.cos(state['pitch'])
    sp = math.sin(state['pitch'])
    cy = math.cos(state['yaw'])
    sy = math.sin(state['yaw'])

    Fx = sy * cp
    Fy = cy * cp
    Fz = sp

    state['x'] += Fx * state['speed'] * dt
    state['y'] += Fy * state['speed'] * dt
    state['z'] += Fz * state['speed'] * dt

    if state['z'] < 1.0:
        state['z'] = 1.0


# --------------------- 主循环 ---------------------
def main():
    # 初始尺寸
    size = shutil.get_terminal_size(fallback=(120, 30))
    cols = size.columns
    rows_total = size.lines
    if rows_total < 8:
        rows_total = 24

    scene_rows = rows_total - 1
    W = cols
    H = scene_rows * 2
    halfW = W / 2.0
    halfH = H / 2.0

    fov_rad = math.radians(FOV_V)
    f = (H / 2.0) / math.tan(fov_rad / 2.0)
    inv_f = 1.0 / f

    state = {
        'x': 0.0,
        'y': 0.0,
        'z': 30.0,
        'yaw': 0.0,
        'pitch': 0.0,
        'roll': 0.0,
        'speed': 20.0,
    }

    if os.name != 'nt':
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    else:
        old_settings = None

    sys.stdout.write("\033[?1049h\033[?25l")
    sys.stdout.flush()

    last_time = time.time()
    target_dt = 1.0 / 30.0

    # 记录上次尺寸，用于检测变化
    last_cols = cols
    last_rows = rows_total

    try:
        while True:
            now = time.time()
            dt = now - last_time
            last_time = now
            if dt > 0.1:
                dt = 0.1
            if dt <= 0:
                dt = 0.0001

            # 动态检测终端尺寸变化
            new_size = shutil.get_terminal_size(fallback=(120, 30))
            new_cols = new_size.columns
            new_rows = new_size.lines
            if new_rows < 8:
                new_rows = 24

            if new_cols != last_cols or new_rows != last_rows:
                # 尺寸变化，更新参数并清屏
                last_cols = new_cols
                last_rows = new_rows
                cols = new_cols
                rows_total = new_rows
                scene_rows = rows_total - 1
                W = cols
                H = scene_rows * 2
                halfW = W / 2.0
                halfH = H / 2.0
                f = (H / 2.0) / math.tan(fov_rad / 2.0)
                inv_f = 1.0 / f
                # 清屏并回到左上角
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.flush()

            keys = read_keys()
            if 'q' in keys:
                break

            update(state, keys, dt)

            frame = render_frame(state, W, H, halfW, halfH, f, inv_f)
            hud = build_hud(state, W)
            scene_str = tv.parse(frame)

            out = "\033[H" + hud + "\n" + scene_str
            sys.stdout.write(out)
            sys.stdout.flush()

            elapsed = time.time() - now
            sleep = target_dt - elapsed
            if sleep > 0:
                time.sleep(sleep)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?1049l\033[?25h")
        if os.name != 'nt':
            import termios
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        sys.stdout.flush()


if __name__ == "__main__":
    main()