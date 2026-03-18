import pygame as pg


class Wrench:
    """
    ประแจสำหรับจัดการ tower — วาง / อัปเกรด / ซ่อม
    ค่อยๆ เพิ่ม feature ทีหลัง
    """

    def __init__(self, player):
        self.player   = player
        self.name     = 'Wrench'
        self.equipped = False

    def on_equip(self):
        self.equipped = True
        print('[Wrench] equipped')

    def on_unequip(self):
        self.equipped = False

    def update(self, dt):
        pass

    def draw_hud(self, screen):
        pass
