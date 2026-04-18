import csv
import pygame as pg


class WaveManager:
    BETWEEN_DELAY = 8.0   # วินาทีพักระหว่าง wave
    START_DELAY   = 8.0   # วินาทีเตรียมตัวก่อน wave 1

    def __init__(self, render, csv_path='wave_1.csv'):
        self.render         = render
        self._waves         = {}
        self.total_waves    = 0
        self.current_wave   = 0
        self._wave_timer    = 0.0
        self._spawn_idx     = 0
        self._spawn_queue   = []
        self._between       = False
        self._between_timer = 0.0
        self.finished       = False
        self._font          = pg.font.SysFont('Arial', 22, bold=True)
        self._font_sm       = pg.font.SysFont('Arial', 16)
        self._load(csv_path)

    def _load(self, csv_path):
        try:
            with open(csv_path, newline='') as f:
                for row in csv.DictReader(f):
                    w = int(row['wave'])
                    self._waves.setdefault(w, []).append({
                        'time': float(row['time']),
                        'lane': int(row['lane']),
                        'type': row['type'].strip(),
                    })
            self.total_waves = max(self._waves.keys()) if self._waves else 0
        except FileNotFoundError:
            print('[WaveManager] wave_1.csv not found')

    # ── public ────────────────────────────────────────────────────

    def start(self):
        self.current_wave   = 0          # 0 = ยังไม่เริ่ม wave ใด
        self.finished       = False
        self._between       = True       # countdown ก่อน wave 1
        self._between_timer = self.START_DELAY
        self._spawn_queue   = []
        self._spawn_idx     = 0
        self._wave_timer    = 0.0

    def _start_next_wave(self):
        self.current_wave += 1
        self._wave_timer  = 0.0
        self._spawn_idx   = 0
        self._between     = False
        entries = self._waves.get(self.current_wave, [])
        self._spawn_queue = sorted(entries, key=lambda e: e['time'])

    # ── update ────────────────────────────────────────────────────

    def update(self, dt):
        if self.finished:
            return

        if self._between:
            self._between_timer -= dt
            if self._between_timer <= 0:
                self._start_next_wave()
            return

        if self.current_wave == 0:
            return

        self._wave_timer += dt

        while self._spawn_idx < len(self._spawn_queue):
            entry = self._spawn_queue[self._spawn_idx]
            if self._wave_timer >= entry['time']:
                self._spawn(entry)
                self._spawn_idx += 1
            else:
                break

        all_spawned = (self._spawn_idx >= len(self._spawn_queue))
        all_dead    = all(len(lane) == 0 for lane in self.render.enemies)
        if all_spawned and all_dead:
            if self.current_wave >= self.total_waves:
                self.finished = True
            else:
                self._between       = True
                self._between_timer = self.BETWEEN_DELAY

    def _spawn(self, entry):
        from entities.enemy import make_enemy
        from world.map import SPAWN_POSITION, BASE_POSITION
        sp   = [SPAWN_POSITION[0], 0, 0]
        wp   = [[BASE_POSITION[0], 0, 0]]
        lane = entry['lane']
        if 0 <= lane < len(self.render.enemies):
            e = make_enemy(self.render, entry['type'], sp, wp, lane=lane)
            self.render.enemies[lane].append(e)

    # ── draw HUD ──────────────────────────────────────────────────

    def draw_hud(self, screen):
        if self.finished:
            return
        W = self.render.WIDTH
        if self._between:
            secs   = max(0, int(self._between_timer) + 1)
            next_w = self.current_wave + 1
            if self.current_wave == 0:
                line1 = self._font.render('Get Ready!', True, (255, 220, 80))
            else:
                line1 = self._font.render(f'Wave {self.current_wave} Clear!', True, (120, 255, 120))
            line2 = self._font_sm.render(f'Wave {next_w} starting in {secs}s...', True, (200, 200, 200))
            screen.blit(line1, (W // 2 - line1.get_width() // 2, 30))
            screen.blit(line2, (W // 2 - line2.get_width() // 2, 60))
        elif self.current_wave > 0:
            label = self._font.render(f'Wave {self.current_wave} / {self.total_waves}', True, (255, 220, 80))
            screen.blit(label, (W // 2 - label.get_width() // 2, 10))
