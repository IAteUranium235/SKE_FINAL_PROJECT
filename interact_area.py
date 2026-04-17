import pygame as pg
import numpy as np


class InteractArea:
    """
    พื้นที่ทรงกลมรอบ object — ถ้า player เข้ามาใกล้และกดปุ่มที่กำหนด จะ trigger callback

    พารามิเตอร์:
        position  — (x, y, z) จุดศูนย์กลาง
        radius    — ระยะที่ถือว่าอยู่ใน zone
        key       — pygame key เช่น pg.K_e
        callback  — function(player) ที่จะถูกเรียกเมื่อ interact
        label     — ข้อความแสดงบนหน้าจอเมื่ออยู่ใน zone
        cooldown  — วินาทีที่ต้องรอก่อน interact ซ้ำได้ (default 1.0)
    """

    def __init__(self, position, radius=3.0, key=pg.K_e,
                 callback=None, label='Press E', cooldown=1.0):
        self.position = np.array(position, dtype=float)
        self.radius   = radius
        self.key      = key
        self.callback = callback
        self.label    = label
        self.cooldown = cooldown
        self._timer   = 0.0   # นับเวลา cooldown
        self._in_zone = False  # player อยู่ใน zone ไหม

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, player, dt):
        """เรียกทุก frame — เช็ค distance และ key press"""
        self._timer = max(0.0, self._timer - dt)

        # เช็คระยะ XZ เท่านั้น (ไม่สนใจ Y)
        dx = player.position[0] - self.position[0]
        dz = player.position[2] - self.position[2]
        dist = (dx**2 + dz**2) ** 0.5

        self._in_zone = dist <= self.radius

        if self._in_zone and self._timer <= 0:
            keys = pg.key.get_pressed()
            if keys[self.key]:
                self._trigger(player)

    def _trigger(self, player):
        """เรียก callback และ reset cooldown"""
        if self.callback:
            self.callback(player)
        self._timer = self.cooldown

    # =========================================================
    # DRAW HUD
    # =========================================================

    def draw_hud(self, screen):
        """แสดง prompt เมื่อ player อยู่ใน zone"""
        if not self._in_zone:
            return
        if not hasattr(self, '_font'):
            self._font = pg.font.SysFont('Arial', 22, bold=True)

        # กรอบ + ข้อความกลางล่างจอ
        W = screen.get_width()
        H = screen.get_height()
        text    = self._font.render(self.label, True, (255, 255, 255))
        padding = 12
        tw, th  = text.get_size()
        bx      = W // 2 - tw // 2 - padding
        by      = H - 70
        bw      = tw + padding * 2
        bh      = th + padding

        # shadow box
        s = pg.Surface((bw, bh), pg.SRCALPHA)
        s.fill((0, 0, 0, 160))
        screen.blit(s, (bx, by))
        screen.blit(text, (bx + padding, by + padding // 2))


# =========================================================
# PRESET CALLBACKS
# =========================================================

def speed_boost(amount=5, duration=5.0):
    """
    เพิ่มความเร็ว player ชั่วคราว
    ต้องการให้ player มี attribute: _speed_timer, _base_speed
    """
    def callback(player):
        if not hasattr(player, '_base_speed'):
            player._base_speed = 0.2
        player.move_speed  = player._base_speed + amount
        player._speed_timer = duration
        print(f"[InteractArea] Speed boost! +{amount} for {duration}s")
    return callback


def heal(amount=20):
    """เพิ่ม HP (ถ้า player มี .hp)"""
    def callback(player):
        if hasattr(player, 'hp'):
            player.hp = min(getattr(player, 'max_hp', 100), player.hp + amount)
            print(f"[InteractArea] Healed +{amount} HP → {player.hp}")
        else:
            print("[InteractArea] Heal: player ไม่มี hp attribute")
    return callback


def teleport(destination):
    """teleport player ไปยัง position ที่กำหนด"""
    dest = np.array([*destination, 1.0])
    def callback(player):
        player.position = dest.copy()
        player.velocity_y = 0
        print(f"[InteractArea] Teleport → {destination}")
    return callback


def open_shop(render):
    """เปิด/ปิด ShopGUI"""
    def callback(player):
        if hasattr(render, 'shop_gui') and not render.shop_gui.is_open:
            render.shop_gui.toggle()
    return callback


def custom(func):
    """ใส่ function เองได้เลย — func(player)"""
    return func


# =========================================================
# MANAGER
# =========================================================

class InteractManager:
    """
    จัดการ InteractArea หลายจุดพร้อมกัน
    ใช้แทนการ loop ใน main.py

    ตัวอย่างการใช้งานใน main.py:
        from interact_area import InteractArea, InteractManager, speed_boost, teleport

        self.interact = InteractManager()
        self.interact.add(InteractArea(
            position=[10, 0, 5],
            radius=3.0,
            key=pg.K_e,
            callback=speed_boost(amount=0.15, duration=5.0),
            label='[E] Speed Boost'
        ))
        self.interact.add(InteractArea(
            position=[-10, 0, 0],
            radius=2.5,
            key=pg.K_e,
            callback=teleport([0, 2, 0]),
            label='[E] Teleport to Start'
        ))

    แล้วใน update():
        self.interact.update(self.player, self.dt)

    แล้วใน draw() หลัง flush_pool():
        self.interact.draw_hud(self.screen)
    """

    def __init__(self):
        self.areas = []

    def add(self, area: InteractArea):
        self.areas.append(area)
        return self  # chain ได้

    def update(self, player, dt):
        for area in self.areas:
            area.update(player, dt)

    def draw_hud(self, screen):
        for area in self.areas:
            area.draw_hud(screen)
