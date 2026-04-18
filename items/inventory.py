import pygame as pg


class Inventory:
    """
    จัดการ item ที่ player ถืออยู่ — สลับด้วยปุ่ม 1-9

    ตัวอย่างการใช้งานใน main.py / player.py:

        from inventory import Inventory
        from weapon import Weapon
        from wrench import Wrench

        # ใน create_objects() หรือ Player.__init__()
        self.inventory = Inventory(player)
        self.inventory.add(1, Weapon(player))
        self.inventory.add(2, Wrench(player))
        self.inventory.equip(1)   # เริ่มต้นถือ weapon

        # ใน update()
        self.inventory.update(dt)

        # ใน draw() หลังสุด
        self.inventory.draw_hud(screen)
    """

    def __init__(self, player):
        self.player  = player
        self.slots   = {}        # {slot_number: item}
        self.current = None      # item ที่ถืออยู่ตอนนี้
        self.current_slot = None

        self._font       = None
        self._slot_size  = 52
        self._padding    = 8

        # key map 1-9 → slot
        self._key_map = {
            pg.K_1: 1, pg.K_2: 2, pg.K_3: 3,
            pg.K_4: 4, pg.K_5: 5, pg.K_6: 6,
            pg.K_7: 7, pg.K_8: 8, pg.K_9: 9,
        }

    # =========================================================
    # SLOT MANAGEMENT
    # =========================================================

    def add(self, slot: int, item):
        """ใส่ item เข้า slot หมายเลขที่กำหนด"""
        self.slots[slot] = item

    def equip(self, slot: int):
        """สลับไปถือ item ใน slot นั้น"""
        if slot not in self.slots:
            return
        if self.current is not None:
            self.current.on_unequip()
        self.current      = self.slots[slot]
        self.current_slot = slot
        self.current.on_equip()

    def unequip(self):
        """วาง item ที่ถืออยู่ลง"""
        if self.current is not None:
            self.current.on_unequip()
            self.current      = None
            self.current_slot = None

    # =========================================================
    # UPDATE
    # =========================================================

    def handle_event(self, event):
        """ส่ง pygame event เข้ามา — ใช้ KEYDOWN แทน get_pressed เพื่อกันรัว"""
        if event.type != pg.KEYDOWN:
            return
        slot = self._key_map.get(event.key)
        if slot is None or slot not in self.slots:
            return
        if slot == self.current_slot:
            self.unequip()
        else:
            self.equip(slot)

    def update(self, dt):
        """เรียกทุก frame — update item ที่ถืออยู่"""
        if self.current:
            self.current.update(dt)

    # =========================================================
    # DRAW HUD
    # =========================================================

    def draw_hud(self, screen):
        """วาด slot bar กลางล่างจอ"""
        if not self._font:
            self._font = pg.font.SysFont('Arial', 13, bold=True)

        W      = screen.get_width()
        H      = screen.get_height()
        sz     = self._slot_size
        pad    = self._padding
        slots  = sorted(self.slots.keys())
        n      = len(slots)
        total_w = n * sz + (n - 1) * pad
        start_x = W // 2 - total_w // 2
        y       = H - sz - 16

        for i, slot in enumerate(slots):
            x       = start_x + i * (sz + pad)
            item    = self.slots[slot]
            active  = (slot == self.current_slot)

            # กรอบ slot
            bg_color     = (60, 60, 60, 200)
            border_color = (255, 215, 0) if active else (120, 120, 120)
            border_w     = 3 if active else 1

            bg = pg.Surface((sz, sz), pg.SRCALPHA)
            bg.fill((40, 40, 40, 180) if not active else (70, 60, 20, 200))
            screen.blit(bg, (x, y))
            pg.draw.rect(screen, border_color, (x, y, sz, sz), border_w)

            # หมายเลข slot มุมบนซ้าย
            num_surf = self._font.render(str(slot), True, (180, 180, 180))
            screen.blit(num_surf, (x + 4, y + 4))

            # ชื่อ item กลาง slot
            name_surf = self._font.render(item.name, True,
                                          (255, 255, 255) if active else (160, 160, 160))
            nw, nh = name_surf.get_size()
            screen.blit(name_surf, (x + sz//2 - nw//2, y + sz//2 - nh//2 + 4))

        # draw HUD ของ item ที่ถืออยู่
        if self.current:
            self.current.draw_hud(screen)
