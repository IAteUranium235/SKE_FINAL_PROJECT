import pygame as pg


class HUD:
    """
    HUD สำหรับแสดงข้อมูล overlay บนหน้าจอ

    ตัวอย่างการใช้งานใน main.py:
        from hud import HUD

        # ใน create_objects()
        self.hud = HUD(self)

        # ใน draw() หลังสุด
        self.hud.draw()
    """

    def __init__(self, render,
                 font_size=18,
                 color=(255, 255, 255),
                 shadow_color=(0, 0, 0),
                 padding=10):
        self.render       = render
        self.color        = color
        self.shadow_color = shadow_color
        self.padding      = padding
        self.font         = pg.font.SysFont('Consolas', font_size, bold=True)
        self._clock_fps   = pg.time.Clock()
        self._fps_display = 0.0
        self._fps_timer   = 0.0

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):
        lines = self._build_lines()
        x = self.padding
        y = self.padding
        for line in lines:
            self._draw_text(line, x, y)
            y += self.font.get_linesize() + 2

    def _build_lines(self):
        player = self.render.player
        px, py, pz = (player.position[0],
                      player.position[1],
                      player.position[2])

        # update fps ทุก 0.3 วินาที ไม่ให้ตัวเลขกระพริบ
        self._fps_timer += getattr(self.render, 'dt', 0.016)
        if self._fps_timer >= 0.3:
            self._fps_display = self.render.clock.get_fps()
            self._fps_timer   = 0.0

        return [
            f'FPS  : {self._fps_display:5.1f}',
            f'X    : {px:7.2f}',
            f'Y    : {py:7.2f}',
            f'Z    : {pz:7.2f}',
        ]

    def _draw_text(self, text, x, y):
        # shadow
        shadow = self.font.render(text, True, self.shadow_color)
        self.render.screen.blit(shadow, (x + 1, y + 1))
        # text
        surf = self.font.render(text, True, self.color)
        self.render.screen.blit(surf, (x, y))


# =========================================================
# CROSSHAIR (optional)
# =========================================================

class Crosshair:
    """
    วาด crosshair กลางจอ

    ตัวอย่าง:
        self.crosshair = Crosshair(self)
        self.crosshair.draw()   # เรียกใน draw() หลังสุด
    """

    def __init__(self, render, size=10, thickness=2,
                 color=(255, 255, 255), gap=4):
        self.render    = render
        self.size      = size
        self.thickness = thickness
        self.color     = color
        self.gap       = gap

    def draw(self):
        cx = self.render.H_WIDTH
        cy = self.render.H_HEIGHT
        s  = self.size
        g  = self.gap
        t  = self.thickness

        # แนวนอน
        pg.draw.line(self.render.screen, self.color,
                     (cx - s - g, cy), (cx - g, cy), t)
        pg.draw.line(self.render.screen, self.color,
                     (cx + g, cy), (cx + s + g, cy), t)
        # แนวตั้ง
        pg.draw.line(self.render.screen, self.color,
                     (cx, cy - s - g), (cx, cy - g), t)
        pg.draw.line(self.render.screen, self.color,
                     (cx, cy + g), (cx, cy + s + g), t)


# =========================================================
# PAUSE MENU
# =========================================================

