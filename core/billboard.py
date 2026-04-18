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

    def draw(self):
        pos = self.position @ self.render.camera.camera_matrix()

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

        # ถ้าอยู่นอกจอ — ไม่วาด
        W, H = self.render.WIDTH, self.render.HEIGHT
        if sx + w//2 < 0 or sx - w//2 > W or sy + h//2 < 0 or sy - h//2 > H:
            return

        # cap เพื่อกันสร้าง surface ขนาดยักษ์ตอนกล้องชิดมาก
        cw = min(w, W * 2)
        ch = min(h, H * 2)

        if not hasattr(self, '_cached_surf') or self._cached_size != (cw, ch):
            self._cached_surf = pg.transform.scale(self.image, (cw, ch))
            self._cached_size = (cw, ch)

        surf = self._cached_surf
        self.render.screen.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height() // 2))