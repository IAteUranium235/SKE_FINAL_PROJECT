import pygame as pg
from tower import Tower
from matrix_function import *


class Wrench:
    TOWER_FILEPATH  = 'resource/Turret.obj'
    WRENCH_FILEPATH = 'resource/wrench.obj'

    def __init__(self, player):
        self.player   = player
        self.render   = player.render
        self.name     = 'Wrench'
        self.equipped = False

        # โหลด wrench obj
        self._obj = self.render.load_obj(self.WRENCH_FILEPATH)
        self._obj.double_sided       = True
        self._obj.skip_frustum_check = True

    def on_equip(self):
        self.equipped = True

    def on_unequip(self):
        self.equipped = False

    def update(self, dt):
        if not self.equipped:
            return
        # copy matrix จาก arm_l (ซ้ายจริงๆ ในโค้ด)
        offset = translate([0.4, -0.4, 0])
        rotate = rotate_x(math.pi/2)
        self._obj.matrix = offset @ self.player.arm_l.matrix.copy()
        self._obj.matrix = rotate @ self._obj.matrix
    def draw(self):
        """เรียกใน draw loop หลัง flush player"""
        if not self.equipped:
            return
        self._obj.draw()
        self.render._flush_pool()
        #self.render.polygon_pool.clear()

    def draw_hud(self, screen):
        pass

    def handle_click(self):
        """คลิกซ้าย — วาง/ลบ tower ตรง grid ที่ player ยืนอยู่"""
        grid_pos = self.player.get_grid_position()
        if grid_pos is None:
            return

        row, col = grid_pos
        grid = self.render.placement_grid

        if grid[row][col] is None:
            tower = Tower(self.render, row=row, col=col,
                          filepath=self.TOWER_FILEPATH)
            grid[row][col] = tower
        else:
            grid[row][col].die()
