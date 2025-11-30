# src/settings_menu.py
"""
MENU CÀI ĐẶT – ĐÃ FIX HOÀN TOÀN LỖI FULLSCREEN
"""
import pygame
import json
from pathlib import Path
from font_helper import get_font


class SettingsMenu:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        self.audio = getattr(ai_game, 'audio_manager', None)
        self.save_file = Path("save_data.json")

        self.hovered = None
        self._init_layout()

        # Tải cài đặt (NHƯNG KHÔNG ÁP DỤNG FULLSCREEN NGAY)
        self.load_settings()

        self.title_font = get_font(72)
        self.label_font = get_font(36)
        self.button_font = get_font(40)

    def _init_layout(self):
        self.center_x = self.screen.get_width() // 2

        self.slider_width = 500
        self.slider_height = 20
        self.volume_rect = pygame.Rect(0, 0, self.slider_width, self.slider_height)
        self.volume_rect.center = (self.center_x, 280)

        self.btn_size = 50
        self.vol_minus = pygame.Rect(0, 0, self.btn_size, self.btn_size)
        self.vol_plus = pygame.Rect(0, 0, self.btn_size, self.btn_size)
        self.vol_minus.center = (self.center_x - self.slider_width // 2 - 40, 280)
        self.vol_plus.center = (self.center_x + self.slider_width // 2 + 40, 280)

        self.fs_rect = pygame.Rect(0, 0, 40, 40)
        self.fs_rect.center = (self.center_x + 150, 380)

        self.back_button = pygame.Rect(0, 0, 260, 70)
        self.back_button.center = (self.center_x, 500)

    def load_settings(self):
        default = {'volume': 0.5, 'fullscreen': False}
        if self.save_file.exists():
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saved = data.get('settings', {})
                    default.update(saved)
            except Exception as e:
                print(f"Load settings error: {e}")

        self.volume = default['volume']
        # BẮT BUỘC MỞ GAME Ở CỬA SỔ – KHÔNG TỰ FULLSCREEN
        self.fullscreen = False

        if self.audio:
            self.audio.set_music_volume(self.volume)
        # KHÔNG GỌI _apply_fullscreen() ở đây → tránh crash

    def save_settings(self):
        try:
            data = {}
            if self.save_file.exists():
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            data['settings'] = {
                'volume': self.volume,
                'fullscreen': self.fullscreen
            }
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Save settings error: {e}")

    def _apply_fullscreen(self):
        """Chuyển fullscreen một cách an toàn, chạy được trên mọi máy (kể cả Intel HD cũ)"""
        try:
            if self.fullscreen:
                info = pygame.display.Info()
                w = info.current_w
                h = info.current_h
                if w <= 0 or h <= 0:
                    w, h = 1920, 1080

                # Ưu tiên cách đẹp nhất
                try:
                    self.ai_game.screen = pygame.display.set_mode(
                        (w, h),
                        pygame.FULLSCREEN | pygame.SCALED
                    )
                    print(f"Fullscreen thành công (SCALED): {w}×{h}")
                except:
                    # Nếu lỗi → dùng cách cũ vẫn chạy tốt
                    self.ai_game.screen = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
                    print(f"Fullscreen thành công (không SCALED): {w}×{h}")
            else:
                self.ai_game.screen = pygame.display.set_mode(
                    (self.settings.screen_width, self.settings.screen_height),
                    pygame.RESIZABLE
                )
                print("Đã trở về cửa sổ 1200×800")

            # Cập nhật lại toàn bộ
            self.ai_game.screen_rect = self.ai_game.screen.get_rect()
            self.screen = self.ai_game.screen
            self.center_x = self.screen.get_width() // 2
            self._update_positions()

            # Scale lại tất cả background cho vừa màn hình mới
            if hasattr(self.ai_game, 'resize_all_backgrounds'):
                self.ai_game.resize_all_backgrounds()

            # Cập nhật vị trí các menu khác
            menus = ['menu', 'level_menu', 'pause_menu', 'level_complete_menu', 'game_over_menu']
            for name in menus:
                menu = getattr(self.ai_game, name, None)
                if menu:
                    for method_name in ['resize', 'update_positions', 'update_button_positions', '_update_button_positions']:
                        if hasattr(menu, method_name):
                            try:
                                getattr(menu, method_name)()
                                break
                            except:
                                pass

        except Exception as e:
            print(f"Lỗi fullscreen: {e} → Ép về cửa sổ")
            self.fullscreen = False
            self.ai_game.screen = pygame.display.set_mode((1200, 800))
            self.ai_game.screen_rect = self.ai_game.screen.get_rect()
            self.screen = self.ai_game.screen

    def _update_positions(self):
        self.volume_rect.center = (self.center_x, 280)
        self.vol_minus.center = (self.center_x - self.slider_width // 2 - 40, 280)
        self.vol_plus.center = (self.center_x + self.slider_width // 2 + 40, 280)
        self.fs_rect.center = (self.center_x + 150, 380)
        self.back_button.center = (self.center_x, 500)

    def draw(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((20, 20, 40, 230))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("CÀI ĐẶT", True, (255, 255, 100))
        self.screen.blit(title, title.get_rect(center=(self.center_x, 130)))

        vol_text = self.label_font.render(f"Âm lượng: {int(self.volume * 100)}%", True, (255, 255, 255))
        self.screen.blit(vol_text, vol_text.get_rect(center=(self.center_x, 220)))

        pygame.draw.rect(self.screen, (60, 60, 80), self.volume_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.volume_rect, 2, border_radius=12)
        fill_w = int(self.volume_rect.width * self.volume)
        pygame.draw.rect(self.screen, (0, 220, 180), (self.volume_rect.x, self.volume_rect.y, fill_w, self.volume_rect.height), border_radius=12)

        self._draw_round_button(self.vol_minus, "−", (220, 70, 70), (255, 100, 100))
        self._draw_round_button(self.vol_plus, "+", (70, 220, 70), (100, 255, 100))

        fs_text = self.label_font.render("Toàn màn hình", True, (255, 255, 255))
        self.screen.blit(fs_text, fs_text.get_rect(midright=(self.fs_rect.left - 20, self.fs_rect.centery)))

        pygame.draw.rect(self.screen, (100, 100, 120), self.fs_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), self.fs_rect, 2, border_radius=10)
        if self.fullscreen:
            pygame.draw.circle(self.screen, (0, 255, 0), self.fs_rect.center, 12)

        back_color = (220, 60, 60) if self.hovered == self.back_button else (200, 40, 40)
        pygame.draw.rect(self.screen, back_color, self.back_button, border_radius=16)
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button, 3, border_radius=16)
        back_text = self.button_font.render("QUAY LẠI", True, (255, 255, 255))
        self.screen.blit(back_text, back_text.get_rect(center=self.back_button.center))

    def _draw_round_button(self, rect, text, color, hover_color):
        col = hover_color if self.hovered == rect else color
        pygame.draw.rect(self.screen, col, rect, border_radius=14)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=14)
        txt = self.button_font.render(text, True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = None

        if self.back_button.collidepoint(mouse_pos):    self.hovered = self.back_button
        elif self.vol_minus.collidepoint(mouse_pos):     self.hovered = self.vol_minus
        elif self.vol_plus.collidepoint(mouse_pos):      self.hovered = self.vol_plus
        elif self.volume_rect.collidepoint(mouse_pos):   self.hovered = self.volume_rect
        elif self.fs_rect.collidepoint(mouse_pos):       self.hovered = self.fs_rect

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    self.save_settings()
                    self.stats.show_settings = False
                    return

                elif self.volume_rect.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    x = mouse_pos[0] - self.volume_rect.x
                    self.volume = max(0.0, min(1.0, x / self.volume_rect.width))
                    if self.audio:
                        self.audio.set_music_volume(self.volume)

                elif self.vol_minus.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    self.volume = max(0.0, self.volume - 0.1)
                    if self.audio:
                        self.audio.set_music_volume(self.volume)

                elif self.vol_plus.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    self.volume = min(1.0, self.volume + 0.1)
                    if self.audio:
                        self.audio.set_music_volume(self.volume)

                elif self.fs_rect.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    self.fullscreen = not self.fullscreen
                    self._apply_fullscreen()
                    self.save_settings()  # lưu luôn trạng thái mới