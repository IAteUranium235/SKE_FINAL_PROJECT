import pygame as pg
import math
import numpy as np
from core.camera import *
from core.projection import *
from core.billboard import Billboard
from core.obj_loader import load_obj
from world.map import *
from world.wave_manager import WaveManager
from world.audio_manager import AudioManager
from entities.player import *
from entities.tower import *
from items.inventory import Inventory
from items.wrench import Wrench
from ui.interact_area import InteractArea, InteractManager, open_shop
from ui.hud import *
from ui.menu import (MainMenu, LevelSelectScreen, SettingsScreen,
                     TutorialScreen, load_save, unlock_next_level, load_settings)
from ui.game_renderer import build_sky, draw_ground, draw_gold_hud, draw_base_hp_bar, draw_damage_numbers, flush_pool
from world.stats_recorder import StatsRecorder

BOSS_LEVELS = {5, 10}


# =========================================================
# SOFTWARE RENDERER + GAME LOGIC
# =========================================================

class SoftwareRender:
    WIDTH, HEIGHT = 800, 450
    FPS = 60

    def __init__(self, screen, level=1):
        self.H_WIDTH  = self.WIDTH  // 2
        self.H_HEIGHT = self.HEIGHT // 2
        self.screen   = screen
        self.level    = level
        self.clock    = pg.time.Clock()
        self.polygon_pool  = []
        self._mouse_locked = True
        self._game_result  = None
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)
        self._init_scene()

    # ── scene setup ───────────────────────────────────────────────────

    def _init_scene(self):
        self.camera     = Camera(self, [0, 5, -10])
        self.projection = Projection(self)
        self.player     = Player(self, PLAYER_SPAWN)
        self.player.gold = 150 + self.level * 50
        self.map        = Map(self)
        self.base_png   = Billboard(self, 'image/base.png',
                                    [BASE_POSITION[0], 4, BASE_POSITION[2]], 20, 20)
        self.billboards = [Billboard(self, 'image/shopkeepe.png', [0, 1, -20], width=7, height=7)]
        self.placement_grid = [[None]*6 for _ in range(5)]
        self.enemies    = [[], [], [], [], []]
        self.bosses     = []
        self.damage_numbers = []
        self._passive_timer = 0.0
        self.base_hp        = 300
        self.base_max_hp    = 300
        self._is_boss_level = self.level in BOSS_LEVELS

        self._sky_surface = build_sky(self.WIDTH, self.HEIGHT)
        self._gold_font   = pg.font.SysFont('Arial', 20, bold=True)
        self._hp_font     = pg.font.SysFont('Arial', 16, bold=True)
        self._dmg_font    = pg.font.SysFont('Arial', 17, bold=True)
        self._boss_font   = pg.font.SysFont('Arial', 18, bold=True)

        self.shop_gui        = ShopGUI(self)
        self.pause_menu      = PauseMenu(self)
        self.game_over_screen= GameOverScreen(self)
        self.victory_screen  = VictoryScreen(self)
        self.tower_select_ui = TowerSelectUI(self)
        self.crosshair       = Crosshair(self)

        self.inventory = Inventory(self.player)
        self.inventory.add(1, Wrench(self.player))
        self.inventory.equip(1)

        self.interact = InteractManager()
        self.interact.add(InteractArea(
            position=[0, 0, -16], radius=4.0, key=pg.K_e,
            callback=open_shop(self), label='[E] Open Shop', cooldown=0.5,
        ))

        self.stats = StatsRecorder(self.level)
        self.wave_manager = WaveManager(self, csv_path=f'data/wave_{self.level}.csv')
        self.wave_manager.start()

        settings = load_settings()
        self.audio = AudioManager()
        self.audio.load(music_vol=settings.get('music_vol', 0.7),
                        sfx_vol=settings.get('sfx_vol', 1.0))
        self.audio.on_wave_start(1, self.wave_manager.total_waves, self._is_boss_level)

    def load_obj(self, filename):
        return load_obj(self, filename)

    # ── update ────────────────────────────────────────────────────────

    def update(self):
        raw_dt = self.clock.get_time() / 1000.0
        self.dt = min(raw_dt, 1/30)
        self._update_physics()
        self._update_entities()
        self._update_game_state()
        self._update_passive_income()
        ui_open = (self.shop_gui.is_open or self.game_over_screen.is_open
                   or self.victory_screen.is_open or self.tower_select_ui.any_open)
        if not ui_open:
            self.player.update(self.dt)
            self.inventory.update(self.dt)
            self.interact.update(self.player, self.dt)
        self._update_camera()

    def _update_physics(self):
        self.player.is_grounded = False
        self.player._prev_y     = self.player.position[1]
        self.player.velocity_y += self.player.gravity * self.dt * 60
        self.player.velocity_y  = max(self.player.velocity_y, -1.0)
        self.player.position[1]+= self.player.velocity_y * self.dt * 60
        if self.player.position[1] - 1.5 <= 0.15 and self.player.velocity_y <= 0:
            self.player.position[1] = 1.5
            self.player.velocity_y  = 0
            self.player.is_grounded = True

    def _update_entities(self):
        for row in self.placement_grid:
            for t in row:
                if t: t.update(self.dt)
        for row in self.enemies:
            for e in row:
                e.update(self.dt)
        for boss in list(self.bosses):
            boss.update(self.dt)
        self.shop_gui.update(self.dt)
        self.tower_select_ui.update(self.dt)
        self.wave_manager.update(self.dt)

    def _update_game_state(self):
        if self.base_hp <= 0 and not self.game_over_screen.is_open:
            self.stats.save_and_show()
            self.game_over_screen.open()
        if self.wave_manager.finished and not self.victory_screen.is_open:
            self.stats.save_and_show()
            self.victory_screen.open()
            self.audio.play_win()

    def _update_passive_income(self):
        self._passive_timer += self.dt
        if self._passive_timer >= 10.0:
            self._passive_timer -= 10.0
            self.player.gold += 15
            self.damage_numbers.append({
                'x': self.player.position[0], 'y': self.player.position[1] + 3.0,
                'z': self.player.position[2], 'value': 15,
                'timer': 1.5, 'max_timer': 1.5, 'gold': True,
            })
            self.stats.record_currency('earn_passive', 15, self.wave_manager.current_wave)

    def _update_camera(self):
        d   = 8
        ang = self.player.angle_y
        cx  = self.player.position[0] - math.sin(ang) * d
        cy  = self.player.position[1] + 3
        cz  = self.player.position[2] - math.cos(ang) * d
        dx, dz = self.player.position[0]-cx, self.player.position[2]-cz
        self.camera.position = np.array([cx, cy, cz, 1.0])
        self.camera.yaw   = math.atan2(dx, dz)
        dy = (self.player.position[1] + 1.0) - cy
        pitch = -math.atan2(dy, math.sqrt(dx**2+dz**2))
        self.camera.pitch = max(-math.pi/4, min(math.pi/4, pitch))
        self.camera.update_vectors()

    # ── draw ──────────────────────────────────────────────────────────

    def draw(self):
        self.screen.blit(self._sky_surface, (0, 0))
        self.polygon_pool.clear()
        self.update()

        draw_ground(self)
        self.map.draw()
        flush_pool(self)

        self.polygon_pool.clear()
        for row in self.enemies:
            for e in row: e.push_to_pool()
        for boss in self.bosses:
            boss.push_to_pool()
        for row in self.placement_grid:
            for t in row:
                if t: t.draw()
        flush_pool(self)

        self.polygon_pool.clear()
        self.base_png.draw()
        self.player.draw()
        item = self.inventory.current
        if hasattr(item, 'draw'): item.draw()
        for b in self.billboards: b.draw()
        flush_pool(self)

        draw_damage_numbers(self, self._dmg_font)
        self.inventory.draw_hud(self.screen)
        self.interact.draw_hud(self.screen)
        self.crosshair.draw()
        draw_base_hp_bar(self, self._hp_font)
        draw_gold_hud(self, self._gold_font)
        self.wave_manager.draw_hud(self.screen)
        for boss in self.bosses:
            boss.draw_boss_hud(self.screen, self._boss_font)
        if self.pause_menu.is_open:
            self.pause_menu.draw()
        self.shop_gui.draw()
        self.tower_select_ui.draw()
        self.game_over_screen.draw()
        self.victory_screen.draw()

    # ── game loop ─────────────────────────────────────────────────────

    def _set_mouse_lock(self, locked):
        self._mouse_locked = locked
        pg.mouse.set_visible(not locked)
        pg.event.set_grab(locked)

    def run(self):
        while self._game_result is None:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit(); exit()
                was_open = self.tower_select_ui.any_open
                self.tower_select_ui.handle_event(event)
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    if not was_open: self.pause_menu.toggle()
                if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                    self._set_mouse_lock(not self._mouse_locked)
                if (event.type == pg.MOUSEBUTTONDOWN and event.button == 1
                        and not was_open
                        and not self.tower_select_ui._click_consumed
                        and not self.shop_gui.is_open
                        and not self.pause_menu.is_open):
                    item = self.inventory.current
                    if hasattr(item, 'handle_click'): item.handle_click()
                self.audio.handle_event(event)
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
# APP — state machine for menus
# =========================================================

