import pygame as pg
import math
import os
from core.object_3d import *
from core.camera import *
from core.projection import *
from core.billboard import Billboard
from world.wall import *
from world.ground import *
from world.map import *
from world.wave_manager import WaveManager
from entities.player import *
from entities.enemy import *
from entities.tower import *
from items.inventory import Inventory
from items.wrench import Wrench
from ui.interact_area import InteractArea, InteractManager, open_shop
from ui.hud import *
from ui.hud import GameOverScreen, TowerSelectUI, VictoryScreen
from ui.menu import MainMenu, LevelSelectScreen, SettingsScreen, load_save, unlock_next_level

class SoftwareRender:
    def __init__(self, screen, level=1):
        self.RES = self.WIDTH, self.HEIGHT = 800, 450
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.FPS = 60
        self.screen = screen
        self.level  = level
        self.clock = pg.time.Clock()
        self.polygon_pool = []
        self._mouse_locked = True
        self._game_result  = None
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)
        self.create_objects()

    def create_objects(self):
        self.camera     = Camera(self, [0, 5, -10])
        self.projection = Projection(self)
        self.player     = Player(self, PLAYER_SPAWN)
        self.player.gold = 150 + self.level * 50   # level 1→200, level 10→650
        self.base_png = Billboard(self, 'image/base.png',[BASE_POSITION[0],4,BASE_POSITION[2]],20,20)
        self.map        = Map(self)
        #tower1 = Tower(self,filepath='resource/Turret.obj', col=2, row=2)
        self.placement_grid = [
            [None, None, None, None, None, None],
            [None, None, None, None, None, None],
            [None, None, None, None, None, None],
            [None, None, None, None, None, None],
            [None, None, None, None, None, None]
            ]
        #for i in range(len(self.placement_grid)):
        #    for j in range(len(self.placement_grid[i])):
        #        self.placement_grid[i][j] = Tower(self,filepath='resource/Turret.obj', col=j, row=i,damage=5,fire_rate=5)
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
        self.enemies = [[], [], [], [], []]
        #for i in range(len(self.enemies)):
        #    for j in range(15):
        #        self.enemies[i].append(
        #            Enemy(self, position=[SPAWN_POSITION[0], 0, 0], waypoints=[[BASE_POSITION[0], 0, 0]],
        #        hp=100, walk_speed=0.02 + j/1000, damage=1, reward=20
        #        ,image_path="image/boss.png",width=6,height=6,lane=i)
        #        )
                
        # self.billboards.append(Billboard(self, "cat.jpg", [0, 1, 0]))
        self.billboards.append(Billboard(self, "image/shopkeepe.png", [0, 1, -20], width=7, height=7))
        self._sky_surface = self._build_sky_surface()

        self.shop_gui   = ShopGUI(self)

        self.interact   = InteractManager()
        self.interact.add(InteractArea(
            position=[0, 0, -16],
            radius=4.0,
            key=pg.K_e,
            callback=open_shop(self),
            label='[E] Open Shop',
            cooldown=0.5,
        ))

        self.inventory  = Inventory(self.player)
        self.inventory.add(1, Wrench(self.player))
        self.inventory.equip(1)
        self.crosshair       = Crosshair(self)
        self.pause_menu      = PauseMenu(self)
        self.damage_numbers   = []
        self._passive_timer   = 0.0
        self.bosses           = []
        self._boss_font       = pg.font.SysFont('Arial', 18, bold=True)
        self.base_hp          = 300
        self.base_max_hp      = 300
        self.game_over_screen = GameOverScreen(self)
        self.victory_screen   = VictoryScreen(self)
        self.tower_select_ui  = TowerSelectUI(self)
        _wave_csv = f'data/wave_{self.level}.csv'
        self.wave_manager     = WaveManager(self, csv_path=_wave_csv)
        self.wave_manager.start()

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
        for boss in list(self.bosses):
            boss.update(self.dt)
            
        # ground collision y=0
        feet_y = self.player.position[1] - 1.5
        if feet_y <= 0.15 and self.player.velocity_y <= 0:
            self.player.position[1] = 1.5
            self.player.velocity_y  = 0
            self.player.is_grounded = True

        if self.base_hp <= 0 and not self.game_over_screen.is_open:
            self.game_over_screen.open()
        if self.wave_manager.finished and not self.victory_screen.is_open:
            self.victory_screen.open()

        self.shop_gui.update(self.dt)
        self.tower_select_ui.update(self.dt)
        self.wave_manager.update(self.dt)

        self._passive_timer += self.dt
        if self._passive_timer >= 10.0:
            self._passive_timer -= 10.0
            self.player.gold += 15
            self.damage_numbers.append({
                'x': self.player.position[0],
                'y': self.player.position[1] + 3.0,
                'z': self.player.position[2],
                'value': 15, 'timer': 1.5, 'max_timer': 1.5,
                'gold': True,
            })
        _ui_open = (self.shop_gui.is_open or self.game_over_screen.is_open
                    or self.victory_screen.is_open
                    or self.tower_select_ui.any_open)
        if not _ui_open:
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

        self._draw_flat_ground()         
        self.map.draw()                  
        

        #for turret in self.testlag:
        #    turret.draw()
                  
                      
        self._flush_pool()             
        self.polygon_pool.clear()
        for row in self.enemies:
            for e in row:
                e.push_to_pool()
        for boss in self.bosses:
            boss.push_to_pool()
        for row in self.placement_grid:
            for turret in row:
                if turret:
                    turret.draw()  
        self._flush_pool()            
        self.polygon_pool.clear()
        self.base_png.draw()
        self.player.draw()
        item = self.inventory.current
        if hasattr(item, 'draw'):
            item.draw() 
                         
        for b in self.billboards:
            b.draw()  
        self._flush_pool()               
        
        self._draw_damage_numbers()
        self.inventory.draw_hud(self.screen)
        self.interact.draw_hud(self.screen)
        self.crosshair.draw()
        self._draw_base_hp_bar()
        self._draw_gold_hud()
        self.wave_manager.draw_hud(self.screen)
        for boss in self.bosses:
            boss.draw_boss_hud(self.screen, self._boss_font)
        if self.pause_menu.is_open:
            self.pause_menu.draw()
        self.shop_gui.draw()
        self.tower_select_ui.draw()
        self.game_over_screen.draw()
        self.victory_screen.draw()

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

    def _draw_gold_hud(self):
        if not hasattr(self, '_gold_font'):
            self._gold_font = pg.font.SysFont('Arial', 20, bold=True)
        text = self._gold_font.render(f'Gold: {self.player.gold}', True, (255, 215, 0))
        shadow = self._gold_font.render(f'Gold: {self.player.gold}', True, (0, 0, 0))
        x = self.WIDTH - text.get_width() - 10
        self.screen.blit(shadow, (x + 1, 11))
        self.screen.blit(text,   (x,     10))

    def _draw_damage_numbers(self):
        if not hasattr(self, '_dmg_font'):
            self._dmg_font = pg.font.SysFont('Arial', 17, bold=True)
        cam_mat  = self.camera.camera_matrix()
        proj_mat = self.projection.projection_matrix
        alive = []
        for dn in self.damage_numbers:
            dn['timer'] -= self.dt
            if dn['timer'] <= 0:
                continue
            alive.append(dn)
            t   = 1.0 - dn['timer'] / dn['max_timer']   # 0→1 ตามเวลาผ่านไป
            wy  = dn['y'] + t * 2.5                      # ลอยขึ้น 2.5 world units
            wp  = np.array([dn['x'], wy, dn['z'], 1.0])
            cp  = wp @ cam_mat
            if cp[2] < 0.1:
                continue
            pp  = cp @ proj_mat
            if abs(pp[3]) < 1e-6:
                continue
            pp /= pp[3]
            sx  = int(pp[0] * self.H_WIDTH  + self.H_WIDTH)
            sy  = int(-pp[1] * self.H_HEIGHT + self.H_HEIGHT)
            if sx < -60 or sx > self.WIDTH + 60 or sy < -30 or sy > self.HEIGHT + 30:
                continue
            alpha = int(255 * (dn['timer'] / dn['max_timer']))
            if dn.get('gold'):
                surf = self._dmg_font.render(f'+{dn["value"]}g', True, (255, 215, 0))
            else:
                surf = self._dmg_font.render(f'-{dn["value"]}', True, (255, 80, 80))
            surf.set_alpha(alpha)
            self.screen.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height() // 2))
        self.damage_numbers = alive

    def _draw_base_hp_bar(self):
        if not hasattr(self, '_hp_font'):
            self._hp_font = pg.font.SysFont('Arial', 16, bold=True)
        bar_w, bar_h = 200, 18
        x, y = 10, 10
        frac = max(0.0, self.base_hp / self.base_max_hp)
        pg.draw.rect(self.screen, (60, 20, 20),  (x, y, bar_w, bar_h))
        r = int(255 * (1 - frac))
        g = int(200 * frac)
        pg.draw.rect(self.screen, (r, g, 0), (x, y, int(bar_w * frac), bar_h))
        pg.draw.rect(self.screen, (200, 200, 200), (x, y, bar_w, bar_h), 2)
        label = self._hp_font.render(f'Base HP  {self.base_hp}/{self.base_max_hp}', True, (255, 255, 255))
        self.screen.blit(label, (x + 4, y + 1))

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
        while self._game_result is None:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()
                _select_was_open = self.tower_select_ui.any_open
                self.tower_select_ui.handle_event(event)
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    if not _select_was_open:
                        self.pause_menu.toggle()
                if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                    self._set_mouse_lock(not self._mouse_locked)
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    if (not self.tower_select_ui.any_open
                            and not self.tower_select_ui._click_consumed
                            and not self.shop_gui.is_open
                            and not self.pause_menu.is_open):
                        item = self.inventory.current
                        if hasattr(item, 'handle_click'):
                            item.handle_click()
                self.inventory.handle_event(event)
                self.pause_menu.handle_event(event)
                self.shop_gui.handle_event(event)
                self.game_over_screen.handle_event(event)
                self.victory_screen.handle_event(event)
            self.draw()
            self.clock.tick(self.FPS)
            pg.display.flip()
        return self._game_result


