import pygame as pg
import numpy as np
import math


# =========================================================
# MAP CONFIG
# =========================================================

GRID_COLS  = 6      # จำนวน column
GRID_ROWS  = 5      # จำนวน row
CELL_SIZE  = 6      # ขนาดแต่ละ cell (world units)

# ตำแหน่งกลาง grid ใน world
GRID_ORIGIN_X = 0.0
GRID_ORIGIN_Z = 0.0

# ตำแหน่ง Base (ซ้ายของ grid) — X ติดลบ = ซ้ายในหน้าจอ
BASE_POSITION  = [GRID_ORIGIN_X + CELL_SIZE * GRID_COLS / 2 + 12, 0, GRID_ORIGIN_Z]

# ตำแหน่ง Enemy Spawn (ขวาของ grid) — X บวก = ขวาในหน้าจอ
SPAWN_POSITION = [GRID_ORIGIN_X - CELL_SIZE * GRID_COLS / 2 - 12, 0, GRID_ORIGIN_Z]

# ตำแหน่ง Shop (บนกลาง grid)
SHOP_POSITION  = [GRID_ORIGIN_X, 0, GRID_ORIGIN_Z - CELL_SIZE * GRID_ROWS / 2 - 6]

# Player spawn
PLAYER_SPAWN   = [GRID_ORIGIN_X, 2, GRID_ORIGIN_Z + CELL_SIZE * GRID_ROWS / 2 + 10]


# =========================================================
# GRID
# =========================================================

class Grid:
    """
    Grid สำหรับวาง tower — GRID_ROWS x GRID_COLS cells
    แต่ละ cell เก็บว่ามี tower อยู่ไหม
    """

    def __init__(self):
        # None = ว่าง, มี object = มี tower
        self.cells = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    def world_to_cell(self, wx, wz):
        """แปลง world position → (row, col) — คืน None ถ้าอยู่นอก grid"""
        half_w = CELL_SIZE * GRID_COLS / 2
        half_h = CELL_SIZE * GRID_ROWS / 2
        lx = wx - (GRID_ORIGIN_X - half_w)
        lz = wz - (GRID_ORIGIN_Z - half_h)
        col = int(lx / CELL_SIZE)
        row = int(lz / CELL_SIZE)
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            return row, col
        return None

    def cell_to_world(self, row, col):
        """แปลง (row, col) → world position (กลาง cell)"""
        half_w = CELL_SIZE * GRID_COLS / 2
        half_h = CELL_SIZE * GRID_ROWS / 2
        wx = GRID_ORIGIN_X - half_w + col * CELL_SIZE + CELL_SIZE / 2
        wz = GRID_ORIGIN_Z - half_h + row * CELL_SIZE + CELL_SIZE / 2
        return wx, 0.0, wz

    def is_empty(self, row, col):
        return self.cells[row][col] is None

    def place(self, row, col, tower):
        self.cells[row][col] = tower

    def remove(self, row, col):
        self.cells[row][col] = None


# =========================================================
# MAP OBJECTS (วาดด้วย 3D box)
# =========================================================

def _make_box_verts_faces(pos, w, h, d, color):
    """สร้าง vertices และ faces สำหรับกล่อง"""
    x, y, z = pos
    hw, hd = w / 2, d / 2
    v = [
        [x-hw, y,   z-hd, 1], [x+hw, y,   z-hd, 1],
        [x+hw, y+h, z-hd, 1], [x-hw, y+h, z-hd, 1],
        [x-hw, y,   z+hd, 1], [x+hw, y,   z+hd, 1],
        [x+hw, y+h, z+hd, 1], [x-hw, y+h, z+hd, 1],
    ]
    f = [
        [0,1,2],[0,2,3],
        [5,4,7],[5,7,6],
        [4,0,3],[4,3,7],
        [1,5,6],[1,6,2],
        [3,2,6],[3,6,7],
    ]
    cf = [(color, face) for face in f]
    return v, f, cf


def _make_roof(pos, w, h, d, color):
    """หลังคาสามเหลี่ยม"""
    x, y, z = pos
    hw, hd = w / 2, d / 2
    peak_x = x
    v = [
        [x-hw, y, z-hd, 1], [x+hw, y, z-hd, 1],
        [x+hw, y, z+hd, 1], [x-hw, y, z+hd, 1],
        [peak_x, y+h, z-hd, 1], [peak_x, y+h, z+hd, 1],
    ]
    f = [
        [0,1,4],           # หน้า
        [2,3,5],           # หลัง
        [0,4,5],[0,5,3],   # ซ้าย
        [1,2,5],[1,5,4],   # ขวา
    ]
    cf = [(color, face) for face in f]
    return v, f, cf


