"""
Drawing helpers for the in-game view.
Each function receives the render (SoftwareRender) instance and any extra args.
"""
import pygame as pg
import numpy as np


# ── sky & ground ──────────────────────────────────────────────────────────────

def build_sky(width, height):
    top, bot = (30, 60, 114), (135, 190, 235)
    surf = pg.Surface((width, height))
    for y in range(height):
        t = y / height
        pg.draw.line(surf, tuple(int(top[i] + (bot[i]-top[i])*t) for i in range(3)),
                     (0, y), (width, y))
    return surf


def draw_ground(render):
    fwd = render.camera.forward[:3]
    ys  = []
    for d in [3, 5, 10, 30, 80]:
        wp = np.array([render.camera.position[0]+fwd[0]*d, 0.0,
                       render.camera.position[2]+fwd[2]*d, 1.0])
        cp = wp @ render.camera.camera_matrix()
        if cp[2] < 0.1:
            continue
        pp = cp @ render.projection.projection_matrix
        if abs(pp[3]) < 1e-6:
            continue
        pp /= pp[3]
        sp = np.array([pp]) @ render.projection.to_screen_matrix
        ys.append(sp[0][1])
    horizon = int(max(0, min(render.HEIGHT, min(ys) if ys else render.H_HEIGHT)))
    if horizon < render.HEIGHT:
        pg.draw.rect(render.screen, (101, 139, 70),
                     (0, horizon, render.WIDTH, render.HEIGHT - horizon))


# ── HUD elements ──────────────────────────────────────────────────────────────

def draw_gold_hud(render, font):
    text   = font.render(f'Gold: {render.player.gold}', True, (255, 215, 0))
    shadow = font.render(f'Gold: {render.player.gold}', True, (0, 0, 0))
    x = render.WIDTH - text.get_width() - 10
    render.screen.blit(shadow, (x+1, 11))
    render.screen.blit(text,   (x,   10))


def draw_base_hp_bar(render, font):
    bw, bh = 200, 18
    frac = max(0.0, render.base_hp / render.base_max_hp)
    pg.draw.rect(render.screen, (60, 20, 20), (10, 10, bw, bh))
    pg.draw.rect(render.screen, (int(255*(1-frac)), int(200*frac), 0),
                 (10, 10, int(bw*frac), bh))
    pg.draw.rect(render.screen, (200, 200, 200), (10, 10, bw, bh), 2)
    lbl = font.render(f'Base HP  {render.base_hp}/{render.base_max_hp}', True, (255, 255, 255))
    render.screen.blit(lbl, (14, 11))


def draw_damage_numbers(render, font):
    cam_mat  = render.camera.camera_matrix()
    proj_mat = render.projection.projection_matrix
    alive = []
    for dn in render.damage_numbers:
        dn['timer'] -= render.dt
        if dn['timer'] <= 0:
            continue
        alive.append(dn)
        t  = 1.0 - dn['timer'] / dn['max_timer']
        wp = np.array([dn['x'], dn['y'] + t*2.5, dn['z'], 1.0])
        cp = wp @ cam_mat
        if cp[2] < 0.1:
            continue
        pp = cp @ proj_mat
        if abs(pp[3]) < 1e-6:
            continue
        pp /= pp[3]
        sx = int(pp[0]*render.H_WIDTH  + render.H_WIDTH)
        sy = int(-pp[1]*render.H_HEIGHT + render.H_HEIGHT)
        if not (-60 < sx < render.WIDTH+60 and -30 < sy < render.HEIGHT+30):
            continue
        label = f'+{dn["value"]}g' if dn.get('gold') else f'-{dn["value"]}'
        color = (255, 215, 0)      if dn.get('gold') else (255, 80, 80)
        surf  = font.render(label, True, color)
        surf.set_alpha(int(255 * dn['timer'] / dn['max_timer']))
        render.screen.blit(surf, (sx - surf.get_width()//2, sy - surf.get_height()//2))
    render.damage_numbers = alive


# ── polygon pool ──────────────────────────────────────────────────────────────

def flush_pool(render):
    render.polygon_pool.sort(key=lambda x: x['depth'], reverse=True)
    for entry in render.polygon_pool:
        if 'billboard' in entry:
            b = entry['billboard']
            render.screen.blit(b['surf'], (b['sx']-b['w']//2, b['sy']-b['h']//2))
            if 'enemy_ref' in b:
                b['enemy_ref'].draw_hp_bar(render.screen, entry)
        elif len(entry['points']) >= 3:
            pg.draw.polygon(render.screen, entry['color'], entry['points'])
