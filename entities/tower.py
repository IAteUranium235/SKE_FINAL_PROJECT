import pygame as pg
import numpy as np
import os
import csv
import math
from core.object_3d import Object3D
from core.matrix_function import *

_TURRET_DATA = {}

def load_turret_data(csv_path='data/turret.csv'):
    global _TURRET_DATA
    _TURRET_DATA = {}
    try:
        with open(csv_path, newline='') as f:
            for row in csv.DictReader(f):
                _TURRET_DATA[row['name']] = {
                    'file_path': row['file_path'],
                    'offset':    (float(row['offset_x']), float(row['offset_y']), float(row['offset_z'])),
                    'rotate_y':  float(row['rotate_y']),
                    'hp':        int(row['hp']),
                    'damage':    int(row['damage']),
                    'fire_rate': float(row['fire_rate']),
                    'range':     float(row.get('range', 0) or 999),
                    'price':     int(row['price']),
                    'special':       row.get('special', '').strip(),
                    'unlock_level':  int(row.get('unlock_level', 1) or 1),
                }
    except FileNotFoundError:
        print('[Tower] turret.csv not found')
    return _TURRET_DATA

def get_turret_types():
    if not _TURRET_DATA:
        load_turret_data()
    return _TURRET_DATA


class Tower:
    MONEY_GEN_INTERVAL = 5.0   # วินาที
    MONEY_GEN_AMOUNT   = 15    # gold ต่อ tick

    def __init__(self, render, row, col, filepath,
                 hp=100, fire_rate=1.0, damage=20,
                 offset=(0.0, 0.0, 0.0), rotate_y=math.pi/2,
                 price=50, special='', range=999):
        self.render      = render
        self.row         = row
        self.col         = col
        self.max_hp      = hp
        self.hp          = hp
        self.fire_rate   = fire_rate
        self.damage      = damage
        self.price       = price
        self.special     = special
        self.range       = range
        self.alive       = True
        self._fire_timer = 0.0
        self._money_timer = 0.0

        self.obj = render.load_obj(filepath)
        self.obj.double_sided       = True
        self.obj.skip_frustum_check = True
        self.obj.rotate_y(rotate_y)
        self.position   = self._grid_to_world(row, col, offset)
        self.obj.matrix = translate(self.position)

    def _grid_to_world(self, row, col, offset=(0.0, 0.0, 0.0)):
        from world.map import GRID_ORIGIN_X, GRID_ORIGIN_Z, CELL_SIZE, GRID_ROWS, GRID_COLS
        half_w = CELL_SIZE * GRID_COLS / 2
        half_h = CELL_SIZE * GRID_ROWS / 2
        wx = GRID_ORIGIN_X - half_w + col * CELL_SIZE + CELL_SIZE / 2 + offset[0]
        wz = GRID_ORIGIN_Z - half_h + row * CELL_SIZE + CELL_SIZE / 2 + offset[2]
        return [wx, 0.0 + offset[1], wz]

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        if not self.alive:
            return
        self._fire_timer += dt

        if self.special == 'money_gen':
            self._money_timer += dt
            if self._money_timer >= self.MONEY_GEN_INTERVAL:
                self._money_timer -= self.MONEY_GEN_INTERVAL
                player = getattr(self.render, 'player', None)
                if player:
                    player.gold += self.MONEY_GEN_AMOUNT
                    nums = getattr(self.render, 'damage_numbers', None)
                    if nums is not None:
                        nums.append({
                            'x': self.position[0],
                            'y': self.position[1] + 2.0,
                            'z': self.position[2],
                            'value':     self.MONEY_GEN_AMOUNT,
                            'timer':     1.2,
                            'max_timer': 1.2,
                            'gold':      True,
                        })
        elif self.special == 'bomb':
            self._update_bomb()
        elif self.special == 'laser' and self.fire_rate > 0:
            self._fire_laser()
        elif self.special not in ('barrier',) and self.fire_rate > 0:
            self.fire()

    # =========================================================
    # COMBAT
    # =========================================================

    def fire(self):
        if self._fire_timer < 1.0 / self.fire_rate:
            return
        self._fire_timer = 0.0

        all_enemies = [e for row in self.render.enemies for e in row]
        if self.special == 'back_shooter':
            alive_enemies = [
                e for e in all_enemies
                if e.alive
                and e.lane == self.row
                and (
                    0 < e.position[0] - self.position[0] <= self.range
                    or (e.stopped and e.position[0] < self.position[0])
                )
            ]
        else:
            alive_enemies = [
                e for e in all_enemies
                if e.alive and not e.reached_end
                and e.lane == self.row
                and 0 < self.position[0] - e.position[0] <= self.range
            ]
        boss_targets = [b for b in getattr(self.render, 'bosses', []) if b.alive]
        all_targets  = alive_enemies + boss_targets
        if not all_targets:
            return

        target = max(all_targets, key=lambda e: e.distance_walked)
        target.take_damage(self.damage)

    def _fire_laser(self):
        """ยิงโดนทุก enemy ในแถวเดียวกันที่อยู่ด้านหน้าภายใน range"""
        if self._fire_timer < 1.0 / self.fire_rate:
            return
        self._fire_timer = 0.0
        all_enemies = getattr(self.render, 'enemies', None)
        if not all_enemies or self.row >= len(all_enemies):
            return
        for e in list(all_enemies[self.row]):
            if (e.alive and not e.reached_end
                    and 0 < self.position[0] - e.position[0] <= self.range):
                e.take_damage(self.damage)
        for b in list(getattr(self.render, 'bosses', [])):
            if b.alive:
                b.take_damage(self.damage)

    def _update_bomb(self):
        """ระเบิดเมื่อ enemy เดินมาถึง cell ของ bomb"""
        from world.map import GRID_ORIGIN_X, GRID_COLS, CELL_SIZE
        all_enemies = getattr(self.render, 'enemies', None)
        if not all_enemies:
            return
        grid_left_x = GRID_ORIGIN_X - CELL_SIZE * GRID_COLS / 2
        for lane_list in all_enemies:
            for e in list(lane_list):
                if e.alive and e.stopped:
                    e_col = int((e.position[0] - grid_left_x) / CELL_SIZE)
                    if e_col == self.col:
                        self._explode()
                        return

    def _explode(self):
        """ระเบิด AoE — โดนทุก enemy ภายใน radius 9 units (= 1.5 cell)"""
        from world.map import CELL_SIZE
        import math
        BOMB_DAMAGE = 700
        RADIUS      = CELL_SIZE * 1.5
        all_enemies = getattr(self.render, 'enemies', None)
        if all_enemies:
            for lane_list in all_enemies:
                for e in list(lane_list):
                    if e.alive:
                        dx = e.position[0] - self.position[0]
                        dz = e.position[2] - self.position[2]
                        if math.sqrt(dx*dx + dz*dz) <= RADIUS:
                            e.take_damage(BOMB_DAMAGE)
        self.die()

    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.die()

    def die(self):
        self.alive = False
        # ลบออกจาก placement_grid
        grid = getattr(self.render, 'placement_grid', None)
        if grid and 0 <= self.row < len(grid) and 0 <= self.col < len(grid[0]):
            self.render.placement_grid[self.row][self.col] = None
        # ลบออกจาก towers list
        #if self in self.render.towers:
        #    self.render.towers.remove(self)

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):
        if not self.alive:
            return
        self.obj.draw()
