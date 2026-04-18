import pygame as pg
import json
import os

SAVE_FILE   = 'save.json'
TOTAL_LEVELS = 10


def load_save():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {'unlocked': 1}


def unlock_next_level(current_level):
    data = load_save()
    if current_level >= data['unlocked'] and current_level < TOTAL_LEVELS:
        data['unlocked'] = current_level + 1
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)


# ──────────────────────────────────────────────────────────────
# Internal helper
# ──────────────────────────────────────────────────────────────

class _Btn:
    def __init__(self, rect, text, font,
                 color=(55, 85, 140), hover=(80, 130, 200),
                 text_color=(255, 255, 255)):
        self.rect       = pg.Rect(rect)
        self.text       = text
        self.font       = font
        self.color      = color
        self.hover      = hover
        self.text_color = text_color

    def draw(self, screen):
        col = self.hover if self.rect.collidepoint(pg.mouse.get_pos()) else self.color
        pg.draw.rect(screen, col, self.rect, border_radius=8)
        pg.draw.rect(screen, (180, 180, 180), self.rect, 2, border_radius=8)
        surf = self.font.render(self.text, True, self.text_color)
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (event.type == pg.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))


def _gradient_bg(W, H):
    surf = pg.Surface((W, H))
    for y in range(H):
        t = y / H
        pg.draw.line(surf, (int(10+15*t), int(12+20*t), int(38+28*t)), (0, y), (W, y))
    return surf


# ──────────────────────────────────────────────────────────────
# Main Menu
# ──────────────────────────────────────────────────────────────

class MainMenu:
    def __init__(self, screen, W, H):
        self.screen = screen
        self.W, self.H = W, H
        tf = pg.font.SysFont('Arial', 52, bold=True)
        bf = pg.font.SysFont('Arial', 26, bold=True)
        cx   = W // 2
        bw, bh, gap = 200, 50, 16
        sy = H // 2 - (3*bh + 2*gap) // 2 + 50
        self._btns = [
            _Btn((cx-bw//2, sy,            bw, bh), 'Play',     bf, (45,95,155), (75,135,210)),
            _Btn((cx-bw//2, sy+bh+gap,     bw, bh), 'Settings', bf, (55,65,85),  (85,100,130)),
            _Btn((cx-bw//2, sy+2*(bh+gap), bw, bh), 'Exit',     bf, (105,38,38), (165,55,55)),
        ]
        self._actions = ['play', 'settings', 'exit']
        self._title_surf   = tf.render('Tower Defense', True, (255, 220, 80))
        self._title_shadow = tf.render('Tower Defense', True, (0, 0, 0))
        self._bg = _gradient_bg(W, H)

    def handle_event(self, event):
        for btn, action in zip(self._btns, self._actions):
            if btn.clicked(event):
                return action
        return None

    def draw(self):
        self.screen.blit(self._bg, (0, 0))
        tx = self.W // 2 - self._title_surf.get_width() // 2
        ty = self.H // 4 - self._title_surf.get_height() // 2
        self.screen.blit(self._title_shadow, (tx+3, ty+3))
        self.screen.blit(self._title_surf,   (tx,   ty))
        for btn in self._btns:
            btn.draw(self.screen)


# ──────────────────────────────────────────────────────────────
# Level Select
# ──────────────────────────────────────────────────────────────

class LevelSelectScreen:
    def __init__(self, screen, W, H):
        self.screen = screen
        self.W, self.H = W, H
        self._tf  = pg.font.SysFont('Arial', 36, bold=True)
        self._lf  = pg.font.SysFont('Arial', 19, bold=True)
        self._lkf = pg.font.SysFont('Arial', 14)
        bf = pg.font.SysFont('Arial', 20, bold=True)
        self.btn_back = _Btn((20, 20, 110, 38), '< Back', bf, (50,50,60),(80,80,100))
        self._bg = _gradient_bg(W, H)
        self._rects = self._build_rects()

    def _build_rects(self):
        cols = 5
        bw, bh, gx, gy = 120, 80, 16, 16
        total_w = cols*(bw+gx) - gx
        total_h = 2*(bh+gy) - gy
        sx = self.W//2 - total_w//2
        sy = self.H//2 - total_h//2 + 25
        rects = []
        for i in range(TOTAL_LEVELS):
            r, c = divmod(i, cols)
            rects.append(pg.Rect(sx + c*(bw+gx), sy + r*(bh+gy), bw, bh))
        return rects

    def handle_event(self, event, unlocked):
        if self.btn_back.clicked(event):
            return 'back'
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._rects):
                if rect.collidepoint(event.pos) and i+1 <= unlocked:
                    return i+1
        return None

    def draw(self, unlocked):
        self.screen.blit(self._bg, (0, 0))
        title = self._tf.render('Select Level', True, (255, 220, 80))
        self.screen.blit(title, (self.W//2 - title.get_width()//2, 15))
        mp = pg.mouse.get_pos()
        for i, rect in enumerate(self._rects):
            lvl = i + 1
            ok  = lvl <= unlocked
            hov = ok and rect.collidepoint(mp)
            col    = (80,130,190) if hov else ((55,85,140) if ok else (32,32,42))
            border = (220,220,220) if ok else (65,65,75)
            pg.draw.rect(self.screen, col,    rect, border_radius=10)
            pg.draw.rect(self.screen, border, rect, 2, border_radius=10)
            if ok:
                t = self._lf.render(f'Level {lvl}', True, (255, 255, 255))
                self.screen.blit(t, t.get_rect(center=rect.center))
            else:
                t    = self._lf.render(f'Level {lvl}', True, (65, 65, 75))
                lock = self._lkf.render('Locked', True, (65, 65, 75))
                self.screen.blit(t,    t.get_rect(centerx=rect.centerx, centery=rect.centery-12))
                self.screen.blit(lock, lock.get_rect(centerx=rect.centerx, centery=rect.centery+13))
        self.btn_back.draw(self.screen)


# ──────────────────────────────────────────────────────────────
# Settings (placeholder)
# ──────────────────────────────────────────────────────────────

class SettingsScreen:
    def __init__(self, screen, W, H):
        self.screen = screen
        self.W, self.H = W, H
        self._tf  = pg.font.SysFont('Arial', 36, bold=True)
        self._inf = pg.font.SysFont('Arial', 22)
        bf = pg.font.SysFont('Arial', 20, bold=True)
        self.btn_back = _Btn((20, 20, 110, 38), '< Back', bf, (50,50,60),(80,80,100))
        self._bg = _gradient_bg(W, H)

    def handle_event(self, event):
        if self.btn_back.clicked(event):
            return 'back'
        return None

    def draw(self):
        self.screen.blit(self._bg, (0, 0))
        title = self._tf.render('Settings', True, (255, 220, 80))
        self.screen.blit(title, (self.W//2 - title.get_width()//2, 15))
        msg = self._inf.render('(Coming soon)', True, (150, 150, 150))
        self.screen.blit(msg, (self.W//2 - msg.get_width()//2, self.H//2 - 15))
        self.btn_back.draw(self.screen)
