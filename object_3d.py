import pygame as pg
from matrix_function import *
from numba import njit

@njit(fastmath=True)
def any_func(arr, a, b):
    return np.any((arr == a) | (arr == b))

class Object3D:
    def __init__(self, render, vertexes, faces, color_faces=None):
        self.render = render
        self.vertexes = np.array([np.array(v) for v in vertexes])
        self.faces = np.array([np.array(face) for face in faces])
        self.matrix = np.eye(4)
        self.font = pg.font.SysFont('Arial', 30, bold=True)
        if color_faces:
            self.color_faces = color_faces
        else:
            self.color_faces = [(pg.Color('white'), face) for face in self.faces]
        self.movement_flag, self.draw_vertexes = True, False
        self.label = ''
        self.skip_frustum_check = False
        self.double_sided = False  # ✅ ปิด backface culling สำหรับ ground/plane
        self._cache_bounds()

    def _cache_bounds(self):
        center = np.mean(self.vertexes[:, :3], axis=0)
        self._local_center = np.append(center, 1.0)
        diffs = self.vertexes[:, :3] - center
        self._bounding_radius = np.max(np.linalg.norm(diffs, axis=1))

    def is_in_frustum(self, camera):
        center_world = self._local_center @ self.matrix
        center_cam   = center_world @ camera.camera_matrix()
        if center_cam[2] + self._bounding_radius < camera.near_plane:
            return False
        if center_cam[2] - self._bounding_radius > camera.far_plane:
            return False
        return True

    def draw(self, pool=None):
        if not self.skip_frustum_check:
            if not self.is_in_frustum(self.render.camera):
                return
        self.screen_projection(pool)

    def movement(self):
        if self.movement_flag:
            self.rotate_y(pg.time.get_ticks() % 0.005)

    def screen_projection(self, pool=None):
        if pool is None:
            pool = self.render.polygon_pool

        world_vertexes  = self.vertexes @ self.matrix
        camera_vertexes = world_vertexes @ self.render.camera.camera_matrix()
        vertexes = camera_vertexes @ self.render.projection.projection_matrix

        w = vertexes[:, -1].reshape(-1, 1)
        w = np.where(np.abs(w) < 1e-6, 1e-6, w)
        vertexes = vertexes / w
        vertexes = vertexes @ self.render.projection.to_screen_matrix
        vertexes = vertexes[:, :2]

        faces = np.array([face for _, face in self.color_faces])

        # near plane
        z_vals = camera_vertexes[faces, 2]
        valid  = ~np.any(z_vals < 0.1, axis=1)

        # backface culling — ข้ามถ้า double_sided = True
        polys = vertexes[faces]
        v0, v1, v2 = polys[:, 0], polys[:, 1], polys[:, 2]
        area = (v1[:, 0] - v0[:, 0]) * (v2[:, 1] - v0[:, 1]) - \
               (v1[:, 1] - v0[:, 1]) * (v2[:, 0] - v0[:, 0])
        if not self.double_sided:
            valid &= (area >= 0)

        # off-screen culling
        W, H = self.render.WIDTH, self.render.HEIGHT
        px, py = polys[:, :, 0], polys[:, :, 1]
        offscreen = (np.all(px < 0, axis=1) | np.all(px > W, axis=1) |
                     np.all(py < 0, axis=1) | np.all(py > H, axis=1))
        valid &= ~offscreen

        depths = np.mean(z_vals, axis=1)
        colors = [cf[0] for cf in self.color_faces]

        pool.extend([
            {'depth': depths[i], 'color': colors[i], 'points': polys[i]}
            for i in np.where(valid)[0]
        ])

    def translate(self, pos):
        self.vertexes = self.vertexes @ translate(pos)

    def scale(self, scale_to):
        self.vertexes = self.vertexes @ scale(scale_to)

    def rotate_x(self, angle):
        self.vertexes = self.vertexes @ rotate_x(angle)

    def rotate_y(self, angle):
        self.vertexes = self.vertexes @ rotate_y(angle)

    def rotate_z(self, angle):
        self.vertexes = self.vertexes @ rotate_z(angle)


class Axes(Object3D):
    def __init__(self, render):
        super().__init__(render)
        self.vertexes = np.array([(0, 0, 0, 1), (1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)])
        self.faces = np.array([(0, 1), (0, 2), (0, 3)])
        self.colors = [pg.Color('red'), pg.Color('green'), pg.Color('blue')]
        self.color_faces = [(color, face) for color, face in zip(self.colors, self.faces)]
        self.draw_vertexes = False
        self.label = 'XYZ'
