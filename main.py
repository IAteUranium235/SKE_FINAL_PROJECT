import pygame as pg
from object_3d import *
from camera import *
from projection import *
class SoftwareRender:
    def __init__(self):
        pg.init(   ) 
        self.RES = self.WIDTH, self.HEIGHT = 800, 450
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.FPS = 60
        self.screen = pg.display.set_mode(self.RES)
        self.clock = pg.time.Clock()
        self.create_object()
        
        
    def create_object(self):
        self.camera = Camera(self, [-5, 5, -50])
        self.projection = Projection(self)
        self.object = self.get_object_from_file('resource/BR_Charizard-Shiny01.obj')
        
         
    def draw(self):
        self.screen.fill(pg.Color('darkslategray'))
        self.object.draw()
        
        
    def get_object_from_file(self, filename):
        vertex, faces = [], []
        with open(filename) as f:
            for line in f:
                if line.startswith('v '):
                    vertex.append([float(i) for i in line.split()[1:]] + [1])
                elif line.startswith('f'):
                    face_indices = [int(face_.split('/')[0]) - 1 for face_ in line.split()[1:]]
                    for i in range(1, len(face_indices) - 1):
                        faces.append([face_indices[0], face_indices[i], face_indices[i+1]])
        print(faces)
        return Object3D(self, vertex, faces)
        
    def run(self):
        while True:
            self.draw()
            self.camera.control()
            [exit() for i in pg.event.get() if i.type == pg.QUIT]
            pg.display.set_caption(str(self.clock.get_fps()))
            pg.display.flip()
            self.clock.tick(self.FPS)
            
if __name__ == '__main__':
    app = SoftwareRender()
    app.run()