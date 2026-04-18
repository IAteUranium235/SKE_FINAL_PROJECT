import random
import pygame as pg
from core.object_3d import *
from world.wall import *
# =========================================================
# SIMPLE 3D OBJECTS
# =========================================================
GROUND_Y     = 0.0
GROUND_COLOR = (101, 139, 70)   # สีหญ้า
SKY_TOP      = (30,  60, 114)
SKY_BOTTOM   = (135, 190, 235)
FEET_OFFSET  = 1.5

def make_box(render, position, w, h, d, color):
    """สร้างกล่อง 3D ง่ายๆ"""
    from core.matrix_function import translate
    hw, hh, hd = w/2, h, d/2
    verts = [
        [-hw, 0,  -hd, 1], [ hw, 0,  -hd, 1], [ hw, hh, -hd, 1], [-hw, hh, -hd, 1],
        [-hw, 0,   hd, 1], [ hw, 0,   hd, 1], [ hw, hh,  hd, 1], [-hw, hh,  hd, 1],
    ]
    faces = [
        [0,1,2],[0,2,3],   # หน้า
        [5,4,7],[5,7,6],   # หลัง
        [4,0,3],[4,3,7],   # ซ้าย
        [1,5,6],[1,6,2],   # ขวา
        [3,2,6],[3,6,7],   # บน
        [4,5,1],[4,1,0],   # ล่าง
    ]
    color_faces = [(color, f) for f in faces]
    obj = Object3D(render, verts, faces, color_faces)
    obj.matrix = translate(position)
    return obj


def make_tree(render, position):
    """ต้นไม้ = ลำต้น + ยอด"""
    from core.matrix_function import translate
    trunk = make_box(render, position, 0.4, 2.0, 0.4, pg.Color('saddlebrown'))
    top_pos = [position[0], position[1] + 2.0, position[2]]
    top   = make_box(render, top_pos,   2.0, 2.5, 2.0, pg.Color('forestgreen'))
    return [trunk, top]


def make_house(render, position, color=None):
    """บ้านง่ายๆ = ตัวบ้าน + หลังคา"""
    color = color or pg.Color('burlywood')
    walls = make_box(render, position, 5, 3, 5, color)
    # หลังคา (กล่องแบน)
    roof_pos = [position[0], position[1]+3, position[2]]
    roof = make_box(render, roof_pos, 5.5, 0.8, 5.5, pg.Color('sienna'))
    return [walls, roof]


def generate_world(render):
    """สร้าง world แบบ random seed"""
    rng = random.Random(1337)
    objects = []

    # ต้นไม้ 30 ต้น
    for _ in range(30):
        x = rng.uniform(-80, 80)
        z = rng.uniform(-80, 80)
        if abs(x) > 8 or abs(z) > 8:   # ห่างจาก spawn
            objects += make_tree(render, [x, 0, z])

    # บ้าน 6 หลัง
    house_colors = [pg.Color('burlywood'), pg.Color('wheat'),
                    pg.Color('tan'), pg.Color('khaki')]
    for _ in range(6):
        x = rng.uniform(-60, 60)
        z = rng.uniform(-60, 60)
        if abs(x) > 12 or abs(z) > 12:
            objects += make_house(render, [x, 0, z],
                                  color=rng.choice(house_colors))

    # กำแพงยาว
    walls_list = []
    for i in range(4):
        angle = i * math.pi / 2
        wx = math.cos(angle) * 40
        wz = math.sin(angle) * 40
        walls_list.append(Wall(render, position=[wx, 0, wz],
                               width=20 if i % 2 == 0 else 0.5,
                               depth=0.5 if i % 2 == 0 else 20,
                               height=2.5, color=pg.Color('gray')))

    return objects, walls_list
