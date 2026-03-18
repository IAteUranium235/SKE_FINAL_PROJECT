import pygame as pg


class Weapon:
    """
    อาวุธของ player — จัดการการยิง raycast
    ค่อยๆ เพิ่ม feature ทีหลัง
    """

    def __init__(self, player):
        self.player   = player
        self.name     = 'Weapon'
        self.equipped = False

    def on_equip(self):
        self.equipped = True
        print('[Weapon] equipped')

    def on_unequip(self):
        self.equipped = False

    def update(self, dt):
        pass

    def draw_hud(self, screen):
        pass
