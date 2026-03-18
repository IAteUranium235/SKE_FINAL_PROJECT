import numpy as np
import pygame as pg
from object_3d import Object3D
from matrix_function import translate


class Ground:
    def __init__(self, render, position, width=5.0, depth=5.0, thick=0.5, color=None):
        self.render   = render
        self.position = np.array(position, dtype=float)
        self.width    = width
        self.depth    = depth
        self.thick    = thick
        self.color    = color or pg.Color('peru')

        self.min_x = self.position[0] - self.width / 2
        self.max_x = self.position[0] + self.width / 2
        self.min_y = self.position[1] - self.thick
        self.max_y = self.position[1]
        self.min_z = self.position[2] - self.depth / 2
        self.max_z = self.position[2] + self.depth / 2

        self._mesh = self._build_mesh()

    def _build_mesh(self):
        x, y, z = self.position
        hw, hd = self.width / 2, self.depth / 2

        vertexes = [
            [-hw, 0, -hd, 1],
            [ hw, 0, -hd, 1],
            [ hw, 0,  hd, 1],
            [-hw, 0,  hd, 1],
        ]
        # ✅ แค่ 2 face — double_sided จะวาดได้จากทุกมุมโดยไม่ต้องซ้ำ face
        faces = [
            [0, 2, 1],
            [0, 3, 2],
        ]
        color_faces = [(self.color, face) for face in faces]
        obj = Object3D(self.render, vertexes, faces, color_faces)
        obj.matrix = translate([x, y, z])
        obj.skip_frustum_check = True  # ground ไม่ต้องเช็ค frustum
        obj.double_sided = True        # ✅ วาดได้จากทุกมุม ไม่ถูก cull
        return obj

    def resolve_player(self, player, hitbox):
        if (hitbox.min_x > self.max_x or hitbox.max_x < self.min_x or
                hitbox.min_z > self.max_z or hitbox.max_z < self.min_z):
            return False

        feet_offset = 1.5
        feet_y    = player.position[1] - feet_offset
        prev_feet = getattr(player, '_prev_y', feet_y + 0.1) - feet_offset

        if prev_feet >= self.max_y and feet_y <= self.max_y:
            if player.velocity_y <= 0:
                player.position[1] = self.max_y + feet_offset
                player.velocity_y  = 0
                player.is_grounded = True
                return True

        if feet_y <= self.max_y + 0.15 and feet_y >= self.max_y - 0.15 and player.velocity_y <= 0:
            player.position[1] = self.max_y + feet_offset
            player.velocity_y  = 0
            player.is_grounded = True
            return True

        return False

    def draw(self):
        self._mesh.draw()


def generate_parkour(render, start=(0, 0, 0)):
    import random
    rng = random.Random(42)

    grounds = []
    colors  = [pg.Color('peru'), pg.Color('sienna'), pg.Color('tan'),
               pg.Color('burlywood'), pg.Color('saddlebrown')]

    grounds.append(Ground(render, position=start, width=8, depth=8, color=pg.Color('peru')))

    x, y, z = start
    for i in range(20):
        gap_z = rng.uniform(2.0, 4.5)
        gap_x = rng.uniform(-3.0, 3.0)
        gap_y = rng.uniform(-0.5, 2.0)
        x += gap_x
        y += gap_y
        z += gap_z + 3
        w = max(1.5, 4.0 - i * 0.1)
        d = max(1.5, 4.0 - i * 0.1)
        grounds.append(Ground(render, position=(x, y, z), width=w, depth=d, color=colors[i % len(colors)]))

    spawn = np.array([start[0], start[1] + 3.0, start[2], 1.0])
    return grounds, spawn
