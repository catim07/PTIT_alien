
import pygame
import sys
import os

# QUAN TRỌNG: Thêm hàm này để .exe tìm được nhạc
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AudioManager:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        self.current_music = None
        self.is_paused = False
        
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.menu_music = self._find_music("menu_music")
        self.game_music = self._find_music("game_music")

    def _find_music(self, name):
        for ext in ['.mp3', '.ogg', '.wav']:
            path = resource_path(os.path.join("src", "sounds", f"{name}{ext}"))
            if os.path.exists(path):
                print(f"Nhạc tìm thấy: {path}")
                return path
        print(f"Không tìm thấy nhạc: {name}")
        return None

    def play_music(self, path, fade=600):
        if not path or path == self.current_music:
            return
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(fade)
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
            self.current_music = path
        except Exception as e:
            print(f"Lỗi phát nhạc: {e}")

    def play_menu_music(self):
        if self.menu_music:
            self.play_music(self.menu_music)

    def play_game_music(self):
        if self.game_music:
            self.play_music(self.game_music)

    def pause_music(self):
        if pygame.mixer.music.get_busy() and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True

    def unpause_music(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False

    def stop_music(self):
        pygame.mixer.music.fadeout(800)

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.ai_game.sounds.values():
            if sound:
                sound.set_volume(self.sfx_volume)