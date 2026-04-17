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
        ('Resume',   'resume'),
        ('Quit',     'quit'),
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
        elif action == 'quit':
            pg.quit()
            exit()

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
# SHOP GUI
# =========================================================

class ShopGUI:
    ITEMS = [
        {'name': 'Basic Tower',  'desc': 'DMG 20 | Rate 1/s',   'price': 50,  'hp': 100, 'damage': 20, 'fire_rate': 1.0},
        {'name': 'Rapid Tower',  'desc': 'DMG 10 | Rate 3/s',   'price': 100, 'hp': 80,  'damage': 10, 'fire_rate': 3.0},
        {'name': 'Heavy Tower',  'desc': 'DMG 50 | Rate 0.5/s', 'price': 200, 'hp': 200, 'damage': 50, 'fire_rate': 0.5},
    ]

    def __init__(self, render):
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
        if event.type == pg.MOUSEMOTION:
            self._hovered = self._get_hovered(event.pos)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._get_hovered(event.pos)
            if idx is not None:
                self._buy(idx)

    def _card_rect(self, idx):
        W, H = self.render.WIDTH, self.render.HEIGHT
        total_w = len(self.ITEMS) * self._card_w + (len(self.ITEMS) - 1) * self._card_gap
        start_x = W // 2 - total_w // 2
        x = start_x + idx * (self._card_w + self._card_gap)
        y = H // 2 - self._card_h // 2 + 20
        return pg.Rect(x, y, self._card_w, self._card_h)

    def _get_hovered(self, pos):
        for i in range(len(self.ITEMS)):
            if self._card_rect(i).collidepoint(pos):
                return i
        return None

    def _buy(self, idx):
        item   = self.ITEMS[idx]
        player = self.render.player
        if player.gold < item['price']:
            self._msg       = 'Not enough gold!'
            self._msg_timer = 2.0
            return
        grid = self.render.placement_grid
        for r in range(len(grid)):
            for c in range(len(grid[r])):
                if grid[r][c] is None:
                    from tower import Tower
                    grid[r][c] = Tower(
                        self.render, row=r, col=c,
                        filepath='resource/Turret.obj',
                        hp=item['hp'],
                        damage=item['damage'],
                        fire_rate=item['fire_rate'],
                    )
                    player.gold    -= item['price']
                    self._msg       = f"Placed {item['name']}!"
                    self._msg_timer = 2.0
                    return
        self._msg       = 'No empty grid slots!'
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

        mouse_pos     = pg.mouse.get_pos()
        self._hovered = self._get_hovered(mouse_pos)
        for i, item in enumerate(self.ITEMS):
            self._draw_card(i, item)

        if self._msg_timer > 0 and self._msg:
            msg_surf = self._font_gold.render(self._msg, True, (255, 120, 120))
            screen.blit(msg_surf, (W // 2 - msg_surf.get_width() // 2, H // 2 + 120))

        hint = self._font_desc.render('[E] Close', True, (160, 160, 160))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 150))

    def _draw_card(self, idx, item):
        rect    = self._card_rect(idx)
        hovered = (self._hovered == idx)
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