# =========================================================
# MAP CLASS
# =========================================================

class Map:
    """
    Map หลักของเกม — สร้าง base, shop, spawn zone, grid

    ใช้งาน:
        from map import Map, PLAYER_SPAWN

        # ใน create_objects()
        self.map = Map(self)

        # ใน draw() ก่อน flush_pool
        self.map.draw()

        # ใน update()
        self.map.update(self.dt)
    """

    def __init__(self, render):
        self.render = render
        self.grid   = Grid()
        self._objects = []   # list of Object3D
        self._build()

    # =========================================================
    # BUILD
    # =========================================================

    def _build(self):
        from core.object_3d import Object3D

        objs = []

        # --- Grid cells (พื้น) — ใช้ layer เดียว gap ระหว่าง cell ทำให้เห็นขอบ ---
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                wx, wy, wz = self.grid.cell_to_world(row, col)
                # cell เล็กกว่า CELL_SIZE นิดหน่อย → เห็นเส้นขอบเป็นพื้นสีเข้มด้านล่าง
                v, f, cf = _make_box_verts_faces(
                    (wx, 0, wz), CELL_SIZE - 0.3, 0.05, CELL_SIZE - 0.3,
                    pg.Color(120, 160, 80)
                )
                objs.append(Object3D(self.render, v, f, cf))
        """
        # --- Base (ซ้าย) ---
        bx, by, bz = BASE_POSITION
        # ตัวบ้าน
        v, f, cf = _make_box_verts_faces(
            (bx, 0, bz), 8, 5, 7, pg.Color('burlywood')
        )
        objs.append(Object3D(self.render, v, f, cf))
        # หลังคา
        v, f, cf = _make_roof(
            (bx, 5, bz), 8.5, 3, 7.5, pg.Color('sienna')
        )
        objs.append(Object3D(self.render, v, f, cf))
        # ประตู
        v, f, cf = _make_box_verts_faces(
            (bx - 4.33, 0, bz), 0.1, 2.5, 1.8, pg.Color('saddlebrown')
        )
        objs.append(Object3D(self.render, v, f, cf))
        """
        """
        # --- Shop (กลางบน grid) ---
        sx, sy, sz = SHOP_POSITION
        # ตัว shop
        v, f, cf = _make_box_verts_faces(
            (sx, 0, sz), 5, 3.5, 4, pg.Color('wheat')
        )
        objs.append(Object3D(self.render, v, f, cf))
        # หลังคา shop
        v, f, cf = _make_roof(
            (sx, 3.5, sz), 5.5, 2, 4.5, pg.Color('chocolate')
        )
        objs.append(Object3D(self.render, v, f, cf))
        # ป้าย shop (กล่องแบนๆ)
        v, f, cf = _make_box_verts_faces(
            (sx, 4, sz - 2.1), 3, 1.2, 0.15, pg.Color('goldenrod')
        )
        objs.append(Object3D(self.render, v, f, cf))
        """
        # --- Enemy Spawn Zone (ขวา) ---
        ex, ey, ez = SPAWN_POSITION
        # เส้นขอบ spawn zone (กล่องแดงบางๆ)
        sz_w, sz_d = 6, CELL_SIZE * GRID_ROWS + 4
        for dx, dz, w, d in [
            (0, -sz_d/2, sz_w, 0.3),
            (0,  sz_d/2, sz_w, 0.3),
            (-sz_w/2, 0, 0.3, sz_d),
            ( sz_w/2, 0, 0.3, sz_d),
        ]:
            v, f, cf = _make_box_verts_faces(
                (ex+dx, 0, ez+dz), w, 0.3, d, pg.Color(180, 50, 50)
            )
            objs.append(Object3D(self.render, v, f, cf))
        # หมุดกลาง spawn
        v, f, cf = _make_box_verts_faces(
            (ex, 0, ez), 1, 3, 1, pg.Color(200, 60, 60)
        )
        objs.append(Object3D(self.render, v, f, cf))

        self._objects = objs

        # ✅ ปิด backface culling ทุก object ใน map
        for obj in self._objects:
            obj.double_sided = True

    # =========================================================
    # UPDATE / DRAW
    # =========================================================

    def update(self, dt):
        pass  # ค่อยใส่ทีหลัง

    def draw(self):
        """push polygon ทุกชิ้นเข้า render.polygon_pool — จะถูก flush และ sort depth ใน _flush_pool()"""
        for obj in self._objects:
            obj.draw()  # draw() โดยไม่ส่ง pool → เข้า self.render.polygon_pool อัตโนมัติ
