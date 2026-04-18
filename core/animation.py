import math

class Animation:
    def __init__(self, name, speed, swing_amplitude, bob_amplitude=0.0, mode='alternate'):
        self.name = name
        self.speed = speed
        self.swing_amplitude = swing_amplitude
        self.bob_amplitude = bob_amplitude
        self.mode = mode  # 'alternate' = สลับ, 'sync' = พร้อมกัน
        self.time = 0.0

    def update(self, dt):
        self.time += self.speed * dt * 60

    def get_swing(self):
        return math.sin(self.time) * self.swing_amplitude

    def get_swing_sync(self):
        # ✅ คืนค่าเดียวกันทั้งสองข้าง ใช้สำหรับ jump
        return math.sin(self.time) * self.swing_amplitude

    def get_bob(self):
        return math.sin(self.time) * self.bob_amplitude

    def reset(self):
        self.time = 0.0