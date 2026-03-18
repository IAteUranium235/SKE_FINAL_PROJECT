import pygame as pg
import numpy as np


class Billboard:
    """
    รูปภาพ 2D ที่ลอยอยู่ใน world space
    หันหน้าเข้าหากล้องเสมอ
    """

    def __init__(self, render, image_path, position, width=2.0, height=2.0):
        self.render   = render
        self.position = np.array([*position, 1.0])
        self.width    = width
        self.height   = height

        img = pg.image.load(image_path).convert_alpha()
        self.image = img  # เก็บ original ไว้ scale ทีหลัง

    def push_to_pool(self):
        """คำนวณ position + scale แล้วใส่เข้า polygon_pool พร้อม depth"""
        pos = self.position[:4] @ self.render.camera.camera_matrix()
        if pos[2] < 0.1:
            return
        proj = pos @ self.render.projection.projection_matrix
        if abs(proj[3]) < 1e-6:
            return
        proj /= proj[3]
        sx    = int(proj[0] * self.render.H_WIDTH  + self.render.H_WIDTH)
        sy    = int(-proj[1] * self.render.H_HEIGHT + self.render.H_HEIGHT)
        scale = self.render.H_WIDTH / pos[2]
        w     = max(1, int(self.width  * scale))
        h     = max(1, int(self.height * scale))
        surf  = pg.transform.scale(self.image, (w, h))
        self.render.polygon_pool.append({
            'depth':     pos[2],
            'billboard': {'surf': surf, 'sx': sx, 'sy': sy, 'w': w, 'h': h},
            'points':    [],
            'color':     None,
        })

    def draw(self):
        pos = self.position[:4] @ self.render.camera.camera_matrix()

        # อยู่หลังกล้อง — ไม่วาด
        if pos[2] < 0.1:
            return

        # project ลงหน้าจอ
        proj = pos @ self.render.projection.projection_matrix
        if abs(proj[3]) < 1e-6:
            return
        proj /= proj[3]

        sx = int(proj[0] * self.render.H_WIDTH  + self.render.H_WIDTH)
        sy = int(-proj[1] * self.render.H_HEIGHT + self.render.H_HEIGHT)

        # scale ขนาดตาม distance
        scale = self.render.H_WIDTH / pos[2]
        w = max(1, int(self.width  * scale))
        h = max(1, int(self.height * scale))

        scaled = pg.transform.scale(self.image, (w, h))
        self.render.screen.blit(scaled, (sx - w // 2, sy - h // 2))