class PauseMenu:
    """
    Pause menu — เปิดด้วย ESC, มีปุ่ม Resume / Quit
    ค่อยเพิ่ม Settings ทีหลัง

    ใช้งาน:
        self.pause_menu = PauseMenu(self)

        # ใน run() event loop
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self.pause_menu.toggle()

        # ใน draw() หลังสุด
        if self.pause_menu.is_open:
            self.pause_menu.draw()
            self.pause_menu.handle_event(event)  # ใน event loop
    """

    BUTTONS = [
        ('Resume',    'resume'),
        ('Main Menu', 'menu'),
    ]

    def __init__(self, render):
        self.render    = render
        self.is_open   = False
        self._font_title  = pg.font.SysFont('Arial', 36, bold=True)
        self._font_btn    = pg.font.SysFont('Arial', 24, bold=True)
        self._hovered     = None   # index ของปุ่มที่ mouse อยู่

        self._btn_w  = 220
        self._btn_h  = 48
        self._btn_gap = 14

    # =========================================================

    def toggle(self):
        self.is_open = not self.is_open
        self.render._set_mouse_lock(not self.is_open)
        if self.is_open:
            pg.mouse.set_pos(self.render.H_WIDTH, self.render.H_HEIGHT)

    def handle_event(self, event):
        if not self.is_open:
            return
        if event.type == pg.MOUSEMOTION:
            self._hovered = self._get_hovered(event.pos)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._get_hovered(event.pos)
            if idx is not None:
                self._on_click(self.BUTTONS[idx][1])

    def _on_click(self, action):
        if action == 'resume':
            self.toggle()
        elif action == 'menu':
            self.is_open = False
            self.render._set_mouse_lock(False)
            self.render._game_result = 'menu'

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):
        W, H = self.render.WIDTH, self.render.HEIGHT

        # dimmed overlay
        overlay = pg.Surface((W, H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.render.screen.blit(overlay, (0, 0))

        # title
        title = self._font_title.render('PAUSED', True, (255, 255, 255))
        self.render.screen.blit(title, (W//2 - title.get_width()//2, H//2 - 120))

        # buttons
        # pg.mouse.set_pos(self.render.H_WIDTH, self.render.H_HEIGHT)
        mouse_pos = pg.mouse.get_pos()
        self._hovered = self._get_hovered(mouse_pos)
        for i, (label, _) in enumerate(self.BUTTONS):
            self._draw_button(i, label)

    def _btn_rect(self, idx):
        W, H = self.render.WIDTH, self.render.HEIGHT
        total = len(self.BUTTONS) * self._btn_h + (len(self.BUTTONS)-1) * self._btn_gap
        start_y = H//2 - total//2 + 20
        x = W//2 - self._btn_w//2
        y = start_y + idx * (self._btn_h + self._btn_gap)
        return pg.Rect(x, y, self._btn_w, self._btn_h)

    def _get_hovered(self, pos):
        for i in range(len(self.BUTTONS)):
            if self._btn_rect(i).collidepoint(pos):
                return i
        return None

    def _draw_button(self, idx, label):
        rect     = self._btn_rect(idx)
        hovered  = (self._hovered == idx)
        bg_color = (90, 90, 90, 220) if not hovered else (130, 130, 200, 240)
        border   = (200, 200, 200) if not hovered else (255, 255, 255)

        bg = pg.Surface((rect.w, rect.h), pg.SRCALPHA)
        bg.fill(bg_color)
        self.render.screen.blit(bg, rect.topleft)
        pg.draw.rect(self.render.screen, border, rect, 2, border_radius=6)

        text = self._font_btn.render(label, True, (255, 255, 255))
        self.render.screen.blit(text, (
            rect.centerx - text.get_width()//2,
            rect.centery - text.get_height()//2
        ))


# =========================================================
# VICTORY SCREEN
# =========================================================

class VictoryScreen:
    BUTTONS = [('Main Menu', 'menu')]

    def __init__(self, render):
        self.render      = render
        self.is_open     = False
        self._font_title = pg.font.SysFont('Arial', 64, bold=True)
        self._font_btn   = pg.font.SysFont('Arial', 28, bold=True)
        self._btn_w      = 220
        self._btn_h      = 52
        self._btn_gap    = 16
        self._hovered    = None

    def open(self):
        self.is_open = True
        self.render._set_mouse_lock(False)
        pg.mouse.set_pos(self.render.H_WIDTH, self.render.H_HEIGHT)

    def handle_event(self, event):
        if not self.is_open:
            return
        if event.type == pg.MOUSEMOTION:
            self._hovered = self._get_hovered(event.pos)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._get_hovered(event.pos)
            if idx is not None:
                self._on_click(self.BUTTONS[idx][1])

    def _btn_rect(self, idx):
        W, H = self.render.WIDTH, self.render.HEIGHT
        total = len(self.BUTTONS) * self._btn_h + (len(self.BUTTONS) - 1) * self._btn_gap
        x = W // 2 - self._btn_w // 2
        y = H // 2 + 30 + idx * (self._btn_h + self._btn_gap)
        return pg.Rect(x, y, self._btn_w, self._btn_h)

    def _get_hovered(self, pos):
        for i in range(len(self.BUTTONS)):
            if self._btn_rect(i).collidepoint(pos):
                return i
        return None

    def _on_click(self, action):
        if action == 'menu':
            self.render._game_result = 'victory'

    def draw(self):
        if not self.is_open:
            return
        W, H   = self.render.WIDTH, self.render.HEIGHT
        screen = self.render.screen

        overlay = pg.Surface((W, H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        title = self._font_title.render('VICTORY!', True, (255, 215, 0))
        screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 110))

        mouse_pos     = pg.mouse.get_pos()
        self._hovered = self._get_hovered(mouse_pos)
        for i, (label, _) in enumerate(self.BUTTONS):
            rect    = self._btn_rect(i)
            hovered = (self._hovered == i)
            bg = pg.Surface((rect.w, rect.h), pg.SRCALPHA)
            bg.fill((160, 140, 30, 240) if hovered else (100, 90, 20, 220))
            screen.blit(bg, rect.topleft)
            pg.draw.rect(screen, (255, 215, 0) if hovered else (180, 160, 40), rect, 2, border_radius=6)
            text = self._font_btn.render(label, True, (255, 255, 255))
            screen.blit(text, (rect.centerx - text.get_width() // 2,
                                rect.centery - text.get_height() // 2))


# =========================================================
# GAME OVER SCREEN
# =========================================================

class GameOverScreen:
    BUTTONS = [('Restart', 'restart'), ('Main Menu', 'menu')]

    def __init__(self, render):
        self.render      = render
        self.is_open     = False
        self._font_title = pg.font.SysFont('Arial', 64, bold=True)
        self._font_btn   = pg.font.SysFont('Arial', 28, bold=True)
        self._btn_w      = 220
        self._btn_h      = 52
        self._btn_gap    = 16
        self._hovered    = None

    def open(self):
        self.is_open = True
        self.render._set_mouse_lock(False)
        pg.mouse.set_pos(self.render.H_WIDTH, self.render.H_HEIGHT)

    def handle_event(self, event):
        if not self.is_open:
            return
        if event.type == pg.MOUSEMOTION:
            self._hovered = self._get_hovered(event.pos)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._get_hovered(event.pos)
            if idx is not None:
                self._on_click(self.BUTTONS[idx][1])

    def _btn_rect(self, idx):
        W, H = self.render.WIDTH, self.render.HEIGHT
        total = len(self.BUTTONS) * self._btn_h + (len(self.BUTTONS) - 1) * self._btn_gap
        start_y = H // 2 + 30
        x = W // 2 - self._btn_w // 2
        y = start_y + idx * (self._btn_h + self._btn_gap)
        return pg.Rect(x, y, self._btn_w, self._btn_h)

    def _get_hovered(self, pos):
        for i in range(len(self.BUTTONS)):
            if self._btn_rect(i).collidepoint(pos):
                return i
        return None

    def _on_click(self, action):
        if action == 'restart':
            self.is_open = False
            self.render.create_objects()
            self.render._set_mouse_lock(True)
        elif action == 'menu':
            self.render._game_result = 'menu'

    def draw(self):
        if not self.is_open:
            return
        W, H   = self.render.WIDTH, self.render.HEIGHT
        screen = self.render.screen

        overlay = pg.Surface((W, H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        title = self._font_title.render('GAME OVER', True, (220, 40, 40))
        screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 100))

        mouse_pos     = pg.mouse.get_pos()
        self._hovered = self._get_hovered(mouse_pos)
        for i, (label, _) in enumerate(self.BUTTONS):
            rect    = self._btn_rect(i)
            hovered = (self._hovered == i)
            bg = pg.Surface((rect.w, rect.h), pg.SRCALPHA)
            bg.fill((130, 50, 50, 240) if hovered else (80, 30, 30, 220))
            screen.blit(bg, rect.topleft)
            pg.draw.rect(screen, (255, 100, 100) if hovered else (160, 60, 60), rect, 2, border_radius=6)
            text = self._font_btn.render(label, True, (255, 255, 255))
            screen.blit(text, (rect.centerx - text.get_width() // 2,
                                rect.centery - text.get_height() // 2))


# =========================================================
# SHOP GUI
# =========================================================

class ShopGUI:
    def __init__(self, render):
        from entities.tower import get_turret_types
        data = get_turret_types()
        _special_desc = {
            'money_gen':    f'+{10} gold / 5s',
            'back_shooter': 'Shoots behind',
            'barrier':      'No attack | Tank',
            'laser':        'Pierce all in lane',
            'bomb':         'AoE 700 on contact',
            'minigun':      'Rapid fire | Low DMG',
        }
        self.ITEMS = [
            {
                'name':         k,
                'desc':         _special_desc.get(v.get('special',''), f'DMG {v["damage"]} | Rate {v["fire_rate"]}/s'),
                'price':        v['price'],
                'hp':           v['hp'],
                'damage':       v['damage'],
                'fire_rate':    v['fire_rate'],
                'file_path':    v['file_path'],
                'offset':       v['offset'],
                'rotate_y':     v['rotate_y'],
                'special':      v.get('special', ''),
                'unlock_level': v.get('unlock_level', 1),
            }
            for k, v in data.items()
        ]

        self.render      = render
        self.is_open     = False
        self._font_title = pg.font.SysFont('Arial', 32, bold=True)
        self._font_item  = pg.font.SysFont('Arial', 20, bold=True)
        self._font_desc  = pg.font.SysFont('Arial', 16)
        self._font_gold  = pg.font.SysFont('Arial', 22, bold=True)
        self._hovered    = None
        self._msg        = ''
        self._msg_timer  = 0.0
        self._card_w     = 180
        self._card_h     = 150
        self._card_gap   = 20
        self._scroll     = 0
        self._max_vis    = 4

    def _shown_items(self):
        lvl = getattr(self.render, 'level', 1)
        return [item for item in self.ITEMS if item['unlock_level'] <= lvl]

    def toggle(self):
        self.is_open = not self.is_open
        self.render._set_mouse_lock(not self.is_open)
        if self.is_open:
            pg.mouse.set_pos(self.render.H_WIDTH, self.render.H_HEIGHT)

    def handle_event(self, event):
        if not self.is_open:
            return
        if event.type == pg.KEYDOWN and event.key == pg.K_e:
            self.toggle()
            return
        shown = self._shown_items()
        if event.type == pg.MOUSEWHEEL:
            self._scroll = max(0, min(len(shown) - self._max_vis, self._scroll - event.y))
            return
        if event.type == pg.MOUSEMOTION:
            self._hovered = self._get_hovered(event.pos)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            la, ra = self._arrow_rects()
            if la.collidepoint(event.pos):
                self._scroll = max(0, self._scroll - 1)
                return
            if ra.collidepoint(event.pos):
                self._scroll = min(len(shown) - self._max_vis, self._scroll + 1)
                return
            idx = self._get_hovered(event.pos)
            if idx is not None:
                self._buy(idx)

    def _visible_count(self):
        return min(self._max_vis, len(self._shown_items()) - self._scroll)

    def _card_rect(self, vis_idx):
        W, H = self.render.WIDTH, self.render.HEIGHT
        n = self._visible_count()
        total_w = n * self._card_w + (n - 1) * self._card_gap
        x = W // 2 - total_w // 2 + vis_idx * (self._card_w + self._card_gap)
        y = H // 2 - self._card_h // 2 + 20
        return pg.Rect(x, y, self._card_w, self._card_h)

    def _arrow_rects(self):
        W, H = self.render.WIDTH, self.render.HEIGHT
        n = self._visible_count()
        total_w = n * self._card_w + (n - 1) * self._card_gap
        cy = H // 2 + 20
        left  = pg.Rect(W // 2 - total_w // 2 - 36, cy - 16, 28, 32)
        right = pg.Rect(W // 2 + total_w // 2 +  8, cy - 16, 28, 32)
        return left, right

    def _get_hovered(self, pos):
        n = self._visible_count()
        for vi in range(n):
            if self._card_rect(vi).collidepoint(pos):
                return self._scroll + vi
        return None

    def _buy(self, idx):
        item   = self._shown_items()[idx]
        player = self.render.player
        if player.gold < item['price']:
            self._msg       = 'Not enough gold!'
            self._msg_timer = 2.0
            return
        player.gold -= item['price']
        inv = player.tower_inventory
        inv[item['name']] = inv.get(item['name'], 0) + 1
        self._msg       = f"Got {item['name']}! (x{inv[item['name']]})"
        self._msg_timer = 2.0

    def update(self, dt):
        if self._msg_timer > 0:
            self._msg_timer = max(0.0, self._msg_timer - dt)

    def draw(self):
        if not self.is_open:
            return
        W, H   = self.render.WIDTH, self.render.HEIGHT
        screen = self.render.screen

        overlay = pg.Surface((W, H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title = self._font_title.render('SHOP', True, (255, 215, 0))
        screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 150))

        gold_text = self._font_gold.render(f'Gold: {self.render.player.gold}', True, (255, 215, 0))
        screen.blit(gold_text, (W // 2 - gold_text.get_width() // 2, H // 2 - 110))

        shown         = self._shown_items()
        mouse_pos     = pg.mouse.get_pos()
        self._hovered = self._get_hovered(mouse_pos)
        visible = shown[self._scroll : self._scroll + self._max_vis]
        for vi, item in enumerate(visible):
            self._draw_card(vi, item, self._scroll + vi)

        self._draw_shop_arrows(screen, W, H)

        # page dots
        total = len(shown)
        if total > self._max_vis:
            dot_y = H // 2 + self._card_h // 2 + 32
            dot_r = 5
            dot_gap = 14
            pages = total - self._max_vis + 1
            start_x = W // 2 - (pages * dot_gap) // 2
            for p in range(pages):
                col = (255, 215, 0) if p == self._scroll else (100, 100, 100)
                pg.draw.circle(screen, col, (start_x + p * dot_gap, dot_y), dot_r)

        if self._msg_timer > 0 and self._msg:
            msg_surf = self._font_gold.render(self._msg, True, (255, 120, 120))
            screen.blit(msg_surf, (W // 2 - msg_surf.get_width() // 2, H // 2 + 120))

        hint = self._font_desc.render('[E] Close  |  Scroll to browse', True, (160, 160, 160))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 155))

    def _draw_shop_arrows(self, screen, W, H):
        la, ra = self._arrow_rects()
        for rect, enabled, pts_fn in [
            (la, self._scroll > 0,
             lambda r: [(r.right, r.centery), (r.left + 6, r.top + 6), (r.left + 6, r.bottom - 6)]),
            (ra, self._scroll < len(self._shown_items()) - self._max_vis,
             lambda r: [(r.left, r.centery), (r.right - 6, r.top + 6), (r.right - 6, r.bottom - 6)]),
        ]:
            col = (220, 220, 220) if enabled else (70, 70, 70)
            pg.draw.polygon(screen, col, pts_fn(rect))

    def _draw_card(self, vis_idx, item, global_idx):
        rect    = self._card_rect(vis_idx)
        hovered = (self._hovered == global_idx)
        screen  = self.render.screen

        bg = pg.Surface((rect.w, rect.h), pg.SRCALPHA)
        bg.fill((90, 90, 140, 240) if hovered else (60, 60, 80, 220))
        screen.blit(bg, rect.topleft)
        pg.draw.rect(screen, (200, 200, 255) if hovered else (120, 120, 160), rect, 2, border_radius=8)

        name_surf = self._font_item.render(item['name'], True, (255, 255, 255))
        screen.blit(name_surf, (rect.centerx - name_surf.get_width() // 2, rect.y + 12))

        desc_surf = self._font_desc.render(item['desc'], True, (160, 220, 160))
        screen.blit(desc_surf, (rect.centerx - desc_surf.get_width() // 2, rect.y + 44))

        price_surf = self._font_item.render(f'{item["price"]} gold', True, (255, 215, 0))
        screen.blit(price_surf, (rect.centerx - price_surf.get_width() // 2, rect.y + 72))

        btn = pg.Rect(rect.x + 20, rect.y + rect.h - 42, rect.w - 40, 30)
        pg.draw.rect(screen, (70, 190, 70) if hovered else (50, 140, 50), btn, border_radius=5)
        buy_text = self._font_desc.render('Buy', True, (255, 255, 255))
        screen.blit(buy_text, (btn.centerx - buy_text.get_width() // 2,
                                btn.centery - buy_text.get_height() // 2))


# =========================================================
# TOWER SELECT UI
# =========================================================

class TowerSelectUI:
    """แสดงขึ้นมาเมื่อ player คลิก wrench บน grid ว่าง — เลือก tower จาก tower_inventory
    หรือยืนยันการลบ tower ที่วางอยู่"""

    def __init__(self, render):
        self.render          = render
        self.is_open         = False
        self._pending_row    = None
        self._pending_col    = None
        self._hovered        = None
        self._click_consumed = False   # กัน click ทะลุหลัง close
        # confirm remove state
        self._confirm_open   = False
        self._confirm_row    = None
        self._confirm_col    = None
        self._confirm_hover  = None    # 'yes' | 'no' | None
        # message
        self._msg            = ''
        self._msg_timer      = 0.0
        # fonts
        self._font        = pg.font.SysFont('Arial', 18, bold=True)
        self._font_sm     = pg.font.SysFont('Arial', 14)
        self._font_title  = pg.font.SysFont('Arial', 22, bold=True)
        self._card_w      = 140
        self._card_h      = 120
        self._card_gap    = 16
        self._scroll      = 0
        self._max_vis     = 5

    # ── open / close ────────────────────────────────────────────

    def open(self, row, col):
        if not self._available():
            self._msg       = 'No towers in inventory — buy from shop first!'
            self._msg_timer = 2.0
            return
        self.is_open      = True
        self._pending_row = row
        self._pending_col = col
        self.render._set_mouse_lock(False)
        pg.mouse.set_pos(self.render.H_WIDTH, self.render.H_HEIGHT)

    def close(self):
        self.is_open         = False
        self._pending_row    = None
        self._pending_col    = None
        self._click_consumed = True    # consume next frame's click
        self.render._set_mouse_lock(True)

    def open_confirm(self, row, col):
        self._confirm_open  = True
        self._confirm_row   = row
        self._confirm_col   = col
        self._confirm_hover = None
        self.render._set_mouse_lock(False)
        pg.mouse.set_pos(self.render.H_WIDTH, self.render.H_HEIGHT)

    def close_confirm(self):
        self._confirm_open   = False
        self._confirm_row    = None
        self._confirm_col    = None
        self._click_consumed = True
        self.render._set_mouse_lock(True)

    @property
    def any_open(self):
        return self.is_open or self._confirm_open

    # ── available towers ────────────────────────────────────────

    def _available(self):
        from entities.tower import get_turret_types
        inv  = self.render.player.tower_inventory
        data = get_turret_types()
        return [(name, inv[name], data[name]) for name in inv if inv.get(name, 0) > 0 and name in data]

    # ── card layout ─────────────────────────────────────────────

    def _visible_count(self, total):
        return min(self._max_vis, total - self._scroll)

    def _card_rect(self, vis_idx, n_vis):
        W, H    = self.render.WIDTH, self.render.HEIGHT
        total_w = n_vis * self._card_w + (n_vis - 1) * self._card_gap
        x = W // 2 - total_w // 2 + vis_idx * (self._card_w + self._card_gap)
        y = H - self._card_h - 40
        return pg.Rect(x, y, self._card_w, self._card_h)

    def _arrow_rects(self, n_vis):
        W, H    = self.render.WIDTH, self.render.HEIGHT
        total_w = n_vis * self._card_w + (n_vis - 1) * self._card_gap
        cy = H - self._card_h - 40 + self._card_h // 2
        left  = pg.Rect(W // 2 - total_w // 2 - 36, cy - 16, 28, 32)
        right = pg.Rect(W // 2 + total_w // 2 +  8, cy - 16, 28, 32)
        return left, right

    def _get_hovered(self, pos):
        available = self._available()
        n_vis = self._visible_count(len(available))
        for vi in range(n_vis):
            if self._card_rect(vi, n_vis).collidepoint(pos):
                return self._scroll + vi
        return None

    # ── confirm button rects ────────────────────────────────────

    def _confirm_btn_rects(self):
        W, H = self.render.WIDTH, self.render.HEIGHT
        bw, bh = 110, 44
        gap    = 24
        cy     = H // 2 + 20
        yes_r  = pg.Rect(W // 2 - bw - gap // 2, cy, bw, bh)
        no_r   = pg.Rect(W // 2 + gap // 2,       cy, bw, bh)
        return yes_r, no_r

    # ── update ──────────────────────────────────────────────────

    def update(self, dt):
        if self._msg_timer > 0:
            self._msg_timer = max(0.0, self._msg_timer - dt)
        # reset consumed flag after one frame
        self._click_consumed = False

    # ── event handling ──────────────────────────────────────────

    def handle_event(self, event):
        # confirm dialog
        if self._confirm_open:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.close_confirm()
                return
            yes_r, no_r = self._confirm_btn_rects()
            if event.type == pg.MOUSEMOTION:
                pos = event.pos
                if yes_r.collidepoint(pos):
                    self._confirm_hover = 'yes'
                elif no_r.collidepoint(pos):
                    self._confirm_hover = 'no'
                else:
                    self._confirm_hover = None
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self._click_consumed = True
                pos = event.pos
                if yes_r.collidepoint(pos):
                    self._do_remove()
                elif no_r.collidepoint(pos):
                    self.close_confirm()
            return

        # select UI
        if not self.is_open:
            return
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self.close()
            return
        available = self._available()
        n_vis = self._visible_count(len(available))
        if event.type == pg.MOUSEWHEEL:
            self._scroll = max(0, min(len(available) - self._max_vis, self._scroll - event.y))
            return
        if event.type == pg.MOUSEMOTION:
            self._hovered = self._get_hovered(event.pos)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self._click_consumed = True
            la, ra = self._arrow_rects(n_vis)
            if la.collidepoint(event.pos):
                self._scroll = max(0, self._scroll - 1)
                return
            if ra.collidepoint(event.pos):
                self._scroll = min(len(available) - self._max_vis, self._scroll + 1)
                return
            idx = self._get_hovered(event.pos)
            if idx is not None:
                self._place(idx)

    # ── placement ───────────────────────────────────────────────

    def _place(self, idx):
        available = self._available()
        if idx >= len(available):
            return
        name, count, data = available[idx]
        from entities.tower import Tower
        r, c = self._pending_row, self._pending_col
        grid = self.render.placement_grid
        if grid[r][c] is None:
            grid[r][c] = Tower(
                self.render, row=r, col=c,
                filepath=data['file_path'],
                hp=data['hp'],
                damage=data['damage'],
                fire_rate=data['fire_rate'],
                offset=data['offset'],
                rotate_y=data['rotate_y'],
                price=data['price'],
                special=data.get('special', ''),
                range=data.get('range', 999),
            )
            self.render.player.tower_inventory[name] -= 1
        self.close()

    # ── remove with refund ──────────────────────────────────────

    def _do_remove(self):
        r, c = self._confirm_row, self._confirm_col
        grid = self.render.placement_grid
        if 0 <= r < len(grid) and 0 <= c < len(grid[r]):
            tower = grid[r][c]
            if tower is not None:
                refund = tower.price // 2
                self.render.player.gold += refund
                self._msg       = f'Removed! Refund: {refund} gold'
                self._msg_timer = 2.0
                tower.die()
        self.close_confirm()

    # ── draw ────────────────────────────────────────────────────

    def draw(self):
        W, H   = self.render.WIDTH, self.render.HEIGHT
        screen = self.render.screen

        # message (ขึ้นแม้ UI ปิด)
        if self._msg_timer > 0 and self._msg:
            msg_s = self._font_sm.render(self._msg, True, (255, 200, 80))
            screen.blit(msg_s, (W // 2 - msg_s.get_width() // 2, H - 50))

        # confirm dialog
        if self._confirm_open:
            self._draw_confirm(screen, W, H)
            return

        if not self.is_open:
            return

        # ── select cards ──
        available = self._available()
        n_vis     = self._visible_count(len(available))
        title = self._font_title.render('Select Tower to Place', True, (255, 255, 255))
        screen.blit(title, (W // 2 - title.get_width() // 2, H - self._card_h - 72))

        mouse_pos     = pg.mouse.get_pos()
        self._hovered = self._get_hovered(mouse_pos)
        visible = available[self._scroll : self._scroll + self._max_vis]
        for vi, (name, count, data) in enumerate(visible):
            gi   = self._scroll + vi
            rect = self._card_rect(vi, n_vis)
            hovered = (self._hovered == gi)

            bg = pg.Surface((rect.w, rect.h), pg.SRCALPHA)
            bg.fill((80, 140, 80, 240) if hovered else (50, 80, 50, 220))
            screen.blit(bg, rect.topleft)
            pg.draw.rect(screen, (150, 255, 150) if hovered else (90, 160, 90), rect, 2, border_radius=8)

            name_s = self._font.render(name.capitalize(), True, (255, 255, 255))
            screen.blit(name_s, (rect.centerx - name_s.get_width() // 2, rect.y + 10))

            desc_s = self._font_sm.render(f'DMG {data["damage"]} | {data["fire_rate"]}/s', True, (180, 230, 180))
            screen.blit(desc_s, (rect.centerx - desc_s.get_width() // 2, rect.y + 38))

            count_s = self._font.render(f'x{count}', True, (255, 220, 80))
            screen.blit(count_s, (rect.centerx - count_s.get_width() // 2, rect.y + 64))

            if hovered:
                place_s = self._font_sm.render('[Click] Place', True, (200, 255, 200))
                screen.blit(place_s, (rect.centerx - place_s.get_width() // 2, rect.y + 92))

        # arrows
        la, ra = self._arrow_rects(n_vis)
        for rect, enabled, pts_fn in [
            (la, self._scroll > 0,
             lambda r: [(r.right, r.centery), (r.left+6, r.top+6), (r.left+6, r.bottom-6)]),
            (ra, self._scroll < len(available) - self._max_vis,
             lambda r: [(r.left, r.centery), (r.right-6, r.top+6), (r.right-6, r.bottom-6)]),
        ]:
            pg.draw.polygon(screen, (200, 200, 200) if enabled else (70, 70, 70), pts_fn(rect))

        hint = self._font_sm.render('[ESC] Cancel  |  Scroll to browse', True, (160, 160, 160))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 16))

    def _draw_confirm(self, screen, W, H):
        # dimmed overlay
        overlay = pg.Surface((W, H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        r, c  = self._confirm_row, self._confirm_col
        grid  = self.render.placement_grid
        tower = grid[r][c] if (grid and 0 <= r < len(grid) and 0 <= c < len(grid[r])) else None
        refund = (tower.price // 2) if tower else 0

        title_s = self._font_title.render('Remove Tower?', True, (255, 160, 60))
        screen.blit(title_s, (W // 2 - title_s.get_width() // 2, H // 2 - 70))

        sub_s = self._font_sm.render(f'Refund: {refund} gold', True, (255, 215, 0))
        screen.blit(sub_s, (W // 2 - sub_s.get_width() // 2, H // 2 - 36))

        yes_r, no_r = self._confirm_btn_rects()
        mouse_pos = pg.mouse.get_pos()
        if yes_r.collidepoint(mouse_pos):
            self._confirm_hover = 'yes'
        elif no_r.collidepoint(mouse_pos):
            self._confirm_hover = 'no'
        else:
            self._confirm_hover = None

        for rect, label, base_col, hov_col in [
            (yes_r, 'Yes', (160, 50, 50), (220, 70, 70)),
            (no_r,  'No',  (50, 80, 50),  (70, 140, 70)),
        ]:
            hovered = (self._confirm_hover == label.lower())
            bg = pg.Surface((rect.w, rect.h), pg.SRCALPHA)
            bg.fill((*( hov_col if hovered else base_col), 230))
            screen.blit(bg, rect.topleft)
            pg.draw.rect(screen, (220, 220, 220) if hovered else (140, 140, 140), rect, 2, border_radius=6)
            lbl_s = self._font.render(label, True, (255, 255, 255))
            screen.blit(lbl_s, (rect.centerx - lbl_s.get_width() // 2,
                                 rect.centery - lbl_s.get_height() // 2))

        hint = self._font_sm.render('[ESC] Cancel', True, (160, 160, 160))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 80))
