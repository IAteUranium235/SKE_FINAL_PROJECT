import numpy as np
import pygame as pg
from core.object_3d import Object3D
from core.hitbox import Hitbox
from core.matrix_function import *


class Wall:
    """
    กำแพงสี่เหลี่ยม พร้อม AABB collision (infinite height)

    พารามิเตอร์:
        render   — SoftwareRender instance
        position — (x, y, z) จุดกึ่งกลางกำแพง
        width    — ความกว้าง (แกน X)
        depth    — ความหนา (แกน Z)
        height   — ความสูง (แกน Y)
        color    — สี pygame.Color
    """

class Wall:
    def __init__(self, render, position, width=5.0, depth=0.5, height=3.0, color=None):
        self.render   = render
        self.position = np.array(position, dtype=float)
        self.width    = width
        self.depth    = depth
        self.height   = height
        self.color    = color or pg.Color('sienna')

        # ✅ AABB bounds ครบทุกแกน
        self.min_x = self.position[0] - self.width  / 2
        self.max_x = self.position[0] + self.width  / 2
        self.min_y = self.position[1]
        self.max_y = self.position[1] + self.height
        self.min_z = self.position[2] - self.depth  / 2
        self.max_z = self.position[2] + self.depth  / 2

        self._mesh = self._build_mesh()

    # =========================================================
    # BUILD MESH
    # =========================================================

    def _build_mesh(self):
        x, y, z = self.position
        hw = self.width  / 2  # half width
        hd = self.depth  / 2  # half depth
        h  = self.height

        # 8 มุมของกล่อง
        vertexes = [
            [-hw, 0,  -hd, 1],  # 0 ล่าง-หน้า-ซ้าย
            [ hw, 0,  -hd, 1],  # 1 ล่าง-หน้า-ขวา
            [ hw, 0,   hd, 1],  # 2 ล่าง-หลัง-ขวา
            [-hw, 0,   hd, 1],  # 3 ล่าง-หลัง-ซ้าย
            [-hw, h,  -hd, 1],  # 4 บน-หน้า-ซ้าย
            [ hw, h,  -hd, 1],  # 5 บน-หน้า-ขวา
            [ hw, h,   hd, 1],  # 6 บน-หลัง-ขวา
            [-hw, h,   hd, 1],  # 7 บน-หลัง-ซ้าย
        ]

        # triangulate ทุกหน้า (winding order ทวนเข็ม = หันหน้าออก)
        faces = [
            # หน้า
            [0, 1, 5], [0, 5, 4],
            # หลัง
            [2, 3, 7], [2, 7, 6],
            # ซ้าย
            [3, 0, 4], [3, 4, 7],
            # ขวา
            [1, 2, 6], [1, 6, 5],
            # บน
            [4, 5, 6], [4, 6, 7],
            # ล่าง
            [3, 2, 1], [3, 1, 0],
        ]

        color_faces = [(self.color, face) for face in faces]
        obj = Object3D(self.render, vertexes, faces, color_faces)
        obj.matrix = translate([x, y, z])
        return obj

    # =========================================================
    # COLLISION
    # =========================================================

    def check_collision(self, hitbox):
        return hitbox.resolve_wall(self)

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):
        self._mesh.draw()
