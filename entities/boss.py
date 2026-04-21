import pygame as pg
import numpy as np
import random
import csv

# phase definitions per boss type (indexed by phases count)
_PHASE_TEMPLATES = {
    3: [
        (1.00, 8.0, ['normal']),
        (0.67, 5.0, ['normal', 'fast']),
        (0.33, 3.0, ['fast', 'fast', 'slow']),
    ],
    5: [
        (1.00, 8.0, ['normal']),
        (0.80, 6.0, ['fast']),
        (0.60, 4.0, ['normal', 'fast']),
        (0.40, 3.0, ['fast', 'slow']),
        (0.20, 2.0, ['fast', 'slow', 'car_boss']),
    ],
}

_BOSS_DATA = {}

def load_boss_data(csv_path='data/boss.csv'):
    global _BOSS_DATA
    _BOSS_DATA = {}
    try:
        with open(csv_path, newline='') as f:
            for row in csv.DictReader(f):
                phases = int(row['phases'])
                _BOSS_DATA[row['name']] = {
                    'hp':           int(row['hp']),
                    'width':        float(row['width']),
                    'height':       float(row['height']),
                    'image':        row['img_path'].strip(),
                    'y_offset':     float(row.get('y_offset', 0) or 0),
                    'summon_limit': int(row.get('summon_limit', 20) or 20),
                    'phases':       _PHASE_TEMPLATES.get(phases, _PHASE_TEMPLATES[3]),
                }
    except FileNotFoundError:
        print('[Boss] boss.csv not found')
    return _BOSS_DATA

def get_boss_data():
    if not _BOSS_DATA:
        load_boss_data()
    return _BOSS_DATA

PHASE_COLORS = [
    (100, 200, 100),
    (200, 200,  50),
    (220, 130,  30),
    (220,  50,  50),
    (180,   0, 200),
]


