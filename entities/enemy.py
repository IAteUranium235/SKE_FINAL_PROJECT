import pygame as pg
import numpy as np
import math
import csv
import random
from world.map import GRID_ORIGIN_Z, CELL_SIZE, GRID_ROWS

_ENEMY_DATA = {}

def load_enemy_data(csv_path='enemy.csv'):
    global _ENEMY_DATA
    _ENEMY_DATA = {}
    try:
        with open(csv_path, newline='') as f:
            for row in csv.DictReader(f):
                _ENEMY_DATA[row['name']] = {
                    'hp':         int(row['hp']),
                    'walk_speed': float(row['walk_speed']),
                    'damage':     int(row['damage']),
                    'reward':     int(row['reward']),
                    'width':      float(row['width']),
                    'height':     float(row['height']),
                    'image_path': row['image_path'],
                    'special':    row.get('special', '').strip(),
                }
    except FileNotFoundError:
        print('[Enemy] enemy.csv not found')
    return _ENEMY_DATA

def get_enemy_types():
    if not _ENEMY_DATA:
        load_enemy_data()
    return _ENEMY_DATA

def make_enemy(render, enemy_type, position, waypoints, lane):
    """สร้าง Enemy จากชื่อ type ใน enemy.csv"""
    data = get_enemy_types().get(enemy_type)
    if data is None:
        raise ValueError(f'Unknown enemy type: {enemy_type}')
    return Enemy(
        render,
        position=position,
        waypoints=waypoints,
        hp=data['hp'],
        walk_speed=data['walk_speed'],
        damage=data['damage'],
        reward=data['reward'],
        width=data['width'],
        height=data['height'],
        image_path=data['image_path'],
        lane=lane,
        special=data.get('special', ''),
    )


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
                 lane=0,
                 special=''):

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

        self.lane            = lane
        self.special         = special
        self._depth_offset   = random.uniform(-0.3, 0.3)
        self.distance_walked = 0.0
        self.stopped         = False
        # car_boss
        self._spawn_timer    = 0.0
        self.SPAWN_INTERVAL  = 7.0
        # portal_dog
        self._teleported     = False
        self._portal_img2    = None   # โหลดล่วงหน้า

        # sprite
        self._image = None
        if image_path:
            self._image = self._load_image(image_path)
        if self.special == 'portal_dog':
            self._portal_img2 = self._load_image('portal_dog_2.png')

    def _load_image(self, path):
        try:
            img = pg.image.load(path)
            if path.lower().endswith(('.jpg', '.jpeg')):
                img = img.convert()
                img.set_colorkey((255, 255, 255))
            else:
                img = img.convert_alpha()
            return img
        except Exception as e:
            print(f"[Enemy] ไม่พบรูป {path}: {e}")
            return None

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        if not self.alive:
            return

        # car_boss: spawn motorcycle ทุก 7 วิ
        if self.special == 'car_boss':
            self._spawn_timer += dt
            if self._spawn_timer >= self.SPAWN_INTERVAL:
                self._spawn_timer = 0.0
                self._spawn_motorcycle()

        self._check_tower_ahead()

        # portal_dog: วาปผ่าน tower ครั้งแรกที่เจอ
        if self.special == 'portal_dog' and self.stopped and not self._teleported:
            self._teleport_forward()
            return

        if self.stopped:
            self._attack_timer += dt
            self._attack_tower()
            return

        if self.wp_index < len(self.waypoints):
            self._move_toward_waypoint(dt)
        else:
            self.reached_end = True
            self._attack_timer += dt
            self._attack_base()

    def _spawn_motorcycle(self):
        from world.map import BASE_POSITION
        wp = [[BASE_POSITION[0], 0, 0]]
        sp = [self.position[0], 0, 0]
        enemies = getattr(self.render, 'enemies', None)
        if enemies and 0 <= self.lane < len(enemies):
            m = make_enemy(self.render, 'motorcycle', sp, wp, lane=self.lane)
            m.distance_walked = self.distance_walked
            enemies[self.lane].append(m)

    def _teleport_forward(self):
        self.position[0] += CELL_SIZE
        self.stopped       = False
        self._teleported   = True
        if self._portal_img2:
            self._image = self._portal_img2
            if hasattr(self, '_cached_surf'):
                del self._cached_surf
                del self._cached_size

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

        from world.map import GRID_ORIGIN_X, GRID_COLS
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
                #self.position[0] = stop_x  # snap ไปที่ขอบ
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

        from world.map import GRID_ORIGIN_X, CELL_SIZE, GRID_COLS
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

    def _attack_base(self):
        if self._attack_timer < 1.0 / self.attack_rate:
            return
        self._attack_timer = 0.0
        if hasattr(self.render, 'base_hp'):
            self.render.base_hp = max(0, self.render.base_hp - self.damage)

    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        dmg_list = getattr(self.render, 'damage_numbers', None)
        if dmg_list is not None:
            dmg_list.append({
                'x': self.position[0] + random.uniform(-0.3, 0.3),
                'y': self.position[1] + self.height * 0.5,
                'z': self.position[2],
                'value':     amount,
                'timer':     1.2,
                'max_timer': 1.2,
            })
        if self.hp <= 0:
            self.hp = 0
            self.die()

    def die(self):
        self.alive = False
        player = getattr(self.render, 'player', None)
        if player:
            player.gold += self.reward
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

        if cam_pos[2] < 2.0:   # ใกล้กล้องเกินไป — ข้าม
            return

        # project ลงหน้าจอ
        proj = cam_pos @ self.render.projection.projection_matrix
        if abs(proj[3]) < 1e-6:
            return
        proj /= proj[3]

        sx    = int(proj[0] * self.render.H_WIDTH  + self.render.H_WIDTH)
        sy    = int(-proj[1] * self.render.H_HEIGHT + self.render.H_HEIGHT)
        scale = self.render.H_WIDTH / cam_pos[2]
        w_half = int(self.width  * scale / 2)
        h_half = int(self.height * scale / 2)
        # ถ้าอยู่นอกจอทั้งหมด — ไม่วาด
        W, H = self.render.WIDTH, self.render.HEIGHT
        if sx + w_half < 0 or sx - w_half > W or sy + h_half < 0 or sy - h_half > H:
            return
        w     = max(1, int(self.width  * scale))
        h     = max(1, int(self.height * scale))

        # สร้าง sprite surface
        surf = self._make_sprite(w, h)

        self.render.polygon_pool.append({
            'depth':     cam_pos[2] + self._depth_offset,
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
            # cache — scale ใหม่เฉพาะตอนขนาดเปลี่ยน
            if not hasattr(self, '_cached_surf') or self._cached_size != (w, h):
                self._cached_surf = pg.transform.scale(self._image, (w, h))
                self._cached_size = (w, h)
            return self._cached_surf

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
