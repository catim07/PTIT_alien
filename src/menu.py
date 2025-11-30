# src/menu.py
"""
ALIEN INVASION - MAIN MENU (ULTRA EDITION + FULLSCREEN BACKGROUND + CREDIT + ÂM THANH HOÀN HẢO)
ĐÃ FIX HOÀN TOÀN TẤT CẢ LỖI!
"""
import sys
import pygame
import random
from pathlib import Path
from font_helper import get_font


class Menu:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        
        # Không scale ở đây → để AlienInvasion quản lý
        self.bg_image = None
        
        # Fonts
        self.font = get_font(48)
        self.title_font = get_font(78)
        
        # Nút chính
        self.play_button = pygame.Rect(0, 0, 300, 70)
        self.settings_button = pygame.Rect(0, 0, 300, 70)
        self.ship_select_button = pygame.Rect(0, 0, 300, 70)
        self.exit_button = pygame.Rect(0, 0, 300, 70)
        self.info_button = pygame.Rect(0, 0, 66, 66)
        
        self._update_button_positions()
        self.hovered = None

    def _update_button_positions(self):
        cx = self.screen_rect.centerx
        y = 260
        s = 100
        self.play_button.center = (cx, y)
        self.settings_button.center = (cx, y + s)
        self.ship_select_button.center = (cx, y + s * 2)
        self.exit_button.center = (cx, y + s * 3)
        self.info_button.bottomright = (self.screen_rect.width - 35, self.screen_rect.height - 35)

    def draw(self):
        # BACKGROUND MENU – FULL MÀN HÌNH
                # BACKGROUND MENU HOÀI CỔ + HIỆN ĐẠI (2 lớp ảnh chồng lên nhau)
        
        # 1. ẢNH MENU CŨ – HIỆN MỜ MỜ NHƯ KÝ ỨC (nếu có trong alien_invasion_main.py)
                # === VẼ ẢNH NỀN MENU MỚI TRƯỚC (menu_bg.png) – HIỆN RÕ RÀNG, ĐẸP NHẤT ===
        if hasattr(self.ai_game, 'menu_bg_scaled') and self.ai_game.menu_bg_scaled:
            self.screen.blit(self.ai_game.menu_bg_scaled, (0, 0))

        # === VẼ ẢNH MENU CŨ HOÀI CỔ MỜ MỜ PHÍA SAU (nếu có) ===
        if hasattr(self.ai_game, 'menu_bg_old_scaled') and self.ai_game.menu_bg_old_scaled:
            old_bg = self.ai_game.menu_bg_old_scaled.copy()
            old_bg.set_alpha(70)  # mờ nhẹ hơn để không che ảnh mới
            self.screen.blit(old_bg, (0, 0))

        # === LỚP TỐI NHẸ ĐỂ CHỮ + NÚT NỔI BẬT TRÊN MỌI ẢNH NỀN ===
        overlay = pygame.Surface((self.screen_rect.width, self.screen_rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))  # đen trong suốt ~30%
        self.screen.blit(overlay, (0, 0))
        # → XÓA HOÀN TOÀN _draw_gradient_bg() – KHÔNG BAO GIỜ HIỆN TUYẾT NỮA!
        

        self._draw_title()
        self._draw_button(self.play_button, "CHƠI NGAY", (0, 180, 80), hover=(0, 255, 100))
        self._draw_button(self.settings_button, "CÀI ĐẶT", (60, 100, 255), hover=(100, 150, 255))
        self._draw_button(self.ship_select_button, "TÊN LỬA", (255, 160, 0), hover=(255, 200, 50))
        self._draw_button(self.exit_button, "THOÁT", (200, 50, 50), hover=(255, 80, 80))
        self._draw_info_button()

        if getattr(self.ai_game, "show_credits", False):
            self._draw_credits_overlay()

    def _draw_title(self):
        text = "ALIEN INVASION"
        shadow = self.title_font.render(text, True, (0, 0, 0))
        title = self.title_font.render(text, True, (100, 200, 255))
        glow = self.title_font.render(text, True, (180, 240, 255))
        r = title.get_rect(center=(self.screen_rect.centerx, 130))
        self.screen.blit(glow, (r.x - 3, r.y - 3))
        self.screen.blit(shadow, (r.x + 4, r.y + 4))
        self.screen.blit(title, r)

    def _draw_button(self, rect, text, color, hover=None):
        is_hovered = self.hovered == rect
        col = hover if is_hovered and hover else color
        pygame.draw.rect(self.screen, col, rect, border_radius=16)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 4, border_radius=16)
        t = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(t, t.get_rect(center=rect.center))
        if is_hovered:
            p = pygame.Surface((rect.width + 30, rect.height + 30), pygame.SRCALPHA)
            p.fill((255, 255, 255, 50))
            self.screen.blit(p, (rect.centerx - p.get_width()//2, rect.centery - p.get_height()//2))

    def _draw_info_button(self):
        center = self.info_button.center
        hovered = self.info_button.collidepoint(pygame.mouse.get_pos())
        pygame.draw.circle(self.screen, (60, 60, 100), center, 33)
        pygame.draw.circle(self.screen, (120, 180, 255) if hovered else (90, 130, 220), center, 33, 6)
        text = get_font(52).render("i", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=center))
        if hovered:
            glow = pygame.Surface((100, 100), pygame.SRCALPHA)
            glow.fill((120, 180, 255, 80))
            self.screen.blit(glow, glow.get_rect(center=center))

    def _draw_gradient_bg(self):
        """Nền gradient vũ trụ + sao lấp lánh"""
        for y in range(self.screen_rect.height):
            ratio = y / self.screen_rect.height
            r = int(5 + ratio * 30)
            g = int(5 + ratio * 20)
            b = int(40 + ratio * 100)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.screen_rect.width, y))
        # Thêm sao
        for _ in range(100):
            x = random.randint(0, self.screen_rect.width)
            y = random.randint(0, self.screen_rect.height // 2)
            size = random.choice([1, 1, 2])
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), size)

    def _draw_credits_overlay(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(0, 0, 920, 640)
        box.center = self.screen_rect.center
        pygame.draw.rect(self.screen, (12, 18, 55), box, border_radius=35)
        pygame.draw.rect(self.screen, (80, 160, 255), box, 12, border_radius=35)

        title = get_font(60).render("THÔNG TIN & HƯỚNG DẪN", True, (255, 230, 100))
        self.screen.blit(title, title.get_rect(center=(box.centerx, box.top + 75)))

        content = [
            "ALIEN INVASION – ULTRA ROCKET EDITION 2025", "",
            "CÁCH CHƠI",
            "← → hoặc A D          Di chuyển tàu tên lửa",
            "SPACE                 Bắn laser",
            "ESC                   Tạm dừng / Menu",
            "F3                    Debug hitbox", "",
            "ẢI CHƠI", "Ải 1–2: Địch bay lưới", "Ải 3: Địch bay random", "Ải 4: BOSS CUỐI siêu khó!", "",
            "TÍNH NĂNG", "• 5 skin tàu cực đẹp", "• Hiệu ứng nổ + lửa", "• Âm thanh chất", "• Lưu game tự động", "",
            "TÁC GIẢ", "LÊ THANH CƯỜNG", "Mã sinh viên: N24DTCN009 – PTIT HCM", "Tiến Phúc", "Mã sinh viên: N24DTCN009 – PTIT HCM", "",
            "Cảm ơn thầy cô và các bạn đã chơi thử!", "Phiên bản 1.0 – 11/2025", "", "", "", "", "", "", "", "", "", "", ""
        ]

        if not hasattr(self.ai_game, "credit_scroll"):
            self.ai_game.credit_scroll = 0
        scroll = self.ai_game.credit_scroll
        max_scroll = 1300
        self.ai_game.credit_scroll = max(0, min(scroll, max_scroll))

        self.screen.set_clip(pygame.Rect(box.x + 40, box.y + 140, 840, 460))
        y = box.y + 140 - scroll

        for line in content:
            if line == "":
                y += 30
                continue
            color = (255, 220, 100) if any(x in line for x in ["CÁCH CHƠI","ẢI CHƠI","TÍNH NĂNG","TÁC GIẢ"]) else (200, 230, 255)
            size = 46 if "CÁCH CHƠI" in line or "TÁC GIẢ" in line else 38
            text = get_font(size).render(line, True, color)
            self.screen.blit(text, text.get_rect(centerx=box.centerx, y=y))
            y += 52

        self.screen.set_clip(None)

        # Thanh cuộn
        pygame.draw.rect(self.screen, (60, 60, 100), (box.right - 40, box.top + 140, 16, 460), border_radius=8)
        h = max(60, 460 // 3)
        ty = box.top + 140 + (scroll / max_scroll) * (460 - h)
        pygame.draw.rect(self.screen, (120, 180, 255), (box.right - 37, ty, 10, h), border_radius=5)

        # Nút X
        pygame.draw.circle(self.screen, (220, 50, 50), (box.right - 60, box.top + 60), 35)
        pygame.draw.circle(self.screen, (255, 100, 100), (box.right - 60, box.top + 55), 35, 8)
        self.screen.blit(get_font(52).render("X", True, (255,255,255)), (box.right - 75, box.top + 17))

    def handle_events(self, events=None):
        if events is None:
            events = pygame.event.get()

        if getattr(self.ai_game, "show_credits", False):
            mouse_pos = pygame.mouse.get_pos()
            box = pygame.Rect(0, 0, 920, 640)
            box.center = self.screen_rect.center
            close_rect = pygame.Rect(box.right - 130, box.top + 25, 100, 80)

            for event in events:
                if event.type == pygame.MOUSEWHEEL and box.collidepoint(mouse_pos):
                    self.ai_game.credit_scroll -= event.y * 70
                    self.ai_game.credit_scroll = max(0, min(self.ai_game.credit_scroll, 1300))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if close_rect.collidepoint(mouse_pos) or not box.collidepoint(mouse_pos):
                        self.ai_game.show_credits = False
                        self.ai_game.credit_scroll = 0
                        self.ai_game.play_sound("selectButton")
            return

        mouse_pos = pygame.mouse.get_pos()
        self.hovered = None
        for btn in [self.play_button, self.settings_button, self.ship_select_button, self.exit_button, self.info_button]:
            if btn.collidepoint(mouse_pos):
                self.hovered = btn
                break

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.play_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    self.ai_game.stats.in_level_select = True
                elif self.settings_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    self.ai_game.stats.show_settings = True
                elif self.ship_select_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    self.ai_game.show_ship_selection = True
                elif self.exit_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    pygame.quit()
                    sys.exit()
                elif self.info_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")
                    self.ai_game.show_credits = True
                    self.ai_game.credit_scroll = 0

    def resize(self):
        self.screen = self.ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self._update_button_positions()
        if hasattr(self.ai_game, 'menu_bg_original') and self.ai_game.menu_bg_original:
            w, h = self.screen.get_width(), self.screen.get_height()
            self.ai_game.menu_bg_scaled = pygame.transform.smoothscale(self.ai_game.menu_bg_original, (w, h))