class Boss:
    FEET_OFFSET = 5.0

    def __init__(self, render, boss_type):
        cfg = get_boss_data().get(boss_type)
        if cfg is None:
            raise ValueError(f'Unknown boss type: {boss_type}')
        self.render        = render
        self.boss_type     = boss_type
        self.max_hp        = cfg['hp']
        self.hp            = cfg['hp']
        self.width         = cfg['width']
        self.height        = cfg['height']
        self.y_offset      = cfg['y_offset']
        self.summon_limit  = cfg['summon_limit']
        self._phases       = cfg['phases']
        self.alive         = True
        self._summon_timer = 0.0
        self._depth_offset = 0.0
        self.distance_walked = 0  # 0 so towers prefer lane enemies first

        from world.map import SPAWN_POSITION, GRID_ORIGIN_Z
        self.position = np.array([
            SPAWN_POSITION[0] + 1.0,
            self.FEET_OFFSET + self.y_offset,
            GRID_ORIGIN_Z,
        ], dtype=float)

        self._image = None
        try:
            self._image = pg.image.load(cfg['image']).convert_alpha()
        except Exception as e:
            print(f'[Boss] image load failed: {e}')

    # ── phase ─────────────────────────────────────────────────────────

    def _phase_index(self):
        frac = self.hp / self.max_hp
        idx = 0
        for i, (thresh, _, _) in enumerate(self._phases):
            if frac <= thresh:
                idx = i
        return idx

    def _current_phase_data(self):
        return self._phases[self._phase_index()]

    # ── update ────────────────────────────────────────────────────────

    def update(self, dt):
        if not self.alive:
            return
        _, interval, pool = self._current_phase_data()
        self._summon_timer += dt
        if self._summon_timer >= interval:
            self._summon_timer -= interval
            self._summon(pool)

    def _summon(self, pool):
        from entities.enemy import make_enemy
        from world.map import SPAWN_POSITION, BASE_POSITION, GRID_ROWS
        enemies = getattr(self.render, 'enemies', None)
        if not enemies:
            return
        current_count = sum(len(lane) for lane in enemies)
        if current_count >= self.summon_limit:
            return
        sp = [SPAWN_POSITION[0], 0, 0]
        wp = [[BASE_POSITION[0], 0, 0]]
        for enemy_type in pool:
            if sum(len(lane) for lane in enemies) >= self.summon_limit:
                break
            lane = random.randint(0, GRID_ROWS - 1)
            if 0 <= lane < len(enemies):
                e = make_enemy(self.render, enemy_type, sp, wp, lane=lane)
                enemies[lane].append(e)

    # ── combat ────────────────────────────────────────────────────────

    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        dmg_list = getattr(self.render, 'damage_numbers', None)
        if dmg_list is not None:
            dmg_list.append({
                'x': self.position[0] + random.uniform(-0.5, 0.5),
                'y': self.position[1] + self.height * 0.35,
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
        bosses = getattr(self.render, 'bosses', None)
        if bosses and self in bosses:
            bosses.remove(self)
        player = getattr(self.render, 'player', None)
        if player:
            player.gold += 500
        # ล้าง enemy ทั้งหมดทันที → wave_manager ตรวจ all_dead → victory
        enemies = getattr(self.render, 'enemies', None)
        if enemies:
            for lane in enemies:
                lane.clear()

    # ── render ────────────────────────────────────────────────────────

    def push_to_pool(self):
        if not self.alive:
            return
        world_pos = np.array([*self.position, 1.0])
        cam_pos   = world_pos @ self.render.camera.camera_matrix()
        if cam_pos[2] < 2.0:
            return
        proj = cam_pos @ self.render.projection.projection_matrix
        if abs(proj[3]) < 1e-6:
            return
        proj /= proj[3]
        sx    = int(proj[0] * self.render.H_WIDTH  + self.render.H_WIDTH)
        sy    = int(-proj[1] * self.render.H_HEIGHT + self.render.H_HEIGHT)
        scale = self.render.H_WIDTH / cam_pos[2]
        w     = max(1, int(self.width  * scale))
        h     = max(1, int(self.height * scale))
        W, H  = self.render.WIDTH, self.render.HEIGHT
        if sx + w // 2 < 0 or sx - w // 2 > W or sy + h // 2 < 0 or sy - h // 2 > H:
            return
        surf = self._make_sprite(w, h)
        self.render.polygon_pool.append({
            'depth': cam_pos[2] + self._depth_offset,
            'billboard': {
                'surf': surf,
                'sx': sx, 'sy': sy, 'w': w, 'h': h,
                'hp_frac':   self.hp / self.max_hp,
                'enemy_ref': self,
                'bar_w': w,
                'bar_x': sx - w // 2,
                'bar_y': sy - h // 2 - 14,
            },
            'points': [],
            'color':  None,
        })

    def _make_sprite(self, w, h):
        if self._image:
            if not hasattr(self, '_cached_surf') or self._cached_size != (w, h):
                self._cached_surf = pg.transform.scale(self._image, (w, h))
                self._cached_size = (w, h)
            return self._cached_surf
        surf = pg.Surface((w, h), pg.SRCALPHA)
        surf.fill((120, 0, 180, 230))
        pg.draw.rect(surf, (255, 100, 255), (0, 0, w, h), max(2, w // 12))
        return surf

    def draw_hp_bar(self, screen, entry):
        b    = entry['billboard']
        bw, bx, by = b['bar_w'], b['bar_x'], b['bar_y']
        frac = b['hp_frac']
        bh = max(6, bw // 10)
        pg.draw.rect(screen, (40, 0, 40),   (bx, by, bw, bh))
        col = PHASE_COLORS[min(self._phase_index(), len(PHASE_COLORS) - 1)]
        pg.draw.rect(screen, col,            (bx, by, int(bw * frac), bh))
        pg.draw.rect(screen, (220, 150, 255), (bx, by, bw, bh), 1)

    def draw_boss_hud(self, screen, font):
        W, H   = screen.get_width(), screen.get_height()
        frac   = self.hp / self.max_hp
        pi     = self._phase_index()
        total  = len(self._phases)
        color  = PHASE_COLORS[min(pi, len(PHASE_COLORS) - 1)]

        bar_w = W * 2 // 3
        bar_h = 22
        bar_x = (W - bar_w) // 2
        bar_y = H - 52

        pg.draw.rect(screen, (20, 0, 30),    (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
        pg.draw.rect(screen, (60, 0, 80),    (bar_x, bar_y, bar_w, bar_h))
        pg.draw.rect(screen, color,          (bar_x, bar_y, int(bar_w * frac), bar_h))
        pg.draw.rect(screen, (200, 100, 255), (bar_x, bar_y, bar_w, bar_h), 2)

        name  = 'BOSS' if self.boss_type == 'boss_3phase' else 'FINAL BOSS'
        label = font.render(
            f'{name}   Phase {pi + 1} / {total}   {self.hp} / {self.max_hp}',
            True, (255, 200, 255))
        screen.blit(label, (bar_x, bar_y - 20))
