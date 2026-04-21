import os
import pygame as pg
from core.object_3d import Object3D


def load_mtl(filename):
    materials = {}
    current_mat = None
    try:
        with open(filename) as f:
            for line in f:
                if line.startswith('newmtl '):
                    current_mat = line.split()[1]
                elif line.startswith('Kd ') and current_mat:
                    r, g, b = [float(i) for i in line.split()[1:4]]
                    materials[current_mat] = pg.Color(int(r*255), int(g*255), int(b*255))
    except FileNotFoundError:
        print(f"[OBJ] MTL not found: '{filename}'")
    return materials


def load_obj(render, filename):
    vertex, faces, color_faces = [], [], []
    materials = {}
    current_color = pg.Color('white')
    obj_dir = os.path.dirname(filename)
    with open(filename) as f:
        for line in f:
            if line.startswith('mtllib '):
                materials = load_mtl(os.path.join(obj_dir, line.split()[1]))
            elif line.startswith('usemtl '):
                current_color = materials.get(line.split()[1], pg.Color('white'))
            elif line.startswith('v '):
                vertex.append([float(i) for i in line.split()[1:]] + [1])
            elif line.startswith('f '):
                indices = [int(f.split('/')[0]) - 1 for f in line.split()[1:]]
                for i in range(1, len(indices) - 1):
                    face = [indices[0], indices[i], indices[i+1]]
                    faces.append(face)
                    color_faces.append((current_color, face))
    return Object3D(render, vertex, faces, color_faces)
