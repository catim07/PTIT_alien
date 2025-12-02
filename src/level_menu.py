# src/level_menu.py
"""
ALIEN INVASION - LEVEL SELECT MENU (ẢNH NỀN TỪ FILE)
Tính năng:
- Dùng ảnh nền từ file (assets/bg/level_menu_bg.jpg)
- Tự động scale full màn hình
- Overlay tối nhẹ (để chữ đọc rõ)
- Giữ tất cả hiệu ứng: hover, sparkle, alien preview...
"""
import os
import sys
import pygame
import random
import math
from pathlib import Path
from font_helper import get_font
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class LevelMenu:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.stats = ai_game.stats
        self.save_data = ai_game.stats.save_data
        self.audio = ai_game.audio_manager
        
        # Fonts
        self.font = get_font(42)
        self.title_font = get_font(76)
        self.small_font = get_font(28)
        
        # Level data
        self.levels = [
            {"id": 1, "name": "Ải 1: Bắt đầu", "color": (50, 200, 120), "desc": "Dễ - alien dịu"},
            {"id": 2, "name": "Ải 2: Sóng lớn", "color": (100, 150, 255), "desc": "Trung bình - alien giận"},
            {"id": 3, "name": "Ải 3: Boss cuối", "color": (200, 50, 50), "desc": "Khó - 25 Alien cuồng"},
            {"id": 4, "name": "Ải 4: Hủy diệt", "color": (180, 0, 180), "desc": "Cực khó - alien nộ"},
        ]
        
        # UI elements
        self.buttons = []
        self.previews = []
        self.particles = []
        self.hovered = None
        self._create_ui()
        
        # Back button
        self.back_button = pygame.Rect(0, 0, 200, 55)
        self.back_button.bottomleft = (40, self.screen_rect.height - 40)

        # === LOAD ẢNH NỀN TỪ FILE ===
        self.bg_image = self._load_background_image()
        self.bg_scaled = None
        self._scale_background()

    def _load_background_image(self):
        """Tải ảnh nền từ file – CHẠY NGON CẢ .EXE"""
        import os
        
        # Danh sách các tên file có thể có
        possible_names = [
            "level_menu_bg.jpg", "level_menu_bg.png",
            "level_select_bg.jpg", "menu_level.jpg",
            "bg_level.jpg", "level_bg.jpg"
        ]
        
        # Thử tìm trong src/backgrounds trước
        for name in possible_names:
            path = resource_path(os.path.join("src", "backgrounds", name))
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert()
                    print(f"ĐÃ TẢI ẢNH NỀN MENU CHỌN ẢI: {path}")
                    return img
                except Exception as e:
                    print(f"Lỗi tải {name}: {e}")
        
        print("Không tìm thấy ảnh nền menu chọn ải → dùng gradient")
        return None

    def _scale_background(self):
        """Scale ảnh nền theo kích thước màn hình"""
        if self.bg_image:
            self.bg_scaled = pygame.transform.smoothscale(self.bg_image, (self.screen_rect.width, self.screen_rect.height))
        else:
            self.bg_scaled = None

    def _create_ui(self):
        self.buttons = []
        self.previews = []
        start_y = 220
        spacing = 100
        for i, level in enumerate(self.levels):
            btn = pygame.Rect(0, 0, 380, 80)
            btn.centerx = self.screen_rect.centerx
            btn.y = start_y + i * spacing
            self.buttons.append(btn)
            
            preview = {
                "rect": pygame.Rect(0, 0, 45, 35),
                "color": level["color"],
                "hp": 3 if level["id"] > 1 else 1,
                "level": level["id"]
            }
            preview["rect"].midleft = (btn.left + 50, btn.centery)
            self.previews.append(preview)

    def draw(self):
        # === VẼ ẢNH NỀN TỪ FILE ===
        self._draw_custom_bg()
        
        # Title
        self._draw_title()
        
        # Level buttons
        for i, (btn, level, preview) in enumerate(zip(self.buttons, self.levels, self.previews)):
            is_unlocked = level["id"] in self.save_data['unlocked_levels']
            is_hovered = self.hovered == i
            
            self._draw_level_button(btn, level, is_unlocked, is_hovered)
            self._draw_alien_preview(preview, is_unlocked)
            
            if is_unlocked and level["id"] > 1 and random.random() < 0.05:
                self._spawn_sparkle(btn.center)
        
        # Particles
        self._update_particles()
        self._draw_particles()
        
        # Back button
        self._draw_back_button()

    def _draw_custom_bg(self):
        if self.bg_scaled:
            self.screen.blit(self.bg_scaled, (0, 0))
            # Overlay tối nhẹ để chữ dễ đọc
            overlay = pygame.Surface((self.screen_rect.width, self.screen_rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 90))
            self.screen.blit(overlay, (0, 0))
        else:
            # Vẽ gradient nếu không có ảnh
            for y in range(self.screen_rect.height):
                ratio = y / self.screen_rect.height
                r = int(10 + ratio * 40)
                g = int(15 + ratio * 55)
                b = int(30 + ratio * 80)
                pygame.draw.line(self.screen, (r, g, b), (0, y), (self.screen_rect.width, y))

    def _draw_title(self):
        text = "CHỌN ẢI"
        shadow = self.title_font.render(text, True, (0, 0, 0))
        title = self.title_font.render(text, True, (120, 200, 255))
        rect = title.get_rect(center=(self.screen_rect.centerx, 100))
        self.screen.blit(shadow, (rect.x + 4, rect.y + 4))
        self.screen.blit(title, rect)

    def _draw_level_button(self, btn, level, unlocked, hovered):
        base_color = level["color"]
        color = tuple(min(255, c + 60) for c in base_color) if hovered else base_color
        if not unlocked:
            color = (80, 80, 80)
        
        pygame.draw.rect(self.screen, color, btn, border_radius=16)
        pygame.draw.rect(self.screen, (255, 255, 255), btn, 3, border_radius=16)
        
        if not unlocked:
            lock_overlay = pygame.Surface((btn.width, btn.height), pygame.SRCALPHA)
            lock_overlay.fill((0, 0, 0, 120))
            self.screen.blit(lock_overlay, btn)
        
        name_text = self.font.render(level["name"], True, (255, 255, 255) if unlocked else (180, 180, 180))
        desc_text = self.small_font.render(level["desc"], True, (200, 200, 200) if unlocked else (120, 120, 120))
        
        self.screen.blit(name_text, name_text.get_rect(midleft=(btn.left + 110, btn.centery - 15)))
        self.screen.blit(desc_text, desc_text.get_rect(midleft=(btn.left + 110, btn.centery + 15)))
        
        if not unlocked:
            lock = self.font.render("LOCK", True, (255, 255, 0))
            self.screen.blit(lock, lock.get_rect(center=(btn.right - 50, btn.centery)))
        
        if hovered and unlocked:
            pulse = pygame.Surface((btn.width + 30, btn.height + 30), pygame.SRCALPHA)
            pulse.fill((255, 255, 255, 50))
            self.screen.blit(pulse, (btn.centerx - pulse.get_width()//2, btn.centery - pulse.get_height()//2))

    def _draw_alien_preview(self, preview, unlocked):
        if not unlocked:
            return
            
        pygame.draw.ellipse(self.screen, preview["color"], preview["rect"])
        pygame.draw.rect(self.screen, preview["color"], preview["rect"], border_radius=8)
        
        eye_y = preview["rect"].top + 10
        pygame.draw.circle(self.screen, (255, 255, 255), (preview["rect"].centerx - 10, eye_y), 5)
        pygame.draw.circle(self.screen, (255, 255, 255), (preview["rect"].centerx + 10, eye_y), 5)
        pygame.draw.circle(self.screen, (0, 0, 0), (preview["rect"].centerx - 10, eye_y), 2)
        pygame.draw.circle(self.screen, (0, 0, 0), (preview["rect"].centerx + 10, eye_y), 2)
        
        max_hp = 3 + (preview["level"] - 1) * 2
        bar_width, bar_height = 40, 6
        bar_x = preview["rect"].centerx - bar_width // 2
        bar_y = preview["rect"].bottom + 8
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=2)
        fill = int(bar_width * preview["hp"] / max_hp)
        color = (0, 255, 0) if fill > bar_width * 0.6 else (255, 255, 0) if fill > bar_width * 0.3 else (255, 0, 0)
        pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill, bar_height), border_radius=2)

    def _spawn_sparkle(self, pos):
        for _ in range(8):
            self.particles.append({
                "pos": [pos[0], pos[1]],
                "vel": [random.uniform(-3, 3), random.uniform(-5, -1)],
                "life": random.randint(20, 40),
                "color": (255, 255, random.randint(100, 200))
            })

    def _update_particles(self):
        for p in self.particles[:]:
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["vel"][1] += 0.2
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def _draw_particles(self):
        for p in self.particles:
            alpha = int(255 * p["life"] / 40)
            color = (*p["color"][:3], alpha)
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (3, 3), 3)
            self.screen.blit(s, (p["pos"][0] - 3, p["pos"][1] - 3))

    def _draw_back_button(self):
        mouse_pos = pygame.mouse.get_pos()
        color = (220, 70, 70) if self.back_button.collidepoint(mouse_pos) else (200, 50, 50)
        pygame.draw.rect(self.screen, color, self.back_button, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button, 3, border_radius=12)
        text = self.font.render("QUAY LẠI", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=self.back_button.center))

    def handle_events(self, events=None):
        if events is None:
            events = pygame.event.get()
            
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = None
        
        for i, btn in enumerate(self.buttons):
            if btn.collidepoint(mouse_pos):
                self.hovered = i
                break
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_button.collidepoint(mouse_pos):
                    self.ai_game.play_sound("selectButton")   # Tiếng "tách" khi bấm Quay Lại
                    self.stats.in_level_select = False
                    return None

                for i, btn in enumerate(self.buttons):
                    if btn.collidepoint(mouse_pos):
                        level_id = self.levels[i]["id"]
                        if level_id in self.save_data['unlocked_levels']:
                            self.ai_game.play_sound("selectButton")   # Tiếng "tách" khi chọn ải được mở
                            return level_id
                        else:
                            self.ai_game.play_sound("ship_hit")       # Giữ nguyên tiếng "bốp" khi bấm ải bị khóa
                            # Có thể thêm hiệu ứng rung nhẹ sau nếu muốn
        
        return None

    def resize(self):
        """Cập nhật khi thay đổi kích thước cửa sổ"""
        self.screen_rect = self.screen.get_rect()
        self._create_ui()
        self.back_button.bottomleft = (40, self.screen_rect.height - 40)
        self._scale_background()