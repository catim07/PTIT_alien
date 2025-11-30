# src/menu_pause.py
import pygame
from font_helper import get_font


class PauseMenu:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.stats = ai_game.stats
        self.font = get_font(48)
        self.title_font = get_font(60)

        self.resume_button = pygame.Rect(0, 0, 220, 60)
        self.settings_button = pygame.Rect(0, 0, 220, 60)
        self.exit_button = pygame.Rect(0, 0, 220, 60)

        self.update_positions()
        self.hovered = None

    def update_positions(self):
        center_x = self.screen.get_width() // 2
        self.resume_button.center = (center_x, 240)
        self.settings_button.center = (center_x, 330)
        self.exit_button.center = (center_x, 420)

    def draw(self):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((30, 30, 30))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("TẠM DỪNG", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.screen.get_width() // 2, 150)))

        self._draw_button(self.resume_button, "Tiếp tục", (0, 255, 0), (0, 200, 0))
        self._draw_button(self.settings_button, "Cài đặt", (0, 200, 200), (0, 150, 150))
        self._draw_button(self.exit_button, "Thoát trận", (200, 50, 50), (150, 30, 30))

    def _draw_button(self, rect, text, color, hover_color):
        is_hovered = self.hovered == rect
        current_color = hover_color if is_hovered else color
        pygame.draw.rect(self.screen, current_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=8)
        text_surf = self.font.render(text, True, (0, 0, 0) if current_color[0] > 100 else (255, 255, 255))
        self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = None
        for btn in [self.resume_button, self.settings_button, self.exit_button]:
            if btn.collidepoint(mouse_pos):
                self.hovered = btn
                break

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.resume_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("hit")
                    self.stats.show_pause_menu = False
                    self.stats.paused = False  # ĐÃ CÓ → TỐT!
                elif self.settings_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("hit")
                    self.stats.show_settings = True
                    self.stats.show_pause_menu = False
                    self.stats.paused = False  # THÊM DÒNG NÀY → ĐẢM BẢO KHÔNG PAUSE KHI VÀO CÀI ĐẶT
                elif self.exit_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("ship_hit")
                    self.stats.game_active = False
                    self.stats.in_level_select = True
                    self.stats.show_pause_menu = False
                    self.stats.paused = False  # THÊM DÒNG NÀY → THOÁT TRẬN, KHÔNG PAUSE
                    return "exit_to_menu"
        return None