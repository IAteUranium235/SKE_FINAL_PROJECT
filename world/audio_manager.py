import csv
import pygame as pg

MUSIC_END = pg.USEREVENT + 10

_AUDIO_DATA = {}

def load_audio_data(csv_path='data/audio.csv'):
    global _AUDIO_DATA
    _AUDIO_DATA = {}
    try:
        with open(csv_path, newline='') as f:
            for row in csv.DictReader(f):
                _AUDIO_DATA[row['name']] = {
                    'path':     row['audio_path'].strip(),
                    'loudness': float(row['loudness']),
                }
    except FileNotFoundError:
        print('[Audio] audio.csv not found')
    return _AUDIO_DATA


class AudioManager:
    def __init__(self):
        self._data      = {}
        self._sfx       = {}
        self._state     = None
        self._music_vol = 0.7
        self._sfx_vol   = 1.0

    def load(self, music_vol=0.7, sfx_vol=1.0):
        self._data      = load_audio_data()
        self._music_vol = music_vol
        self._sfx_vol   = sfx_vol
        pg.mixer.music.set_endevent(MUSIC_END)

        for key in ('sfx_bullet', 'sfx_win'):
            info = self._data.get(key)
            if not info:
                continue
            try:
                s = pg.mixer.Sound(info['path'])
                s.set_volume(info['loudness'] * sfx_vol)
                self._sfx[key] = s
            except Exception as e:
                print(f'[Audio] SFX load failed ({key}): {e}')

    def set_volumes(self, music_vol, sfx_vol):
        self._music_vol = music_vol
        self._sfx_vol   = sfx_vol
        for key, sound in self._sfx.items():
            sound.set_volume(self._data[key]['loudness'] * sfx_vol)
        if pg.mixer.music.get_busy():
            key = self._state
            info = self._data.get(key) if key else None
            if info:
                pg.mixer.music.set_volume(info['loudness'] * music_vol)

    # ── internal ──────────────────────────────────────────────────────

    def _play_music(self, key, loops=0):
        info = self._data.get(key)
        if not info:
            return
        try:
            pg.mixer.music.load(info['path'])
            pg.mixer.music.set_volume(info['loudness'] * self._music_vol)
            pg.mixer.music.play(loops)
            self._state = key
        except Exception as e:
            print(f'[Audio] Music load failed ({key}): {e}')

    # ── public API ────────────────────────────────────────────────────

    def play_menu(self):
        if self._state == 'stx_menu':
            return
        self._play_music('stx_menu', loops=-1)

    def play_wave_normal(self):
        """wave ปกติ: เล่น start ก่อน → จะ loop อัตโนมัติเมื่อจบ (ผ่าน handle_event)"""
        if self._state in ('stx_normal_wave_start', 'stx_normal_wave_loop'):
            return
        self._play_music('stx_normal_wave_start', loops=0)

    def play_last_wave(self):
        if self._state == 'last_wave':
            return
        self._play_music('last_wave', loops=-1)

    def play_boss(self):
        if self._state == 'stx_boss':
            return
        self._play_music('stx_boss', loops=-1)

    def play_win(self):
        pg.mixer.music.stop()
        self._state = None
        s = self._sfx.get('sfx_win')
        if s:
            s.play()

    def play_sfx(self, key):
        s = self._sfx.get(key)
        if s:
            s.play()

    def stop(self):
        pg.mixer.music.stop()
        self._state = None

    def handle_event(self, event):
        if event.type == MUSIC_END:
            if self._state == 'stx_normal_wave_start':
                self._play_music('stx_normal_wave_loop', loops=-1)
            elif self._state == 'stx_normal_wave_end':
                self._play_music('stx_normal_wave_start', loops=0)

    def on_wave_start(self, wave_num, total_waves, is_boss_level):
        if is_boss_level:
            self.play_boss()
        elif wave_num >= total_waves:
            self.play_last_wave()
        else:
            self.play_wave_normal()