class App:
    W, H = 800, 450

    def __init__(self):
        pg.init()
        pg.mixer.init()
        pg.display.set_caption('Tower Defence 3D')
        try:
            icon = pg.image.load('image/game_Icon.png')
            pg.display.set_icon(icon)
        except Exception:
            pass
        settings = load_settings()
        flags = (pg.FULLSCREEN | pg.SCALED) if settings.get('fullscreen', False) else pg.SCALED
        self.screen = pg.display.set_mode((self.W, self.H), flags)
        self.clock  = pg.time.Clock()
        self.state  = 'menu'
        self.selected_level = 1

        self.main_menu    = MainMenu(self.screen, self.W, self.H)
        self.level_select = LevelSelectScreen(self.screen, self.W, self.H)
        self.settings_scr = SettingsScreen(self.screen, self.W, self.H,
                                           on_fullscreen=self._apply_fullscreen)
        self.tutorial_scr = TutorialScreen(self.screen, self.W, self.H)

        self.audio = AudioManager()
        self.audio.load(music_vol=settings.get('music_vol', 0.7),
                        sfx_vol=settings.get('sfx_vol', 1.0))
        self.audio.play_menu()
        self.settings_scr._audio = self.audio

    def _apply_fullscreen(self, enabled):
        flags = (pg.FULLSCREEN | pg.SCALED) if enabled else pg.SCALED
        self.screen = pg.display.set_mode((self.W, self.H), flags)

    def run(self):
        while True:
            self.clock.tick(60)
            events = pg.event.get()
            for e in events:
                if e.type == pg.QUIT:
                    pg.quit(); exit()
                self.audio.handle_event(e)
            {
                'menu':         self._state_menu,
                'level_select': self._state_level_select,
                'settings':     self._state_settings,
                'tutorial':     self._state_tutorial,
                'playing':      lambda _: self._state_playing(),
            }[self.state](events)
            pg.display.flip()

    def _state_menu(self, events):
        self.main_menu.draw()
        for e in events:
            action = self.main_menu.handle_event(e)
            if   action == 'play':     self.state = 'level_select'
            elif action == 'tutorial': self.state = 'tutorial'
            elif action == 'settings': self.state = 'settings'
            elif action == 'exit':     pg.quit(); exit()

    def _state_level_select(self, events):
        save = load_save()
        self.level_select.draw(save['unlocked'])
        for e in events:
            result = self.level_select.handle_event(e, save['unlocked'])
            if result == 'back':          self.state = 'menu'
            elif isinstance(result, int): self.selected_level = result; self.state = 'playing'

    def _state_settings(self, events):
        self.settings_scr.draw()
        for e in events:
            if self.settings_scr.handle_event(e) == 'back':
                self.state = 'menu'

    def _state_tutorial(self, events):
        self.tutorial_scr.draw()
        for e in events:
            if self.tutorial_scr.handle_event(e) == 'back':
                self.state = 'menu'

    def _state_playing(self):
        self.audio.stop()
        game = SoftwareRender(self.screen, self.selected_level)
        result = game.run()
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)
        if result == 'victory':
            unlock_next_level(self.selected_level)
        self.state = 'level_select'
        self.audio.play_menu()


if __name__ == '__main__':
    App().run()
