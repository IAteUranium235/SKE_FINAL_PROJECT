import pygame as pg
import math
import os
from object_3d import *
from camera import *
from projection import *
from player import *
from wall import *
from ground import *
from billboard import Billboard
from inventory import Inventory
from weapon import Weapon
from wrench import Wrench
from interact_area import InteractArea, InteractManager, speed_boost
from hud import *
from enemy import *
from map import *
from tower import *

class SoftwareRender:
    def __init__(self):
        pg.init()
        self.RES = self.WIDTH, self.HEIGHT = 800, 450
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.FPS = 60
        self.screen = pg.display.set_mode(self.RES)
        self.clock = pg.time.Clock()
        self.polygon_pool = []
        self._mouse_locked = True
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)
        self.create_objects()

    def create_objects(self):
        self.camera     = Camera(self, [0, 5, -10])
        self.projection = Projection(self)
        self.player     = Player(self, PLAYER_SPAWN)
        
        self.map        = Map(self)
        tower1 = Tower(self,filepath='resource/Turret.obj', col=2, row=2)
        self.placement_grid = [
            [None, None, None, None, None, None],
            [None, None, None, None, None, None],
            [None, None, None, None, None, None],
            [None, None, None, None, None, None],
            [None, None, None, None, None, None]
            ]
        for i in range(len(self.placement_grid)):
            for j in range(len(self.placement_grid[i])):
                self.placement_grid[i][j] = Tower(self,filepath='resource/Turret.obj', col=j, row=i,damage=5,fire_rate=5)
        self.walls      = []
        self.grounds    = []
        self.billboards = []
        # self.boss = Billboard(self, 'image/boss.png', [0, 1, 10], width=6, height=6)
        # self.turret = Tower(self,filepath='resource/Turret.obj', col=2, row=2)
        # self.turret.translate([0, 1, 20])
        """self.testlag = []
        for i in range(30):
            self.testlag.append(self.load_obj('resource/Turret.obj'))
            self.testlag[i].translate([i * 3 % 16, 1, int(i/5) * 3])
            self.testlag[i].double_sided = True
            self.testlag[i].skip_frustum_check = True"""
        #self.turret.double_sided = True
        #self.turret.skip_frustum_check = True
        #self.test1 = self.load_obj()
        #self.test2 = self.load_obj()
        #self.test3 = self.load_obj()
        self.towers = []
        self.enemies = [
            [],
            [],
            [
                Enemy(self, position=[SPAWN_POSITION[0], 0, 0], waypoints=[[BASE_POSITION[0], 0, 0]],
                hp=200, walk_speed=0.04, damage=10, reward=20
                ,image_path="cat.jpg",width=6,height=6,lane=2),
                Enemy(self, position=[SPAWN_POSITION[0], 0, 0], waypoints=[[BASE_POSITION[0], 0, 0]],
                hp=300, walk_speed=0.06, damage=10, reward=20
                ,image_path="image/boss.png",width=6,height=6,lane=2)
                ],
            [Enemy(self, position=[SPAWN_POSITION[0], 0, 0], waypoints=[[BASE_POSITION[0], 0, 0]],
                hp=100, walk_speed=0.08, damage=10, reward=20
                ,image_path="image/boss.png",width=6,height=6,lane=3)],
            []
            
        ]
        for i in range(len(self.enemies)):
            for j in range(15):
                self.enemies[i].append(
                    Enemy(self, position=[SPAWN_POSITION[0], 0, 0], waypoints=[[BASE_POSITION[0], 0, 0]],
                hp=100, walk_speed=0.02 + j/1000, damage=1, reward=20
                ,image_path="image/boss.png",width=6,height=6,lane=i)
                )
                
        # self.billboards.append(Billboard(self, "cat.jpg", [0, 1, 0]))
        self.billboards.append(Billboard(self, "shopkeepe.png", [0, 1, -20], width=7, height=7))
        self._sky_surface = self._build_sky_surface()

        self.interact   = InteractManager()
        self.interact.add(InteractArea(
            position=[0, 0, -16],
            radius=4.0,
            key=pg.K_e,
            callback=speed_boost(amount=0.15, duration=5.0),
            label='[E] Speed Boost (5s)'
        ))

        self.inventory  = Inventory(self.player)
        self.inventory.add(1, Weapon(self.player))
        self.inventory.add(2, Wrench(self.player))
        self.inventory.equip(1)
        self.crosshair  = Crosshair(self)
        self.pause_menu = PauseMenu(self)

    def _build_sky_surface(self):
        top    = (30,  60, 114)
        bottom = (135, 190, 235)
        surf = pg.Surface((self.WIDTH, self.HEIGHT))
        for y in range(self.HEIGHT):
            t = y / self.HEIGHT
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            pg.draw.line(surf, (r, g, b), (0, y), (self.WIDTH, y))
        return surf

    def load_mtl(self, filename):
        materials = {}
        current_mat = None
        try:
            with open(filename) as f:
                for line in f:
                    if line.startswith('newmtl '):
                        current_mat = line.split()[1]
                    elif line.startswith('Kd ') and current_mat:
                        r, g, b = [float(i) for i in line.split()[1:4]]
                        materials[current_mat] = pg.Color(int(r * 255), int(g * 255), int(b * 255))
        except FileNotFoundError:
            print(f"Warning: MTL file '{filename}' not found.")
        return materials

    def load_obj(self, filename):
        vertex, faces, color_faces = [], [], []
        materials = {}
        current_color = pg.Color('white')
        obj_dir = os.path.dirname(filename)
        with open(filename) as f:
            for line in f:
                if line.startswith('mtllib '):
                    mtl_path = os.path.join(obj_dir, line.split()[1])
                    materials = self.load_mtl(mtl_path)
                elif line.startswith('usemtl '):
                    current_color = materials.get(line.split()[1], pg.Color('white'))
                elif line.startswith('v '):
                    vertex.append([float(i) for i in line.split()[1:]] + [1])
                elif line.startswith('f '):
                    indices = [int(f.split('/')[0]) - 1 for f in line.split()[1:]]
                    for i in range(1, len(indices) - 1):
                        face = [indices[0], indices[i], indices[i + 1]]
                        faces.append(face)
                        color_faces.append((current_color, face))
        return Object3D(self, vertex, faces, color_faces)

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self):
        raw_dt = self.clock.get_time() / 1000.0
        self.dt = min(raw_dt, 1/30)

        self.player.is_grounded = False
        self.player._prev_y = self.player.position[1]

        self.player.velocity_y += self.player.gravity * self.dt * 60
        self.player.velocity_y  = max(self.player.velocity_y, -1.0)
        self.player.position[1] += self.player.velocity_y * self.dt * 60

        cam_mat = self.camera.camera_matrix()
        for row in self.placement_grid:
            for turret in row:
                if turret != None:
                    turret.update(self.dt) 
        for row in self.enemies:
            for e in row:
                e.update(self.dt)
            # e.push_to_pool(cam_mat)
            
        # ground collision y=0
        feet_y = self.player.position[1] - 1.5
        if feet_y <= 0.15 and self.player.velocity_y <= 0:
            self.player.position[1] = 1.5
            self.player.velocity_y  = 0
            self.player.is_grounded = True

        self.player.update(self.dt)
        self.inventory.update(self.dt)
        self.interact.update(self.player, self.dt)

        self.update_camera()

    def update_camera(self):
        distance  = 8
        height    = 3
        angle_rad = self.player.angle_y

        cam_x = self.player.position[0] - math.sin(angle_rad) * distance
        cam_y = self.player.position[1] + height
        cam_z = self.player.position[2] - math.cos(angle_rad) * distance

        dx = self.player.position[0] - cam_x
        dz = self.player.position[2] - cam_z
        distance_2d = math.sqrt(dx**2 + dz**2)

        target_y = self.player.position[1] + 1.0
        dy = target_y - cam_y

        self.camera.position = np.array([cam_x, cam_y, cam_z, 1.0])
        self.camera.yaw   = math.atan2(dx, dz)
        pitch = -math.atan2(dy, distance_2d)
        self.camera.pitch = max(-math.pi / 4, min(math.pi / 4, pitch))
        self.camera.update_vectors()

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):
        self.draw_sky()
        self.polygon_pool.clear()
        self.update()

        self._draw_flat_ground()         # พื้น 2D ก่อนสุด
        self.map.draw()                  # map → pool
        

        #for turret in self.testlag:
        #    turret.draw()
                  
                      
        self._flush_pool()               # 1. flush map + turret + billboard
        self.polygon_pool.clear()
        for row in self.enemies:
            for e in row:
                e.push_to_pool()             # enemy → pool แยก
        # self.boss.draw()  
        for row in self.placement_grid:
            for turret in row:
                if turret:
                    turret.draw()
         
        self._flush_pool()               # 2. flush enemy
        self.polygon_pool.clear()
        self.player.draw()               # player → pool แยก
        for b in self.billboards:
            b.draw()  
        self._flush_pool()               # 3. flush player
        self.inventory.draw_hud(self.screen)
        self.interact.draw_hud(self.screen)
        self.crosshair.draw()
        if self.pause_menu.is_open:
            self.pause_menu.draw()

    def _draw_flat_ground(self):
        forward = self.camera.forward[:3]
        screen_ys = []
        for dist in [3, 5, 10, 30, 80]:
            wp = np.array([
                self.camera.position[0] + forward[0] * dist,
                0.0,
                self.camera.position[2] + forward[2] * dist,
                1.0
            ])
            cp = wp @ self.camera.camera_matrix()
            if cp[2] < 0.1:
                continue
            pp = cp @ self.projection.projection_matrix
            if abs(pp[3]) < 1e-6:
                continue
            pp /= pp[3]
            sp = np.array([pp]) @ self.projection.to_screen_matrix
            screen_ys.append(sp[0][1])

        horizon_y = int(max(0, min(self.HEIGHT,
                        min(screen_ys) if screen_ys else self.H_HEIGHT)))
        if horizon_y < self.HEIGHT:
            pg.draw.rect(self.screen, (101, 139, 70),
                         (0, horizon_y, self.WIDTH, self.HEIGHT - horizon_y))

    def _flush_pool(self):
        """flush polygon_pool — รองรับทั้ง polygon และ billboard"""
        self.polygon_pool.sort(key=lambda x: x['depth'], reverse=True)
        for entry in self.polygon_pool:
            if 'billboard' in entry:
                b = entry['billboard']
                self.screen.blit(b['surf'], (b['sx'] - b['w'] // 2, b['sy'] - b['h'] // 2))
            elif len(entry['points']) >= 3:
                pg.draw.polygon(self.screen, entry['color'], entry['points'])

    def draw_sky(self):
        self.screen.blit(self._sky_surface, (0, 0))

    # =========================================================
    # GAME LOOP
    # =========================================================

    def _set_mouse_lock(self, locked):
        self._mouse_locked = locked
        pg.mouse.set_visible(not locked)
        pg.event.set_grab(locked)
 
    def run(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    self.pause_menu.toggle()
                if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                    self._set_mouse_lock(not self._mouse_locked)
                self.inventory.handle_event(event)
                self.pause_menu.handle_event(event)
            self.draw()
            self.clock.tick(self.FPS)
            pg.display.flip()


if __name__ == '__main__':
    app = SoftwareRender()
    app.run()