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

    #def toggle(self):
    #    self.is_open = not self.is_open
    #    self.render._set_mouse_lock(not self.is_open)
    #    if self.is_open:
    #        pg.mouse.set_pos(self.render.H_WIDTH, self.render.H_HEIGHT)
            
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
