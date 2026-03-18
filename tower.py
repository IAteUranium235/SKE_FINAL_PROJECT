import pygame as pg
import numpy as np
import os
from object_3d import Object3D
from matrix_function import *
import math


class Tower:
    def __init__(self, render, row, col, filepath,
                 hp=100, fire_rate=1.0, damage=20):
        self.render      = render
        self.row         = row
        self.col         = col
        self.max_hp      = hp
        self.hp          = hp
        self.fire_rate   = fire_rate
        self.damage      = damage
        self.alive       = True
        self._fire_timer = 0.0
        
        self.obj = render.load_obj(filepath)
        self.obj.double_sided       = True
        self.obj.skip_frustum_check = True
        if filepath=='resource/Turret.obj':
            self.obj.rotate_y(math.pi/2)
        self.position   = self._grid_to_world(row, col)
        self.obj.matrix = translate(self.position)

    def _grid_to_world(self, row, col):
        from map import GRID_ORIGIN_X, GRID_ORIGIN_Z, CELL_SIZE, GRID_ROWS, GRID_COLS
        half_w = CELL_SIZE * GRID_COLS / 2
        half_h = CELL_SIZE * GRID_ROWS / 2
        wx = GRID_ORIGIN_X - half_w + col * CELL_SIZE + CELL_SIZE / 2
        wz = GRID_ORIGIN_Z - half_h + row * CELL_SIZE + CELL_SIZE / 2
        return [wx, 0.0, wz]

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        if not self.alive:
            return
        self._fire_timer += dt
        self.fire()

    # =========================================================
    # COMBAT
    # =========================================================

    def fire(self):
        if self._fire_timer < 1.0 / self.fire_rate:
            return
        self._fire_timer = 0.0

        # flatten enemies ทุก lane แล้วกรองเฉพาะ lane เดียวกัน + อยู่ด้านหน้า tower
        all_enemies = [e for row in self.render.enemies for e in row]
        alive_enemies = [
            e for e in all_enemies
            if e.alive
            and not e.reached_end
            and e.lane == self.row
            and e.position[0] > self.position[0]
        ]
        if not alive_enemies:
            return

        target = max(alive_enemies, key=lambda e: e.distance_walked)
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
        # ลบออกจาก placement_grid
        grid = getattr(self.render, 'placement_grid', None)
        if grid and 0 <= self.row < len(grid) and 0 <= self.col < len(grid[0]):
            self.render.placement_grid[self.row][self.col] = None
        # ลบออกจาก towers list
        if self in self.render.towers:
            self.render.towers.remove(self)

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):
        if not self.alive:
            return
        self.obj.draw()
