import pygame as pg
import json
import os

SAVE_DIR      = 'save'
PROGRESS_FILE = 'save/progress.json'
SETTINGS_FILE = 'save/settings.json'
TOTAL_LEVELS  = 10

_DEFAULT_SETTINGS = {
    'music_vol': 0.7,
    'sfx_vol':   1.0,
    'fullscreen': False,
}


def _ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def load_save():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {'unlocked': 1}


def save_progress(data):
    _ensure_save_dir()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def unlock_next_level(current_level):
    data = load_save()
    if current_level >= data['unlocked'] and current_level < TOTAL_LEVELS:
        data['unlocked'] = current_level + 1
        save_progress(data)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                s = json.load(f)
                return {**_DEFAULT_SETTINGS, **s}
        except Exception:
            pass
    return dict(_DEFAULT_SETTINGS)


def save_settings(settings):
    _ensure_save_dir()
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


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
        sy = H // 2 - (4*bh + 3*gap) // 2 + 50
        self._btns = [
            _Btn((cx-bw//2, sy,            bw, bh), 'Play',     bf, (45,95,155),  (75,135,210)),
            _Btn((cx-bw//2, sy+bh+gap,     bw, bh), 'Tutorial', bf, (40,110,80),  (60,160,110)),
            _Btn((cx-bw//2, sy+2*(bh+gap), bw, bh), 'Settings', bf, (55,65,85),   (85,100,130)),
            _Btn((cx-bw//2, sy+3*(bh+gap), bw, bh), 'Exit',     bf, (105,38,38),  (165,55,55)),
        ]
        self._actions = ['play', 'tutorial', 'settings', 'exit']
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
# Tutorial
# ──────────────────────────────────────────────────────────────

class TutorialScreen:
    IMG_DIR = 'image/tutorial'

    def __init__(self, screen, W, H):
        self.screen = screen
        self.W, self.H = W, H
        self._index  = 0
        self._images = []
        self._bg     = _gradient_bg(W, H)
        bf = pg.font.SysFont('Arial', 20, bold=True)
        sf = pg.font.SysFont('Arial', 16)
        self._font_page = sf
        self.btn_back  = _Btn((20,  20, 110, 38), '< Back', bf, (50,50,60), (80,80,100))
        self.btn_prev  = _Btn((20,  H//2-19, 44, 38), '<',    bf, (50,70,50), (80,120,80))
        self.btn_next  = _Btn((W-64, H//2-19, 44, 38), '>',   bf, (50,70,50), (80,120,80))
        self._load_images()

    def _load_images(self):
        self._images = []
        try:
            files = sorted(
                [f for f in os.listdir(self.IMG_DIR)
                 if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
                key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x
            )
            for fname in files:
                try:
                    img = pg.image.load(os.path.join(self.IMG_DIR, fname)).convert()
                    self._images.append(img)
                except Exception as e:
                    print(f'[Tutorial] load failed {fname}: {e}')
        except FileNotFoundError:
            print('[Tutorial] tutorial folder not found')

    def _scaled(self):
        if not self._images:
            return None
        img = self._images[self._index]
        iw, ih = img.get_size()
        max_w = self.W - 120
        max_h = self.H - 100
        scale = min(max_w / iw, max_h / ih, 1.0)
        nw, nh = int(iw * scale), int(ih * scale)
        return pg.transform.smoothscale(img, (nw, nh))

    def handle_event(self, event):
        if self.btn_back.clicked(event):
            self._index = 0
            return 'back'
        if self._images:
            if self.btn_prev.clicked(event):
                self._index = (self._index - 1) % len(self._images)
            if self.btn_next.clicked(event):
                self._index = (self._index + 1) % len(self._images)
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_LEFT, pg.K_a):
                    self._index = (self._index - 1) % len(self._images)
                if event.key in (pg.K_RIGHT, pg.K_d):
                    self._index = (self._index + 1) % len(self._images)
        return None

    def draw(self):
        self.screen.blit(self._bg, (0, 0))
        surf = self._scaled()
        if surf:
            x = self.W // 2 - surf.get_width() // 2
            y = self.H // 2 - surf.get_height() // 2 + 10
            self.screen.blit(surf, (x, y))
            page = self._font_page.render(
                f'{self._index + 1} / {len(self._images)}', True, (200, 200, 200))
            self.screen.blit(page, (self.W // 2 - page.get_width() // 2, self.H - 28))
        else:
            msg = self._font_page.render('No tutorial images found', True, (180, 80, 80))
            self.screen.blit(msg, (self.W // 2 - msg.get_width() // 2, self.H // 2))
        self.btn_back.draw(self.screen)
        self.btn_prev.draw(self.screen)
        self.btn_next.draw(self.screen)


# ──────────────────────────────────────────────────────────────
# Level Select
# ──────────────────────────────────────────────────────────────

BOSS_LEVELS = {5, 10}

class LevelSelectScreen:
    def __init__(self, screen, W, H):
        self.screen = screen
        self.W, self.H = W, H
        self._tf  = pg.font.SysFont('Arial', 36, bold=True)
        self._lf  = pg.font.SysFont('Arial', 19, bold=True)
        self._lkf = pg.font.SysFont('Arial', 14)
        self._bf  = pg.font.SysFont('Arial', 12, bold=True)
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
            lvl    = i + 1
            ok     = lvl <= unlocked
            hov    = ok and rect.collidepoint(mp)
            is_boss = lvl in BOSS_LEVELS

            if is_boss:
                col    = (160, 60, 60) if hov else ((110, 30, 30) if ok else (32,32,42))
                border = (255, 80, 80) if ok else (65, 65, 75)
            else:
                col    = (80,130,190) if hov else ((55,85,140) if ok else (32,32,42))
                border = (220,220,220) if ok else (65,65,75)

            pg.draw.rect(self.screen, col,    rect, border_radius=10)
            pg.draw.rect(self.screen, border, rect, 2, border_radius=10)

            if ok:
                label = f'Level {lvl}'
                tc    = (255, 200, 200) if is_boss else (255, 255, 255)
                t = self._lf.render(label, True, tc)
                if is_boss:
                    tag = self._bf.render('☠ BOSS', True, (255, 80, 80))
                    self.screen.blit(t,   t.get_rect(centerx=rect.centerx, centery=rect.centery - 11))
                    self.screen.blit(tag, tag.get_rect(centerx=rect.centerx, centery=rect.centery + 12))
                else:
                    self.screen.blit(t, t.get_rect(center=rect.center))
            else:
                tc   = (90, 30, 30) if is_boss else (65, 65, 75)
                t    = self._lf.render(f'Level {lvl}', True, tc)
                lock = self._lkf.render('Locked', True, tc)
                self.screen.blit(t,    t.get_rect(centerx=rect.centerx, centery=rect.centery-12))
                self.screen.blit(lock, lock.get_rect(centerx=rect.centerx, centery=rect.centery+13))
        self.btn_back.draw(self.screen)


# ──────────────────────────────────────────────────────────────
# Settings
# ──────────────────────────────────────────────────────────────

class SettingsScreen:
    _ROWS = [
        ('music_vol', 'Music Volume'),
        ('sfx_vol',   'SFX Volume'),
    ]
    _SLIDER_W = 260
    _SLIDER_H = 14

    def __init__(self, screen, W, H, audio=None, on_fullscreen=None):
        self.screen   = screen
        self.W, self.H = W, H
        self._tf  = pg.font.SysFont('Arial', 36, bold=True)
        self._lf  = pg.font.SysFont('Arial', 20, bold=True)
        self._sf  = pg.font.SysFont('Arial', 16)
        bf = pg.font.SysFont('Arial', 20, bold=True)
        self.btn_back = _Btn((20, 20, 110, 38), '< Back', bf, (50,50,60),(80,80,100))
        self._bg      = _gradient_bg(W, H)
        self._settings      = load_settings()
        self._dragging      = None
        self._audio         = audio
        self._on_fullscreen = on_fullscreen

    # ── layout helpers ────────────────────────────────────────

    def _row_y(self, idx):
        return self.H // 2 - 60 + idx * 70

    def _slider_rect(self, idx):
        x = self.W // 2 - self._SLIDER_W // 2
        y = self._row_y(idx) + 28
        return pg.Rect(x, y, self._SLIDER_W, self._SLIDER_H)

    def _toggle_rect(self):
        w, h = 60, 30
        return pg.Rect(self.W // 2 - w // 2, self._row_y(len(self._ROWS)) + 20, w, h)

    # ── event handling ────────────────────────────────────────

    def handle_event(self, event):
        if self.btn_back.clicked(event):
            save_settings(self._settings)
            return 'back'

        # slider drag start
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for i, (key, _) in enumerate(self._ROWS):
                if self._slider_rect(i).collidepoint(event.pos):
                    self._dragging = (i, key)
                    self._set_from_mouse(i, key, event.pos[0])
                    return None
            if self._toggle_rect().collidepoint(event.pos):
                self._settings['fullscreen'] = not self._settings['fullscreen']
                save_settings(self._settings)
                if self._on_fullscreen:
                    self._on_fullscreen(self._settings['fullscreen'])
                return None

        if event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                save_settings(self._settings)
            self._dragging = None

        if event.type == pg.MOUSEMOTION and self._dragging:
            i, key = self._dragging
            self._set_from_mouse(i, key, event.pos[0])

        return None

    def _set_from_mouse(self, idx, key, mx):
        r = self._slider_rect(idx)
        val = (mx - r.x) / r.w
        self._settings[key] = max(0.0, min(1.0, val))
        if self._audio:
            self._audio.set_volumes(
                self._settings.get('music_vol', 0.7),
                self._settings.get('sfx_vol', 1.0),
            )

    # ── draw ──────────────────────────────────────────────────

    def draw(self):
        self.screen.blit(self._bg, (0, 0))
        title = self._tf.render('Settings', True, (255, 220, 80))
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, 15))

        for i, (key, label) in enumerate(self._ROWS):
            y    = self._row_y(i)
            val  = self._settings.get(key, 1.0)
            rect = self._slider_rect(i)

            lbl = self._lf.render(label, True, (220, 220, 220))
            self.screen.blit(lbl, (self.W // 2 - lbl.get_width() // 2, y))

            # track
            pg.draw.rect(self.screen, (60, 60, 80), rect, border_radius=7)
            # fill
            fill = pg.Rect(rect.x, rect.y, int(rect.w * val), rect.h)
            pg.draw.rect(self.screen, (80, 160, 220), fill, border_radius=7)
            # border
            pg.draw.rect(self.screen, (140, 140, 180), rect, 2, border_radius=7)
            # handle
            hx = rect.x + int(rect.w * val)
            pg.draw.circle(self.screen, (220, 220, 255), (hx, rect.centery), 10)
            pg.draw.circle(self.screen, (180, 180, 220), (hx, rect.centery), 10, 2)

            pct = self._sf.render(f'{int(val*100)}%', True, (180, 220, 180))
            self.screen.blit(pct, (rect.right + 10, rect.centery - pct.get_height() // 2))

        # fullscreen toggle
        fy   = self._row_y(len(self._ROWS))
        flbl = self._lf.render('Fullscreen', True, (220, 220, 220))
        self.screen.blit(flbl, (self.W // 2 - flbl.get_width() // 2, fy))
        trect = self._toggle_rect()
        fs_on = self._settings.get('fullscreen', False)
        pg.draw.rect(self.screen, (60, 160, 60) if fs_on else (80, 40, 40), trect, border_radius=15)
        pg.draw.rect(self.screen, (180, 180, 180), trect, 2, border_radius=15)
        knob_x = trect.right - 18 if fs_on else trect.left + 18
        pg.draw.circle(self.screen, (240, 240, 240), (knob_x, trect.centery), 11)
        st = self._sf.render('ON' if fs_on else 'OFF', True, (255,255,255))
        self.screen.blit(st, st.get_rect(center=trect.center))

        hint = self._sf.render('Settings are saved automatically', True, (110, 110, 130))
        self.screen.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 40))

        self.btn_back.draw(self.screen)
