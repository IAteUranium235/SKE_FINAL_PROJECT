import pygame as pg
import numpy as np
import math
from map import GRID_ORIGIN_Z, CELL_SIZE, GRID_ROWS


class Enemy:
    """
    Enemy แบบ Doom-style — sprite 2D หันหน้าเข้าหากล้องเสมอ (billboard)

    พารามิเตอร์:
        render      — SoftwareRender instance
        position    — [x, y, z] ตำแหน่ง spawn
        waypoints   — list of [x, y, z] จุดที่ enemy เดินไป (ไปจนถึง base)
        hp          — HP เริ่มต้น
        walk_speed  — ความเร็วเดิน (world units/frame)
        damage      — ดาเมจที่ทำกับ base เมื่อถึงที่หมาย
        reward      — เงินที่ได้เมื่อ kill
        width       — ขนาด sprite กว้าง (world units)
        height      — ขนาด sprite สูง (world units)
        color       — สีของ placeholder sprite (ถ้าไม่มีรูป)
    """

    FEET_OFFSET = 1.5   # ระยะจากกลาง position ลงมาถึงพื้น

    def __init__(self, render, position,
                 waypoints=None,
                 hp=100,
                 walk_speed=0.04,
                 damage=10,
                 reward=20,
                 width=1.8,
                 height=2.5,
                 color=(180, 30, 30),
                 image_path=None,
                 lane=0):

        self.render      = render
        # Z position คำนวณจาก lane (row ของ grid)
        lane_z = GRID_ORIGIN_Z - CELL_SIZE * GRID_ROWS / 2 + lane * CELL_SIZE + CELL_SIZE / 2
        self.position    = np.array([position[0],
                                     position[1] + self.FEET_OFFSET,
                                     lane_z], dtype=float)
        # waypoints — override Z ให้ตรงกับ lane
        self.waypoints   = [np.array([wp[0], wp[1] if len(wp) > 1 else 0, lane_z], dtype=float) for wp in (waypoints or [])]
        self.wp_index    = 0          # waypoint ปัจจุบัน

        self.max_hp      = hp
        self.hp          = hp
        self.walk_speed  = walk_speed
        self.damage      = damage
        self.reward      = reward
        self.width       = width
        self.height      = height
        self.color       = color
        self.attack_rate    = 1.0    # โจมตีกี่ครั้งต่อวินาที
        self._attack_timer  = 0.0
        self.alive          = True
        self.reached_end    = False   # ถึง base แล้ว

        self.lane           = lane    # row ของ grid (0-4) คำนวณจาก Z
        self.distance_walked = 0.0   # ระยะทางที่เดินมาแล้ว
        self.stopped        = False   # หยุดเพราะเจอ tower

        # sprite — ถ้ามีรูปใช้รูป ถ้าไม่มีใช้ placeholder สีทึบ
        self._image = None
        if image_path:
            try:
                self._image = pg.image.load(image_path).convert_alpha()
            except Exception as e:
                print(f"[Enemy] ไม่พบรูป {image_path}: {e}")

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        if not self.alive:
            return

        # ถึงแม้หยุดอยู่ ก็ยังเช็ค grid ทุก frame
        self._check_tower_ahead()

        if self.stopped:
            self._attack_timer += dt
            self._attack_tower()
            return

        if self.wp_index < len(self.waypoints):
            self._move_toward_waypoint(dt)
        else:
            self.reached_end = True

    def _move_toward_waypoint(self, dt):
        target = self.waypoints[self.wp_index]
        dx = target[0] - self.position[0]
        dz = target[2] - self.position[2]
        dist = math.sqrt(dx**2 + dz**2)
        if dist < 0.3:
            self.wp_index += 1
            return

        speed = self.walk_speed * dt * 60
        self.position[0] += (dx / dist) * speed
        self.position[2] += (dz / dist) * speed
        self.distance_walked += speed

    def _check_tower_ahead(self):
        grid = getattr(self.render, 'placement_grid', None)
        if grid is None:
            return

        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0

        from map import GRID_ORIGIN_X, GRID_COLS
        grid_left_x = GRID_ORIGIN_X - CELL_SIZE * GRID_COLS / 2
        col = int((self.position[0] - grid_left_x) / CELL_SIZE)
        row = self.lane

        # กันออกนอก grid
        if row < 0 or row >= rows or col < 0 or col >= cols:
            self.stopped = False
            return

        if grid[row][col] is not None:
            # หยุดที่ขอบซ้ายของ cell (ก่อนเข้า cell ที่มี tower)
            stop_x = grid_left_x + col * CELL_SIZE
            if self.position[0] >= stop_x:
                self.position[0] = stop_x  # snap ไปที่ขอบ
                self.stopped = True
        else:
            self.stopped = False

    # =========================================================
    # COMBAT
    # =========================================================

    def _attack_tower(self):
        if self._attack_timer < 1.0 / self.attack_rate:
            return
        self._attack_timer = 0.0

        grid = getattr(self.render, 'placement_grid', None)
        if grid is None:
            return

        from map import GRID_ORIGIN_X, CELL_SIZE, GRID_COLS
        grid_left_x = GRID_ORIGIN_X - CELL_SIZE * GRID_COLS / 2
        col = int((self.position[0] - grid_left_x) / CELL_SIZE)
        row = self.lane

        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        if row < 0 or row >= rows or col < 0 or col >= cols:
            return

        target = grid[row][col]
        if target is not None and hasattr(target, 'take_damage'):
            target.take_damage(self.damage)

    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.die()

    def die(self):
        self.alive = False
        # ลบออกจาก enemies[lane]
        enemies = getattr(self.render, 'enemies', None)
        if enemies and 0 <= self.lane < len(enemies):
            lane_list = enemies[self.lane]
            if self in lane_list:
                lane_list.remove(self)

    # =========================================================
    # DRAW (billboard + HP bar)
    # =========================================================

    def push_to_pool(self):
        """push sprite เข้า polygon_pool พร้อม depth — sort รวมกับ objects อื่น"""
        if not self.alive:
            return

        # แปลง position เป็น camera space
        world_pos = np.array([*self.position, 1.0])
        cam_pos   = world_pos @ self.render.camera.camera_matrix()

        if cam_pos[2] < 0.3:   # อยู่หลังกล้อง
            return

        # project ลงหน้าจอ
        proj = cam_pos @ self.render.projection.projection_matrix
        if abs(proj[3]) < 1e-6:
            return
        proj /= proj[3]

        sx    = int(proj[0] * self.render.H_WIDTH  + self.render.H_WIDTH)
        sy    = int(-proj[1] * self.render.H_HEIGHT + self.render.H_HEIGHT)
        scale = self.render.H_WIDTH / cam_pos[2]
        w     = max(1, int(self.width  * scale))
        h     = max(1, int(self.height * scale))

        # สร้าง sprite surface
        surf = self._make_sprite(w, h)

        self.render.polygon_pool.append({
            'depth':     cam_pos[2],
            'billboard': {
                'surf': surf,
                'sx': sx, 'sy': sy,
                'w': w,   'h': h,
                # HP bar info ส่งไปวาดหลัง blit
                'hp_frac': self.hp / self.max_hp,
                'enemy_ref': self,
                'bar_w': w,
                'bar_x': sx - w // 2,
                'bar_y': sy - h // 2 - 10,
            },
            'points': [],
            'color':  None,
        })

    def _make_sprite(self, w, h):
        if self._image:
            return pg.transform.scale(self._image, (w, h))

        # placeholder — สี่เหลี่ยมสีแดงเข้ม + outline
        surf = pg.Surface((w, h), pg.SRCALPHA)
        surf.fill((*self.color, 220))
        # ขอบ
        pg.draw.rect(surf, (255, 80, 80), (0, 0, w, h), max(1, w // 20))
        # ตา (สองจุดขาว)
        ew = max(2, w // 8)
        eh = max(2, h // 10)
        ex1 = w // 3 - ew // 2
        ex2 = 2 * w // 3 - ew // 2
        ey  = h // 3
        pg.draw.ellipse(surf, (255, 255, 200), (ex1, ey, ew, eh))
        pg.draw.ellipse(surf, (255, 255, 200), (ex2, ey, ew, eh))
        return surf

    def draw_hp_bar(self, screen, entry):
        """วาด HP bar เหนือ sprite — เรียกหลัง blit"""
        b = entry['billboard']
        bw   = b['bar_w']
        bx   = b['bar_x']
        by   = b['bar_y']
        frac = b['hp_frac']

        bh = max(4, bw // 12)
        # พื้นหลังสีเทา
        pg.draw.rect(screen, (60, 60, 60), (bx, by, bw, bh))
        # HP สีเขียว → แดงตาม frac
        r = int(255 * (1 - frac))
        g = int(255 * frac)
        pg.draw.rect(screen, (r, g, 0), (bx, by, int(bw * frac), bh))
        # ขอบ
        pg.draw.rect(screen, (200, 200, 200), (bx, by, bw, bh), 1)