# =========================================================
# APP — manages menu states and launches the game
# =========================================================

class App:
    def __init__(self):
        pg.init()
        pg.display.set_caption('Tower Defense 3D')
        self.W, self.H = 800, 450
        self.screen = pg.display.set_mode((self.W, self.H))
        self.clock  = pg.time.Clock()
        self.state  = 'menu'
        self.selected_level = 1
        self.main_menu      = MainMenu(self.screen, self.W, self.H)
        self.level_select   = LevelSelectScreen(self.screen, self.W, self.H)
        self.settings_scr   = SettingsScreen(self.screen, self.W, self.H)

    def run(self):
        while True:
            self.clock.tick(60)
            events = pg.event.get()
            for e in events:
                if e.type == pg.QUIT:
                    pg.quit(); exit()

            if self.state == 'menu':
                self._state_menu(events)
            elif self.state == 'level_select':
                self._state_level_select(events)
            elif self.state == 'settings':
                self._state_settings(events)
            elif self.state == 'playing':
                self._state_playing()

            pg.display.flip()

    def _state_menu(self, events):
        self.main_menu.draw()
        for e in events:
            action = self.main_menu.handle_event(e)
            if action == 'play':      self.state = 'level_select'
            elif action == 'settings': self.state = 'settings'
            elif action == 'exit':     pg.quit(); exit()

    def _state_level_select(self, events):
        save = load_save()
        self.level_select.draw(save['unlocked'])
        for e in events:
            result = self.level_select.handle_event(e, save['unlocked'])
            if result == 'back':
                self.state = 'menu'
            elif isinstance(result, int):
                self.selected_level = result
                self.state = 'playing'

    def _state_settings(self, events):
        self.settings_scr.draw()
        for e in events:
            result = self.settings_scr.handle_event(e)
            if result == 'back':
                self.state = 'menu'

    def _state_playing(self):
        game = SoftwareRender(self.screen, self.selected_level)
        result = game.run()
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)
        if result == 'victory':
            unlock_next_level(self.selected_level)
        self.state = 'level_select'


if __name__ == '__main__':
    App().run()