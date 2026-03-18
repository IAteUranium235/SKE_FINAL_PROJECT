import pygame as pg
from matrix_function import *

class Camera:
    def __init__(self, render, position):
        self.render = render
        self.position = np.array([*position, 1.0])
        self.forward = np.array([0, 0 ,1, 1])
        self.up = np.array([0, 1, 0, 1])
        self.right = np.array([1, 0, 0, 1])
        self.h_fov = math.pi / 3
        self.v_fov = self.h_fov * (render.HEIGHT / render.WIDTH)
        self.near_plane = 0.1
        self.far_plane = 300
        self.moving_speed = 10
        self.rotation_speed = 0.01
        self.pitch = 0
        self.yaw = 0
        self.mouse_sensitivity = 0.002
        self.update_vectors()
        
        
    def control(self, dt):
        actual_speed = self.moving_speed * dt 
        
        key = pg.key.get_pressed()
        if key[pg.K_a]:
            self.position -= self.right * actual_speed
        if key[pg.K_d]:
            self.position += self.right * actual_speed
        if key[pg.K_w]:
            self.position += self.forward * actual_speed
        if key[pg.K_s]:
            self.position -= self.forward * actual_speed
        if key[pg.K_q]:
            self.position += self.up * actual_speed
        if key[pg.K_e]:
            self.position -= self.up * actual_speed
            
        mouse_dx, mouse_dy = pg.mouse.get_rel()
        
        if mouse_dx != 0:
            self.camera_yaw(mouse_dx * self.mouse_sensitivity)
            
        if mouse_dy != 0:
            # ถ้าก้มเงยแล้วรู้สึก "กลับด้าน" (Inverted) ให้เปลี่ยนเป็น -mouse_dy แทนครับ
            self.camera_pitch(mouse_dy * self.mouse_sensitivity)
        
        
    def camera_yaw(self, angle):
        self.yaw += angle
        self.update_vectors()
        
    def camera_pitch(self, angle):
        # ล็อคมุมก้มเงย ไม่ให้ตีลังกา (ประมาณ +- 89 องศา)
        self.pitch = max(-math.pi/2.1, min(math.pi/2.1, self.pitch + angle))
        self.update_vectors()
        
    def update_vectors(self):
        base_forward = np.array([0, 0, 1, 1])
        base_right   = np.array([1, 0, 0, 1])
        base_up      = np.array([0, 1, 0, 1])
        rotate = rotate_x(self.pitch) @ rotate_y(self.yaw)
        self.forward = base_forward @ rotate
        self.right   = base_right   @ rotate
        self.up      = base_up      @ rotate
        # ✅ cache ทันทีที่ vectors เปลี่ยน
        x, y, z = self.position[:3]
        self._cached_cam_matrix = (
            translate([-x, -y, -z]) @ rotate_y(-self.yaw) @ rotate_x(-self.pitch)
        )
        
    def _build_camera_matrix(self):
        x, y, z = self.position[:3]
        return translate([-x, -y, -z]) @ rotate_y(-self.yaw) @ rotate_x(-self.pitch)
        
    
    def translate_matrix(self):
        x, y, z, w = self.position
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [-x, -y, -z, 1]
        ])
        
        
    def rotate_matrix(self):
        rx, ry, rz, w = self.right
        fx, fy, fz, w = self.forward
        ux, uy, uz, w = self.up
        return np.array([
            [rx, ux, fx, 0],
            [ry, uy, fy, 0],
            [rz, uz, fz, 0],
            [0, 0, 0, 1]
        ])
        
    def camera_matrix(self):
        return self._cached_cam_matrix