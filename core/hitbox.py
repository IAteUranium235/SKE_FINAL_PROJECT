import numpy as np
import pygame as pg


class Hitbox:
    """
    AABB Hitbox สำหรับ character
    กล่องคลุมตัวละคร กำหนดด้วย width, height, depth และ offset จาก position ของ owner

    พารามิเตอร์:
        owner   — object ที่มี .position (np.array)
        width   — ความกว้าง (แกน X)
        height  — ความสูง  (แกน Y)
        depth   — ความลึก  (แกน Z)
        offset  — (x, y, z) ขยับ hitbox จาก position ของ owner
    """

    def __init__(self, owner, width=0.6, height=1.8, depth=0.6, offset=(0, 0, 0)):
        self.owner  = owner
        self.width  = width
        self.height = height
        self.depth  = depth
        self.offset = np.array(offset, dtype=float)
        self.debug = True

    # =========================================================
    # BOUNDS
    # =========================================================

    @property
    def center(self):
        return self.owner.position[:3] + self.offset

    @property
    def min_x(self): return self.center[0] - self.width  / 2
    @property
    def max_x(self): return self.center[0] + self.width  / 2
    @property
    def min_y(self): return self.center[1]
    @property
    def max_y(self): return self.center[1] + self.height
    @property
    def min_z(self): return self.center[2] - self.depth  / 2
    @property
    def max_z(self): return self.center[2] + self.depth  / 2

    # =========================================================
    # COLLISION VS WALL (AABB vs AABB)
    # =========================================================

    def resolve_wall(self, wall):
        """
        AABB vs AABB collision แล้วดัน owner ออกในแกนที่ overlap น้อยที่สุด
        คืนค่า True ถ้าชน
        """
        overlap_x = min(self.max_x, wall.max_x) - max(self.min_x, wall.min_x)
        overlap_z = min(self.max_z, wall.max_z) - max(self.min_z, wall.min_z)

        if overlap_x <= 0 or overlap_z <= 0:
            return False

        # ดันออกในแกนที่ overlap น้อยที่สุด (Minimum Penetration Axis)
        if overlap_x < overlap_z:
            if self.center[0] < (wall.min_x + wall.max_x) / 2:
                self.owner.position[0] -= overlap_x
            else:
                self.owner.position[0] += overlap_x
        else:
            if self.center[2] < (wall.min_z + wall.max_z) / 2:
                self.owner.position[2] -= overlap_z
            else:
                self.owner.position[2] += overlap_z

        return True

    # =========================================================
    # COLLISION VS HITBOX (AABB vs AABB)
    # =========================================================

    def resolve_wall(self, wall):
        # ✅ เช็ค Y ก่อน — ถ้ากระโดดข้ามความสูงกำแพงได้เลย
        if self.min_y >= wall.max_y or self.max_y <= wall.min_y:
            return False

        overlap_x = min(self.max_x, wall.max_x) - max(self.min_x, wall.min_x)
        overlap_z = min(self.max_z, wall.max_z) - max(self.min_z, wall.min_z)

        if overlap_x <= 0 or overlap_z <= 0:
            return False

        if overlap_x < overlap_z:
            if self.center[0] < (wall.min_x + wall.max_x) / 2:
                self.owner.position[0] -= overlap_x
            else:
                self.owner.position[0] += overlap_x
        else:
            if self.center[2] < (wall.min_z + wall.max_z) / 2:
                self.owner.position[2] -= overlap_z
            else:
                self.owner.position[2] += overlap_z

        return True

    # =========================================================
    # DEBUG DRAW
    # =========================================================

    def draw_debug(self, screen, camera, projection):
        """วาดกล่อง hitbox บนหน้าจอ (2D projection ของ 8 มุมกล่อง)"""
        if not self.debug:   # ✅ ไม่ทำงานถ้า debug = False
            return
        corners = [
            [self.min_x, self.min_y, self.min_z, 1],
            [self.max_x, self.min_y, self.min_z, 1],
            [self.max_x, self.min_y, self.max_z, 1],
            [self.min_x, self.min_y, self.max_z, 1],
            [self.min_x, self.max_y, self.min_z, 1],
            [self.max_x, self.max_y, self.min_z, 1],
            [self.max_x, self.max_y, self.max_z, 1],
            [self.min_x, self.max_y, self.max_z, 1],
        ]

        edges = [
            (0,1),(1,2),(2,3),(3,0),  # ล่าง
            (4,5),(5,6),(6,7),(7,4),  # บน
            (0,4),(1,5),(2,6),(3,7),  # เสาตั้ง
        ]

        verts = np.array(corners, dtype=float)
        cam_v = verts @ camera.camera_matrix()

        proj_v = cam_v @ projection.projection_matrix
        w = proj_v[:, 3:4]
        w = np.where(np.abs(w) < 1e-6, 1e-6, w)
        proj_v = proj_v / w
        proj_v = proj_v @ projection.to_screen_matrix
        screen_pts = proj_v[:, :2]

        for a, b in edges:
            if cam_v[a, 2] < 0.1 or cam_v[b, 2] < 0.1:
                continue
            pg.draw.line(screen, (0, 255, 0),
                         screen_pts[a].astype(int),
                         screen_pts[b].astype(int), 1)
