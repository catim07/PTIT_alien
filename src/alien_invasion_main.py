# src/alien_invasion_main.py
import sys
import os
import pygame
from pygame.sprite import Sprite, Group
from dataclasses import dataclass
import json
import random
import math
from pathlib import Path

# Nhập các module
try:
    from menu_pause import PauseMenu
    from level_menu import LevelMenu
    from settings_menu import SettingsMenu
    from save_manager import SaveManager
    from menu import Menu
    from audio_manager import AudioManager
except ImportError as e:
    print(f"Lỗi nhập: {e}")
    print("Vui lòng đảm bảo tất cả các module menu đã có sẵn!")
    sys.exit(1)

# ================== CẤU HÌNH SCREEN & FONT ==================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

from font_helper import get_font

# ================== CẤU HÌNH LEVEL ==================
@dataclass
class LevelConfig:
    alien_speed: float
    fleet_drop_speed: int
    bullet_allowed: int
    alien_points: int
    alien_count: int
    shoot_chance: float

LEVEL_CONFIGS = {
    1: LevelConfig(0.6, 8, 5, 50, 1, 0.0003),
    2: LevelConfig(1.2, 12, 7, 100, 1, 0.0010),
    3: LevelConfig(1.8, 18, 10, 200, 25, 0.0020),
    4: LevelConfig(3.0, 30, 15, 500, 30, 0.0040),
}

# ================== SETTINGS CLASS ==================
class Settings:
    def __init__(self):
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.bg_color = (20, 25, 35)
        self.ship_speed = 6.0
        self.bullet_width = 4
        self.bullet_height = 18
        self.bullet_speed = 8.5
        self.fleet_direction = 1
        self.alien_speed = 0.6
        self.fleet_drop_speed = 8
        self.bullet_allowed = 5
        self.alien_points = 50
        self.ship_skin = 0                    
        self.ship_skins = [f"roket_{i}" for i in range(5)]

# ================== GAME STATS ==================
class GameStats:
    def __init__(self):
        self.save_data = SaveManager.load()
        # Mở tất cả các ải từ đầu
        self.save_data['unlocked_levels'] = [1, 2, 3, 4]
        self.reset_stats()
        self.game_active = False
        self.in_level_select = False
        self.show_pause_menu = False
        self.show_settings = False
        self.show_level_complete = False
        self.show_game_over = False
        self.paused = False
        self.completed_level = 0
        self.boss_active = False
        self.last_level = 0
        
    def reset_stats(self):
        self.ships_left = 3
        self.score = 0
        self.current_level = 1
        self.level_score = 0
        self.completed_level = 0
        self.boss_active = False

    def unlock_next_level(self):
        next_level = self.current_level + 1
        if next_level <= len(LEVEL_CONFIGS) and next_level not in self.save_data['unlocked_levels']:
            self.save_data['unlocked_levels'].append(next_level)
            SaveManager.save(self.save_data['unlocked_levels'], self.save_data['high_score'])

    def update_high_score(self):
        # Luôn lưu điểm hiện tại (cho cả trường hợp score = 0 khi reset)
        if self.score >= self.save_data['high_score']:
            self.save_data['high_score'] = self.score
        SaveManager.save(self.save_data['unlocked_levels'], self.save_data['high_score'])

# ================== SHIP – ẢNH + HITBOX CHÍNH XÁC 100% ==================
class Ship(Sprite):
    def __init__(self, ai_game):
        super().__init__()
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.screen_rect = ai_game.screen.get_rect()

        # TẢI ẢNH
        self.original_image = self._load_ship_image()
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.screen_rect.midbottom

                # ====== HITBOX TÀU ROCKET – CHỈNH SIÊU SÁT + CỰC MƯỢT ======
        # Giá trị càng lớn → hitbox càng nhỏ (dễ né hơn)
        self.hitbox_inset_x = 27  # Thu nhỏ ngang (cánh rocket)
        self.hitbox_inset_y = 5  # Thu nhỏ dọc (đầu + đuôi)

        self.hitbox = self.rect.inflate(
            -self.hitbox_inset_x * 2,   # nhỏ 36px theo chiều ngang
            -self.hitbox_inset_y * 2    # nhỏ 24px theo chiều dọc
        )
        self.hitbox.midbottom = self.rect.midbottom  # Vẫn giữ đúng vị trí đáy tàu

        self.x = float(self.rect.x)
        self.moving_right = False
        self.moving_left = False

    def _load_ship_image(self):
        """Tải ảnh tàu theo skin đã chọn (roket_0.png → roket_4.png)"""
        skin_name = self.settings.ship_skins[self.settings.ship_skin]
        ship_path = Path(f"src/backgrounds/{skin_name}.png")
        
        if not ship_path.exists():
            print(f"Không tìm thấy skin: {skin_name}.png → dùng roket_0.png")
            ship_path = Path("src/backgrounds/roket_0.png")
        
        if not ship_path.exists():
            print("Không có skin nào → vẽ hình thay thế")
            surf = pygame.Surface((90, 68), pygame.SRCALPHA)
            pygame.draw.polygon(surf, (100, 180, 255), [(45,0), (85,68), (45,50), (5,68)])
            return surf
        
        try:
            img = pygame.image.load(ship_path).convert_alpha()
            return pygame.transform.smoothscale(img, (90, 68))
        except Exception as e:
            print(f"Lỗi tải skin {skin_name}: {e}")
            surf = pygame.Surface((90, 68), pygame.SRCALPHA)
            pygame.draw.polygon(surf, (255, 100, 100), [(45,0), (85,68), (45,50), (5,68)])
            return surf

    def update(self):
        if self.moving_right and self.rect.right < self.screen_rect.right:
            self.x += self.settings.ship_speed
        if self.moving_left and self.rect.left > 0:
            self.x -= self.settings.ship_speed
        self.rect.x = int(self.x)
        self.hitbox.midbottom = self.rect.midbottom  # Cập nhật hitbox theo rect

    def draw(self):
        self.screen.blit(self.image, self.rect)

    def center_ship(self):
        self.rect.centerx = self.screen_rect.centerx
        self.x = float(self.rect.x)
        self.hitbox.midbottom = self.rect.midbottom

    def get_hitbox(self):
        return self.hitbox

# ================== BULLET ==================
class Bullet(Sprite):
    def __init__(self, ai_game, start_pos, color, speed, width=6, height=20, trail=True, spiral=False):
        super().__init__()
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.color = color
        self.speed = speed
        self.width = width
        self.height = height
        self.trail = trail
        self.spiral = spiral
        self.phase = 0
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = start_pos
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.trail_age = 0

    def update(self):
        if self.spiral:
            self.phase += 0.3
            self.x += math.cos(self.phase) * 3
            self.y += self.speed
        else:
            self.y += self.speed
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.trail_age += 1

    def draw(self):
        pygame.draw.rect(self.screen, self.color, self.rect, border_radius=3)
        if self.trail and self.trail_age < 12:
            trail_alpha = 120 - self.trail_age * 10
            trail_rect = self.rect.copy()
            trail_rect.y -= 6
            trail_rect.height += 4
            s = pygame.Surface((trail_rect.width, trail_rect.height), pygame.SRCALPHA)
            s.fill((*self.color, trail_alpha))
            self.screen.blit(s, trail_rect)

# ================== ALIEN ==================
class Alien(Sprite):
    def __init__(self, ai_game, x: int, y: int, random_alien=False):
        super().__init__()
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.width = 45
        self.height = 35
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.random_alien = random_alien
        
        level = ai_game.stats.current_level
        config = LEVEL_CONFIGS[level]
        self.max_hp = 1 if level == 1 else 3 + (level - 2) * 2
        if level == 4: self.max_hp = 8
        self.hp = self.max_hp
        self.shoot_chance = config.shoot_chance
        self.points = config.alien_points
        
        if level == 1:
            self.color = (150, 80, 220)
            self.eye_color = (255, 200, 255)
        else:
            self.color = (random.randint(100, 255), random.randint(40, 120), random.randint(100, 220))
            self.eye_color = (255, 255 - level * 30, 255 - level * 30)
        
        self.last_shot = 0
        self.shoot_delay = 2200 - level * 220

    def update(self):
        if self.random_alien:
            if not hasattr(self, 'initialized'):
                self.x = float(self.rect.x)
                self.y = float(self.rect.y)
                self.move_dir_x = random.choice([-1, 1])
                self.move_speed_x = random.uniform(2.5, 5.2) if self.ai_game.stats.current_level == 4 else random.uniform(2.0, 4.0)
                self.move_dir_y = random.choice([-1, 1])
                self.move_speed_y = random.uniform(1.5, 3.0) if self.ai_game.stats.current_level == 4 else random.uniform(1.2, 2.5)
                self.change_timer = random.randint(40, 120)
                self.y_amplitude = random.uniform(60, 150)
                self.y_center = self.y
                self.phase = random.uniform(0, 6.28)
                self.initialized = True

            self.x += self.move_dir_x * self.move_speed_x
            if self.x <= 0 or self.x >= self.ai_game.settings.screen_width - self.width:
                self.move_dir_x *= -1
                self.x = max(0, min(self.x, self.ai_game.settings.screen_width - self.width))

            self.phase += 0.08
            self.y_center += self.move_dir_y * self.move_speed_y
            self.y_center = max(100, min(self.y_center, 520))
            wave_offset = self.y_amplitude * math.sin(self.phase)
            self.y = self.y_center + wave_offset

            self.change_timer -= 1
            if self.change_timer <= 0:
                self.move_dir_x *= -1
                self.move_speed_x = random.uniform(2.0, 5.5)
                self.move_dir_y *= -1
                self.move_speed_y = random.uniform(1.0, 3.2)
                self.change_timer = random.randint(40, 120)

            self.rect.x = int(self.x)
            self.rect.y = int(self.y)

        else:
            if self.ai_game.fleet_direction_cooldown <= 0:
                delta = self.settings.alien_speed * self.settings.fleet_direction
                self.rect.x += delta

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            bullet = Bullet(self.ai_game, self.rect.midbottom, (255, 80, 80), 5.5, width=4, height=18)
            self.ai_game.enemy_bullets.add(bullet)
            self.ai_game.play_sound("shoot")
            self.last_shot = now

    def take_damage(self, damage=1):
        self.hp -= damage
        self.ai_game.play_sound("hit")
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def draw(self):
        pygame.draw.ellipse(self.screen, self.color, self.rect)
        pygame.draw.rect(self.screen, self.color, self.rect, border_radius=8)
        eye_y = self.rect.top + 10
        pygame.draw.circle(self.screen, self.eye_color, (self.rect.centerx - 10, eye_y), 5)
        pygame.draw.circle(self.screen, self.eye_color, (self.rect.centerx + 10, eye_y), 5)
        pygame.draw.circle(self.screen, (0, 0, 0), (self.rect.centerx - 10, eye_y), 2)
        pygame.draw.circle(self.screen, (0, 0, 0), (self.rect.centerx + 10, eye_y), 2)
        if self.hp < self.max_hp:
            bar_width, bar_height = 35, 5
            bar_x = self.rect.centerx - bar_width // 2
            bar_y = self.rect.top - 10
            pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=2)
            fill_width = int((bar_width * self.hp) / self.max_hp)
            color = (0, 255, 0) if self.hp / self.max_hp > 0.6 else (255, 255, 0) if self.hp / self.max_hp > 0.3 else (255, 0, 0)
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_width, bar_height), border_radius=2)

# ================== BOSS ==================
class Boss(Sprite):
    def __init__(self, ai_game):
        super().__init__()
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        
        self.width = 260
        self.height = 180
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.centerx = self.screen.get_width() // 2
        self.rect.top = 20
        
        self.max_hp = 350
        self.hp = self.max_hp
        self.phase = 1
        self.color = (200, 0, 50)
        
        self.move_speed = 4.2
        self.direction = 1
        self.last_shot = 0
        self.shoot_delay = 600  # Bắn cực nhanh
        self.show_credits = False
    def update(self):
        # Di chuyển nhanh + nảy tường khi chạm biên
        self.rect.x += self.direction * self.move_speed
        if self.rect.left <= 0 or self.rect.right >= self.settings.screen_width:
            self.direction *= -1

        # Chuyển phase 2 khi máu < 50%
        if self.hp <= self.max_hp * 0.5 and self.phase == 1:
            self.phase = 2
            self.color = (255, 0, 100)
            self.shoot_delay = 300  # Bắn nhanh gấp đôi
            self.ai_game.play_sound("level_up")

        self.shoot()

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot < self.shoot_delay:
            return
        self.last_shot = now

        cx = self.rect.centerx
        cy = self.rect.bottom

        # === ĐẠN ĐIÊN CUỒNG – KHÔNG THỂ NÉ ===
        if self.phase == 1:
            # 20 viên tròn xoay + bắn theo người chơi
            ship_x = self.ai_game.ship.rect.centerx
            for i in range(20):
                angle = math.radians(i * 18 + now // 20)
                dx = math.cos(angle) * 10
                dy = math.sin(angle) * 10
                bullet = Bullet(self.ai_game, (cx + dx*8, cy), (255, 80, 80), 7, width=9, height=22)
                self.ai_game.enemy_bullets.add(bullet)

            # 9 tia laser nhắm thẳng tàu
            for offset in range(-120, 130, 30):
                target_x = ship_x + offset + random.randint(-40, 40)
                dx = (target_x - cx) / 80
                bullet = Bullet(self.ai_game, (cx, cy), (255, 0, 150), 8, width=20, height=40, trail=True)
                bullet.x += dx * 10
                self.ai_game.enemy_bullets.add(bullet)

        else:  # PHASE 2: HỎA NGỤC THẬT SỰ
            # 32 viên xoáy liên tục
            for i in range(32):
                angle = math.radians(i * 11.25 + now // 15)
                dx = math.cos(angle) * 11
                dy = math.sin(angle) * 11
                b = Bullet(self.ai_game, (cx + dx*10, cy), (255, 0, 255), 9, width=10, height=26, spiral=True)
                self.ai_game.enemy_bullets.add(b)

            # Bắn 12 tia laser dày đặc + đạn xoáy chồng lên
            for offset in range(-150, 160, 25):
                bullet = Bullet(self.ai_game, (cx + offset, cy), (200, 0, 255), 9, width=22, height=50, trail=True)
                self.ai_game.enemy_bullets.add(bullet)
                spiral = Bullet(self.ai_game, (cx + offset, cy), (255, 100, 255), 8, spiral=True)
                self.ai_game.enemy_bullets.add(spiral)

        self.ai_game.play_sound("shoot")

    # === QUAN TRỌNG: THÊM HÀM take_damage ĐÃ BỊ THIẾU ===
    def take_damage(self, damage=1):
        self.hp -= damage
        self.ai_game.play_sound("hit")
        if self.hp <= 0:
            self.ai_game.boss_explosion()
            self.kill()
            return True
        return False

    def draw(self):
        # Boss to, đẹp, dữ
        pygame.draw.rect(self.screen, self.color, self.rect, border_radius=40)
        pygame.draw.rect(self.screen, (255, 80, 80), self.rect, 10, border_radius=40)
        
        # Mắt đỏ rực
        eye_y = self.rect.top + 60
        pygame.draw.circle(self.screen, (255, 0, 0), (self.rect.centerx - 60, eye_y), 30)
        pygame.draw.circle(self.screen, (255, 0, 0), (self.rect.centerx + 60, eye_y), 30)
        pygame.draw.circle(self.screen, (0, 0, 0), (self.rect.centerx - 60, eye_y), 12)
        pygame.draw.circle(self.screen, (0, 0, 0), (self.rect.centerx + 60, eye_y), 12)

        # Thanh máu + chữ BOSS rung
        bar_width = 900
        bar_x = (self.screen.get_width() - bar_width) // 2
        fill = int(bar_width * self.hp / self.max_hp)
        color = (0, 255, 0) if self.hp > self.max_hp*0.6 else (255, 255, 0) if self.hp > self.max_hp*0.3 else (255, 0, 0)
        pygame.draw.rect(self.screen, (40, 40, 40), (bar_x-6, 4, bar_width+12, 42), border_radius=20)
        pygame.draw.rect(self.screen, color, (bar_x, 10, fill, 30), border_radius=15)
        
        import random
        shake = 5 if self.phase == 2 else 0
        text = get_font(56).render("FINAL BOSS", True, (255, 0, 100))
        rect = text.get_rect(center=(self.screen.get_width()//2, 60))
        rect.x += random.randint(-shake, shake)
        rect.y += random.randint(-shake, shake)
        self.screen.blit(text, rect)

# ================== SCOREBOARD, MENU, ETC ==================
class Scoreboard:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        self.font = get_font(32)
        self.big_font = get_font(48)

    def show_score(self):
        score_str = f"Điểm: {self.stats.score:,}"
        level_str = f"Ải: {self.stats.current_level}"
        ships_str = f"Tàu: {self.stats.ships_left}"
        high_str = f"Cao nhất: {self.stats.save_data['high_score']:,}"

        self.screen.blit(self.font.render(score_str, True, (255, 255, 255)), (20, 15))
        self.screen.blit(self.font.render(level_str, True, (200, 220, 255)), (20, 55))
        self.screen.blit(self.font.render(ships_str, True, (200, 255, 200)), (20, 95))

        high_surf = self.font.render(high_str, True, (255, 215, 0))
        hw = high_surf.get_width()
        reserve = 20
        try:
            if hasattr(self.ai_game, 'menu_button') and self.ai_game.menu_button:
                reserve += self.ai_game.menu_button.rect.width + 10
        except Exception:
            pass
        x = max(20, self.screen.get_width() - hw - reserve)
        self.screen.blit(high_surf, (x, 15))

class MenuButton:
    def __init__(self, ai_game):
        self.screen = ai_game.screen
        self.stats = ai_game.stats
        self.font = get_font(26)
        self.rect = pygame.Rect(0, 0, 140, 40)
        self.rect.topright = (ai_game.screen.get_width() - 20, 20)
        self.hover = False

    def draw(self):
        try:
            self.rect.topright = (self.screen.get_width() - 20, 20)
        except Exception:
            pass

        try:
            mouse_pos = pygame.mouse.get_pos()
            self.hover = self.rect.collidepoint(mouse_pos)
        except Exception:
            pass

        color = (120, 180, 255) if not self.hover else (150, 200, 255)
        pygame.draw.rect(self.screen, color, self.rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.rect, 2, border_radius=8)
        text = self.font.render("MENU", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def handle_click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.stats.show_pause_menu = True
            return True
        return False

class LevelCompleteMenu:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.stats = ai_game.stats
        self.font = get_font(42)
        self.title_font = get_font(64)
        self.next_button = pygame.Rect(0, 0, 260, 70)
        self.menu_button = pygame.Rect(0, 0, 260, 70)
        self.update_button_positions()

    def update_button_positions(self):
        center_x = self.screen.get_width() // 2
        self.next_button.center = (center_x - 150, 420)
        self.menu_button.center = (center_x + 150, 420)

    def draw(self):
        # Không vẽ nền xanh nữa → để lộ ảnh youWin.jpg phía sau
        # (ảnh đã được vẽ bởi show_youwin_screen() trước đó)

        # === LỚP TỐI NHẸ ĐỂ CHỮ + NÚT NỔI BẬT TRÊN MỌI ẢNH NỀN ===
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))  # đen trong suốt 50%
        self.screen.blit(overlay, (0, 0))

        # === CHỮ HOÀN THÀNH ẢI ===
        title = self.title_font.render(f"HOÀN THÀNH ẢI {self.stats.completed_level}!", True, (255, 255, 100))
        shadow = self.title_font.render(f"HOÀN THÀNH ẢI {self.stats.completed_level}!", True, (0, 0, 0))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 220))
        # bóng đổ
        self.screen.blit(shadow, (title_rect.x + 5, title_rect.y + 5))
        self.screen.blit(title, title_rect)

        # === ĐIỂM THƯỞNG ===
        score_text = self.font.render(f"+{self.stats.level_score:,} ĐIỂM", True, (0, 255, 200))
        score_shadow = self.font.render(f"+{self.stats.level_score:,} ĐIỂM", True, (0, 0, 0))
        score_rect = score_text.get_rect(center=(self.screen.get_width() // 2, 320))
        self.screen.blit(score_shadow, (score_rect.x + 4, score_rect.y + 4))
        self.screen.blit(score_text, score_rect)

        # === NÚT ẢI TIẾP ===
        pygame.draw.rect(self.screen, (0, 200, 100), self.next_button, border_radius=16)
        pygame.draw.rect(self.screen, (255, 255, 255), self.next_button, 4, border_radius=16)
        next_text = self.font.render("ẢI TIẾP", True, (255, 255, 255))
        self.screen.blit(next_text, next_text.get_rect(center=self.next_button.center))

        # === NÚT MENU ===
        pygame.draw.rect(self.screen, (200, 60, 60), self.menu_button, border_radius=16)
        pygame.draw.rect(self.screen, (255, 255, 255), self.menu_button, 4, border_radius=16)
        menu_text = self.font.render("MENU", True, (255, 255, 255))
        self.screen.blit(menu_text, menu_text.get_rect(center=self.menu_button.center))

    def handle_click(self, mouse_pos):
        if self.next_button.collidepoint(mouse_pos):
            self.ai_game.play_sound("selectButton")
            next_level = self.stats.completed_level + 1
            if next_level in self.ai_game.stats.save_data['unlocked_levels']:
                self.ai_game.start_level(next_level)
            else:
                self.ai_game.stats.in_level_select = True
            self.ai_game.stats.show_level_complete = False
            return True
        elif self.menu_button.collidepoint(mouse_pos):
            self.ai_game.play_sound("selectButton")
            self.ai_game.stats.in_level_select = True
            self.ai_game.stats.show_level_complete = False
            return True
        return False

class GameOverMenu:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.stats = ai_game.stats
        self.font = get_font(64)
        self.small_font = get_font(42)
        self.button_font = get_font(36)
        self.retry_button = pygame.Rect(0, 0, 280, 70)
        self.menu_button = pygame.Rect(0, 0, 280, 70)
        self._update_button_positions()

    def _update_button_positions(self):
        center_x = self.screen.get_width() // 2
        self.retry_button.center = (center_x - 160, 420)
        self.menu_button.center = (center_x + 160, 420)

    def draw(self):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(230)
        overlay.fill((0, 0, 0))

        title = self.font.render("BẠN ĐÃ THUA!", True, (255, 80, 80))
        shadow = self.font.render("BẠN ĐÃ THUA!", True, (150, 0, 0))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(shadow, (title_rect.x + 4, title_rect.y + 4))
        self.screen.blit(title, title_rect)

        # Thay nguyên 2 dòng cũ bằng đoạn code dưới đây (thêm viền đen siêu đẹp + nổi bật)

        text = f"Điểm: {self.stats.score:,}"
        center_x = self.screen.get_width() // 2
        center_y = 300

# 1. Viền đen (outline) - blit nhiều lần offset
        outline = self.small_font.render(text, True, (0, 0, 0))  # MÀU ĐEN
        for dx in [-2, -1, 1, 2]:
            for dy in [-2, -1, 1, 2]:
                outline_rect = outline.get_rect(center=(center_x + dx, center_y + dy))
                self.screen.blit(outline, outline_rect)

# 2. Bóng đổ nhẹ (tùy chọn, làm chữ nổi 3D)
        shadow = self.small_font.render(text, True, (150, 150, 150))  # XÁM NHẸ
        shadow_rect = shadow.get_rect(center=(center_x + 2, center_y + 2))
        self.screen.blit(shadow, shadow_rect)

# 3. Chữ chính vàng sáng (đè lên trên)
        score_text = self.small_font.render(text, True, (255, 255, 100))
        score_rect = score_text.get_rect(center=(center_x, center_y))
        self.screen.blit(score_text, score_rect)

        mouse_pos = pygame.mouse.get_pos()
        retry_color = (0, 200, 100) if self.retry_button.collidepoint(mouse_pos) else (0, 180, 80)
        pygame.draw.rect(self.screen, retry_color, self.retry_button, border_radius=14)
        pygame.draw.rect(self.screen, (255, 255, 255), self.retry_button, 3, border_radius=14)
        retry_text = self.button_font.render("CHƠI LẠI", True, (255, 255, 255))
        self.screen.blit(retry_text, retry_text.get_rect(center=self.retry_button.center))

        menu_color = (200, 70, 70) if self.menu_button.collidepoint(mouse_pos) else (180, 50, 50)
        pygame.draw.rect(self.screen, menu_color, self.menu_button, border_radius=14)
        pygame.draw.rect(self.screen, (255, 255, 255), self.menu_button, 3, border_radius=14)
        menu_text = self.button_font.render("MENU ẢI", True, (255, 255, 255))
        self.screen.blit(menu_text, menu_text.get_rect(center=self.menu_button.center))

    def handle_click(self, mouse_pos):
        if self.retry_button.collidepoint(mouse_pos):
            self.ai_game.start_level(self.stats.current_level)
            self.ai_game.stats.show_game_over = False
            return True
        elif self.menu_button.collidepoint(mouse_pos):
            self.ai_game.stats.in_level_select = True
            self.ai_game.stats.show_game_over = False
            return True
        return False

# ================== GAME CORE ==================
class AlienInvasion:
    def __init__(self):
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("ALIEN INVASION - TÀU ROCKET SIÊU CHÍNH XÁC")
        self.clock = pygame.time.Clock()
        
        # Tải ảnh nền gameplay nếu có
        self.gameplay_bg_original = self._load_gameplay_bg()
        self.gameplay_bg = None
        self._resize_gameplay_bg()
                # ================== TẢI BACKGROUND MENU CHÍNH ==================
                # ================== TẢI BACKGROUND MENU CHÍNH + MENU CŨ HOÀI CỔ ==================
        try:
            menu_path = Path("src/backgrounds/menu_bg.png")
            if menu_path.exists():
                self.menu_bg_original = pygame.image.load(menu_path).convert()
                print(f"ĐÃ TẢI MENU BACKGROUND MỚI: {menu_path}")
            else:
                self.menu_bg_original = self.gameplay_bg_original or pygame.Surface((1200, 800))
                print("Không có menu_bg.png → dùng ảnh mặc định")
        except Exception as e:
            print(f"Lỗi tải menu_bg.png: {e}")
            self.menu_bg_original = self.gameplay_bg_original

        # === TẢI ẢNH MENU CŨ – HOÀI CỔ, KÝ ỨC TUỔI THƠ ===
        self.menu_bg_old_original = None
        old_paths = [
            "src/backgrounds/menu_bg.png",
            "src/backgrounds/menu_cu.jpg",
            "src/backgrounds/old_menu.png",
            "src/backgrounds/menu_classic.jpg",
            "src/backgrounds/menu_2005.jpg",
            "backgrounds/menu_old.jpg",
        ]
        for p in old_paths:
            path = Path(p)
            if path.exists():
                try:
                    self.menu_bg_old_original = pygame.image.load(path).convert()
                    print(f"ĐÃ TẢI ẢNH MENU CŨ HOÀI CỔ: {path}")
                    break
                except Exception as e:
                    print(f"Lỗi tải ảnh cũ {path}: {e}")
        else:
            print("Không tìm thấy ảnh menu cũ → chỉ dùng menu mới thôi nha!")
        self.resize_all_backgrounds()
        
        self.stats = GameStats()
        self.audio_manager = AudioManager(self)
        self.menu = Menu(self)
        self.level_menu = LevelMenu(self)
        self.pause_menu = PauseMenu(self)
        self.settings_menu = SettingsMenu(self)
        self.level_complete_menu = LevelCompleteMenu(self)
        self.game_over_menu = GameOverMenu(self)
        self.stats.show_game_over = False
        self.ship = Ship(self)
        self.bullets = Group()
        self.enemy_bullets = Group()
        self.aliens = Group()
        self.boss = None
        self.explosion_particles = []

        self.sb = Scoreboard(self)
        self.menu_button = MenuButton(self)

        self.sounds = {}
        self.load_sounds()
        self.fleet_direction_cooldown = 0
        self.last_shot_time = 0
        self.shoot_cooldown = 150
        self.boss_spawned = False
        self.show_hitboxes = False
        self.show_ship_selection = False
    def _load_gameplay_bg(self):
        """Tự động tìm gameplay_bg.jpg ở nhiều chỗ phổ biến"""
        possible_paths = [
            "src/backgrounds/gameplay_bg.png",
            "src/backgrounds/gameplay_bg.png",
            "src/backgrounds/gameplay_bg.png",
            "src/backgrounds/gameplay_bg.png",
            "src/backgrounds/gameplay_bg.png",
        ]
        for p in possible_paths:
            path = Path(p)
            if path.exists():
                try:
                    img = pygame.image.load(path).convert()
                    print(f"ĐÃ TẢI BACKGROUND: {path}")
                    return img
                except Exception as e:
                    print(f"Lỗi tải {path}: {e}")
        print("Không tìm thấy gameplay_bg.jpg → dùng nền đen")
        return None

    def _resize_gameplay_bg(self):
        """Scale lại background theo kích thước màn hình"""
        if self.gameplay_bg_original:
            self.gameplay_bg = pygame.transform.smoothscale(
                self.gameplay_bg_original,
                (self.settings.screen_width, self.settings.screen_height)
            )
    def _load_gameplay_background(self):
        bg_path = Path("assets/bg/gameplay_bg.jpg")
        if not bg_path.exists():
            bg_path = Path("assets/bg/gameplay_bg.png")
        if not bg_path.exists():
            return None
        try:
            return pygame.image.load(bg_path).convert()
        except:
            return None

    def _scale_gameplay_bg(self):
        if self.gameplay_bg:
            self.bg_scaled = pygame.transform.smoothscale(self.gameplay_bg, (self.settings.screen_width, self.settings.screen_height))
        else:
            self.bg_scaled = None

    def load_sounds(self):
        # Hỗ trợ âm thanh nằm trong src/sounds/ và nhiều định dạng
        sound_list = [
            "shoot", "hit", "ship_hit", "level_up", "explosion",
            "selectButton",   # ← tiếng click menu
            "laser",              # ← tiếng bắn
            "youWin"
        ]

        for name in sound_list:
            # Thử tìm trong src/sounds/ trước, rồi mới thử thư mục gốc
            for folder in ["src/sounds", "sounds"]:
                for ext in [".mp3", ".wav", ".ogg"]:
                    sound_path = Path(folder) / f"{name}{ext}"
                    if sound_path.exists():
                        try:
                            self.sounds[name] = pygame.mixer.Sound(sound_path)
                            print(f"ĐÃ TẢI ÂM THANH: {sound_path}")
                            break  # tìm thấy rồi thì thoát vòng lặp
                        except Exception as e:
                            print(f"Lỗi tải {sound_path}: {e}")
                else:
                    continue  # nếu chưa tìm thấy thì thử folder tiếp theo
                break  # nếu đã tìm thấy trong folder này thì thoát
            else:
                print(f"Không tìm thấy âm thanh: {name} trong src/sounds/ hoặc sounds/")
                self.sounds[name] = None

    def play_sound(self, name):
        # Phát âm thanh hiệu ứng
        if sound := self.sounds.get(name):
            volume = getattr(self.audio_manager, 'sfx_volume', 0.7)
            sound.set_volume(volume)
            sound.play()

    def boss_explosion(self):
        self.play_sound("explosion")
        center = self.boss.rect.center
        for _ in range(100):
            particle = {
                'pos': [center[0], center[1]],
                'vel': [random.uniform(-12, 12), random.uniform(-12, 12)],
                'life': random.randint(50, 100),
                'color': (random.randint(200, 255), random.randint(80, 180), 0)
            }
            self.explosion_particles.append(particle)

    def update_particles(self):
        for p in self.explosion_particles[:]:
            p['pos'][0] += p['vel'][0]
            p['pos'][1] += p['vel'][1]
            p['vel'][1] += 0.5
            p['life'] -= 1
            if p['life'] <= 0:
                self.explosion_particles.remove(p)
            else:
                pygame.draw.circle(self.screen, p['color'], (int(p['pos'][0]), int(p['pos'][1])), 4)

    def start_level(self, level_id):
        if level_id not in LEVEL_CONFIGS:
            return
        config = LEVEL_CONFIGS[level_id]
        self.settings.alien_speed = config.alien_speed
        self.settings.fleet_drop_speed = config.fleet_drop_speed
        self.settings.bullet_allowed = config.bullet_allowed
        self.settings.alien_points = config.alien_points

        carry_scores = False
        if self.stats.completed_level == level_id - 1:
            if self.stats.last_level == self.stats.completed_level or self.stats.show_level_complete:
                carry_scores = True

        if carry_scores:
            self.stats.ships_left = 3
            self.stats.level_score = 0
        else:
            self.stats.reset_stats()
            try:
                self.stats.save_data['high_score'] = 0
                SaveManager.save(self.stats.save_data['unlocked_levels'], self.stats.save_data['high_score'])
            except Exception:
                pass
        
        self.stats.last_level = level_id
        self.stats.current_level = level_id
        self.stats.game_active = True
        self.stats.in_level_select = False
        self.stats.show_level_complete = False
        self.stats.show_pause_menu = False
        self.stats.show_game_over = False
        self.fleet_direction_cooldown = 0
        self.stats.paused = False
        
        self.aliens.empty()
        self.bullets.empty()
        self.enemy_bullets.empty()
        self.boss = None
        self.boss_spawned = False
        self.explosion_particles.clear()
        self.ship.center_ship()
        self._create_fleet(level_id)
        
        self.last_shot_time = pygame.time.get_ticks()
        self.audio_manager.play_game_music()

    def _create_fleet(self, level_id):
        config = LEVEL_CONFIGS[level_id]
        alien_width, alien_height = 45, 35
        margin_x, margin_y = 80, 100

        # XÓA HẾT alien cũ
        self.aliens.empty()

        # ================================
        # MÀN 1 & 2: TẠO LƯỚI ĐẸP, TỰ ĐỘNG THEO alien_count TRONG CONFIG
        # ================================
        if level_id in (1, 2):
            target_count = config.alien_count

            # Tự động tính số hàng và cột sao cho gần vuông nhất + đẹp nhất
            cols = int(target_count ** 0.5) + 2
            rows = (target_count + cols - 1) // cols  # làm tròn lên

            # Điều chỉnh khoảng cách để vừa màn hình
            available_width = self.settings.screen_width - 2 * margin_x
            available_height = 500  # chiều cao vùng trên dành cho alien

            spacing_x = max(55, available_width // (cols + 1))
            spacing_y = max(48, available_height // (rows + 2))

            start_x = (self.settings.screen_width - (cols - 1) * spacing_x) // 2
            start_y = 80 if level_id == 1 else 60  # màn 2 sát hơn tí

            for r in range(rows):
                for c in range(cols):
                    if len(self.aliens) >= target_count:
                        break
                    x = start_x + c * spacing_x
                    y = start_y + r * spacing_y
                    self.aliens.add(Alien(self, x, y))
                if len(self.aliens) >= target_count:
                    break

            print(f"ẢI {level_id}: Lưới đẹp {cols}×{rows} → {len(self.aliens)} alien (đúng {target_count})")

        # ================================
        # MÀN 3: RANDOM BAY LƯỢN – DÙNG ĐÚNG alien_count
        # ================================
        elif level_id == 3:
            target_count = config.alien_count
            attempts = 0
            spawned = 0
            ship_y = self.settings.screen_height - 100

            while spawned < target_count and attempts < 3000:
                x = random.randint(margin_x, self.settings.screen_width - margin_x - alien_width)
                y = random.randint(margin_y, margin_y + 450)
                if y < ship_y - 80:
                    rect = pygame.Rect(x, y, alien_width, alien_height)
                    if not any(rect.colliderect(a.rect.inflate(-25, -25)) for a in self.aliens):
                        self.aliens.add(Alien(self, x, y, random_alien=True))
                        spawned += 1
                attempts += 1
            print(f"ẢI 3: Random bay lượn → {len(self.aliens)}/{target_count} alien")

        # ================================
        # MÀN 4: RANDOM ĐIÊN CUỒNG + CHUẨN BỊ BOSS
        # ================================
        elif level_id == 4:
            target_count = config.alien_count
            attempts = 0
            while len(self.aliens) < target_count and attempts < 5000:
                x = random.randint(margin_x, self.settings.screen_width - margin_x - alien_width)
                y = random.randint(margin_y, 650)
                rect = pygame.Rect(x, y, alien_width, alien_height)
                if not any(rect.colliderect(a.rect.inflate(-35, -35)) for a in self.aliens):
                    self.aliens.add(Alien(self, x, y, random_alien=True))
                attempts += 1
            print(f"ẢI 4: Random cực mạnh → {len(self.aliens)}/{target_count} alien – SẴN SÀNG BOSS!")
    def draw_ship_selection(self):
        """Bảng chọn 5 skin tên lửa – đẹp như game AAA"""
        if not self.show_ship_selection:
            return

        # Overlay mờ
        overlay = pygame.Surface((self.settings.screen_width, self.settings.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        # Khung chính
        box = pygame.Rect(0, 0, 960, 560)
        box.center = self.screen.get_rect().center
        pygame.draw.rect(self.screen, (15, 25, 60), box, border_radius=30)
        pygame.draw.rect(self.screen, (100, 180, 255), box, 10, border_radius=30)

        # Tiêu đề
        title = get_font(72).render("CHỌN TÊN LỬA", True, (255, 220, 50))
        title_rect = title.get_rect(center=(box.centerx, box.top + 80))
        shadow = get_font(72).render("CHỌN TÊN LỬA", True, (0, 0, 0))
        self.screen.blit(shadow, (title_rect.x + 4, title_rect.y + 4))
        self.screen.blit(title, title_rect)

        # Hiển thị 5 skin
        start_x = box.centerx - 400
        y = box.centery + 20
        for i in range(5):
            x = start_x + i * 180
            path = Path(f"src/backgrounds/roket_{i}.png")
            
            if path.exists():
                img = pygame.image.load(path).convert_alpha()
            else:
                # Hình thay thế nếu thiếu file
                img = pygame.Surface((100, 80), pygame.SRCALPHA)
                pygame.draw.polygon(img, (180, 180, 180), [(50,0), (90,80), (50,60), (10,80)])
            
            img = pygame.transform.smoothscale(img, (140, 105))
            rect = img.get_rect(center=(x, y))

            # Viền vàng nếu đang chọn
            if i == self.settings.ship_skin:
                glow = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
                glow.fill((255, 220, 0, 100))
                self.screen.blit(glow, glow.get_rect(center=rect.center))
                pygame.draw.rect(self.screen, (255, 230, 0), rect.inflate(30, 30), 8, border_radius=20)

            self.screen.blit(img, rect)

            # Bấm để chọn
            if rect.collidepoint(pygame.mouse.get_pos()):
                if pygame.mouse.get_pressed()[0]:
                    self.settings.ship_skin = i
                    self.ship.image = self.ship._load_ship_image()
                    self.ship.rect = self.ship.image.get_rect()
                    self.ship.rect.midbottom = self.screen.get_rect().midbottom
                    self.play_sound("selectButton")
                    pygame.time.wait(180)  # chống click liên tục

        # Nút ĐÓNG
        close_btn = pygame.Rect(box.centerx - 120, box.bottom - 100, 240, 70)
        pygame.draw.rect(self.screen, (200, 40, 40), close_btn, border_radius=20)
        pygame.draw.rect(self.screen, (255, 255, 255), close_btn, 5, border_radius=20)
        close_text = get_font(48).render("ĐÓNG", True, (255, 255, 255))
        self.screen.blit(close_text, close_text.get_rect(center=close_btn.center))

        if close_btn.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.show_ship_selection = False
            pygame.time.wait(180)
    def run_game(self):
        last_state = None
        while True:
            self.clock.tick(FPS)
            events = pygame.event.get()
            self._check_events(events)

            if self.stats.show_level_complete:
                current = "level_complete"
            elif self.stats.show_game_over:
                current = "game_over"
            elif not self.stats.game_active and not self.stats.in_level_select and not self.stats.show_settings:
                current = "main_menu"
            elif self.stats.in_level_select:
                current = "level_select"
            elif self.stats.show_settings:
                current = "settings"
            elif self.stats.game_active:
                if self.stats.show_pause_menu:
                    current = "pause_menu"
                elif self.stats.paused:
                    current = "paused"
                else:
                    current = "game"
            else:
                current = "unknown"

            if current != last_state:
                if current in ["main_menu", "level_select", "settings", "level_complete", "pause_menu", "game_over"]:
                    self.audio_manager.play_menu_music()
                elif current == "game":
                    self.audio_manager.play_game_music()
                elif current == "paused":
                    self.audio_manager.pause_music()
                else:
                    self.audio_manager.unpause_music()
                last_state = current

            if current == "main_menu":
                # Phiên bản mới của Menu không còn trả về action nữa
                # mà xử lý trực tiếp trong class → chỉ cần gọi handle_events()
                self.menu.handle_events(events)

                # Xử lý hành động từ menu (nếu có)
                if getattr(self.stats, "in_level_select", False) and self.stats.in_level_select:
                    self.stats.in_level_select = True
                if getattr(self.stats, "show_settings", False) and self.stats.show_settings:
                    self.stats.show_settings = True
                if getattr(self, "show_ship_selection", False):
                    self.show_ship_selection = True

            elif current == "level_select":
                level_id = self.level_menu.handle_events(events)
                if level_id:
                    self.start_level(level_id)

            elif current == "settings":
                self.settings_menu.handle_events(events)

            elif current == "level_complete":
                if any(e.type == pygame.MOUSEBUTTONDOWN for e in events):
                    self.level_complete_menu.handle_click(pygame.mouse.get_pos())

            elif current == "game_over":
                if any(e.type == pygame.MOUSEBUTTONDOWN for e in events):
                    self.game_over_menu.handle_click(pygame.mouse.get_pos())

            elif self.stats.game_active:
                if self.stats.show_pause_menu:
                    self.pause_menu.handle_events(events)
                elif not self.stats.paused:
                    self._update_game()

            self._update_screen()
            self.draw_ship_selection()
            pygame.display.flip()

    def _check_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self._cleanup_and_exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.stats.game_active and not self.stats.paused:
                    self._fire_bullet()
                    
                elif event.key == pygame.K_ESCAPE and self.stats.game_active and not self.stats.show_pause_menu:
                    self.stats.show_pause_menu = True
                elif event.key == pygame.K_F3:
                    self.show_hitboxes = not self.show_hitboxes
                    status = "BẬT" if self.show_hitboxes else "TẮT"
                    print(f"[DEBUG] Hiện hitbox: {status}")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.stats.game_active and not self.stats.paused:
                    self.menu_button.update(mouse_pos)
                    if self.menu_button.handle_click(mouse_pos):
                        continue

    def _cleanup_and_exit(self):
        if self.audio_manager:
            self.audio_manager.stop_music()
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.quit()
        sys.exit()

    def _update_game(self):
        keys = pygame.key.get_pressed()
        self.ship.moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self.ship.moving_left = keys[pygame.K_LEFT] or keys[pygame.K_a]

        self.ship.update()
        self._update_bullets()
        self._update_aliens()

    def _fire_bullet(self):
        now = pygame.time.get_ticks()
        if (now - self.last_shot_time >= self.shoot_cooldown and 
            len(self.bullets) < self.settings.bullet_allowed):
            bullet = Bullet(self, self.ship.rect.midtop, (100, 255, 255), -self.settings.bullet_speed)
            self.bullets.add(bullet)
            self.play_sound("laser")
            self.last_shot_time = now

    def _update_bullets(self):
        self.bullets.update()
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        
        self.enemy_bullets.update()
        for bullet in self.enemy_bullets.copy():
            if bullet.rect.top >= self.screen.get_height():
                self.enemy_bullets.remove(bullet)
        
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, False)
        for bullet, aliens in collisions.items():
            for alien in aliens:
                if alien.take_damage():
                    self.stats.score += alien.points
                    self.stats.level_score += alien.points
                    self.stats.update_high_score()

        if self.boss:
            boss_hit = pygame.sprite.spritecollideany(self.boss, self.bullets)
            if boss_hit:
                self.bullets.remove(boss_hit)
                self.boss.take_damage()

        # Kiểm tra va chạm với đạn địch
        ship_hit = pygame.sprite.spritecollideany(self.ship, self.enemy_bullets, collided=pygame.sprite.collide_rect)
        if ship_hit and self.ship.get_hitbox().colliderect(ship_hit.rect):
            self.enemy_bullets.remove(ship_hit)
            self._ship_hit()

    def _update_aliens(self):
        non_random_aliens = [a for a in self.aliens if not a.random_alien]
        if non_random_aliens:
            self._check_fleet_edges(non_random_aliens)

        for alien in self.aliens:
            alien.update()
            if random.random() < alien.shoot_chance:
                alien.shoot()
        
        # Kiểm tra va chạm với alien
        if pygame.sprite.spritecollideany(self.ship, self.aliens, collided=lambda s, a: s.get_hitbox().colliderect(a.rect)):
            self._ship_hit()
            
        for alien in self.aliens:
            if alien.rect.bottom >= self.screen.get_height() - 50:
                self._ship_hit()
                break
                
        if self.stats.current_level == 4 and not self.boss_spawned and not self.aliens:
            self.boss_spawned = True
            self.boss = Boss(self)
            self.play_sound("level_up")

        if not self.aliens and not self.boss and self.stats.game_active:
            self.stats.completed_level = self.stats.current_level
            bonus = 1000 if self.stats.current_level < 4 else 10000
            self.stats.score += self.stats.level_score + bonus
            self.play_sound("youWin")
            self.show_youwin_screen()
            self.stats.show_level_complete = True
            self.stats.game_active = False
            self.stats.unlock_next_level()
            self.play_sound("level_up")

        if self.boss:
            self.boss.update()

        if self.boss and self.boss.hp <= 0:
            self.stats.completed_level = self.stats.current_level
            self.stats.score += 10000
            self.play_sound("youWin")
            self.show_youwin_screen()
            self.stats.show_level_complete = True
            self.stats.game_active = False
            self.stats.unlock_next_level()
            self.boss = None

    def _ship_hit(self):
        self.play_sound("ship_hit")
        self.stats.ships_left -= 1
        
        if self.stats.ships_left > 0:
            # Giữ nguyên quái + boss (KHÔNG reset fleet nữa!)
            self.bullets.empty()          # Chỉ reset đạn tàu
            self.enemy_bullets.empty()    # Reset đạn địch để công bằng
            self.ship.center_ship()       # Tàu về giữa
            pygame.time.wait(800)         # Dừng 0.8s để thở
            
            # Boss giữ nguyên vị trí + máu (nếu có)
            if self.boss:
                self.boss.rect.centerx = self.settings.screen_width // 2
        else:
            self.stats.game_active = False
            self.stats.show_game_over = True
            self.stats.update_high_score()
            self.show_gameover_screen() 
            pygame.mouse.set_visible(True)

    def _check_fleet_edges(self, aliens):
        if self.fleet_direction_cooldown > 0:
            self.fleet_direction_cooldown -= 1
            return
        for alien in aliens:
            if (alien.rect.right >= self.settings.screen_width and self.settings.fleet_direction > 0) or \
               (alien.rect.left <= 0 and self.settings.fleet_direction < 0):
                self._change_fleet_direction()
                self.fleet_direction_cooldown = 18
                break

    def _change_fleet_direction(self):
        self.settings.fleet_direction *= -1

    def _update_screen(self):
                # VẼ BACKGROUND CHỈ KHI ĐANG CHƠI (không vẽ lên menu)
        if self.stats.game_active and not self.stats.show_level_complete and not self.stats.show_game_over:
            if self.gameplay_bg:
                self.screen.blit(self.gameplay_bg, (0, 0))
                # Lớp overlay nhẹ cho dễ nhìn chữ + tàu
                overlay = pygame.Surface((self.settings.screen_width, self.settings.screen_height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 50))   # 50/255 = trong suốt nhẹ
                self.screen.blit(overlay, (0, 0))
            else:
                self.screen.fill(self.settings.bg_color)
        else:
            # Menu, pause, game over → nền đen như cũ
            self.screen.fill(self.settings.bg_color)

        if self.stats.show_level_complete:
            # VẼ ẢNH YOU WIN NẾU CÓ (nằm dưới cùng)
            if hasattr(self, 'current_win_image') and self.current_win_image:
                self.screen.blit(self.current_win_image, self.current_win_rect)
            
            # VẼ MENU CHỮ + NÚT Ở TRÊN CÙNG
            self.level_complete_menu.draw()
        elif self.stats.show_game_over:
            if hasattr(self, 'current_gameover_image') and self.current_gameover_image:
                self.screen.blit(self.current_gameover_image, self.current_gameover_rect)
            
            # VẼ MENU CHỮ + NÚT LÊN TRÊN
            self.game_over_menu.draw()
        elif not self.stats.game_active and not self.stats.in_level_select and not self.stats.show_settings:
            self.menu.draw()
        elif self.stats.in_level_select:
            self.level_menu.draw()
        elif self.stats.show_settings:
            self.settings_menu.draw()
        elif self.stats.game_active:
            for bullet in self.bullets:
                bullet.draw()
            for bullet in self.enemy_bullets:
                bullet.draw()
            for alien in self.aliens:
                alien.draw()
            if self.boss:
                self.boss.draw()
            self.ship.draw()
            self.sb.show_score()
            self.menu_button.draw()
            self.update_particles()

            if self.stats.show_pause_menu:
                self.pause_menu.draw()

            if self.stats.paused and not self.stats.show_pause_menu:
                overlay = pygame.Surface(self.screen.get_size())
                overlay.set_alpha(180)
                overlay.fill((40, 40, 60))
                self.screen.blit(overlay, (0, 0))
                pause_text = get_font(72).render("TẠM DỪNG", True, (255, 255, 255))
                self.screen.blit(pause_text, pause_text.get_rect(center=self.screen.get_rect().center))
                        # ==============================================================
            # BẤM F3 ĐỂ BẬT/TẮT HIỆN HITBOX – CHỈ HIỆN KHI ĐANG CHƠI GAME
            # ==============================================================
            if self.show_hitboxes and self.stats.game_active and not self.stats.paused:
                # Hitbox tàu – XANH LÁ SIÊU RÕ
                ship_hitbox = self.ship.get_hitbox()
                pygame.draw.rect(self.screen, (0, 255, 0), ship_hitbox, 4)

                # Hitbox alien – ĐỎ
                for alien in self.aliens:
                    pygame.draw.rect(self.screen, (255, 0, 0), alien.rect, 2)

                # Hitbox boss – TÍM ĐẬM
                if self.boss:
                    pygame.draw.rect(self.screen, (200, 0, 255), self.boss.rect, 6)

                # Đạn bạn – XANH DƯƠNG
                for bullet in self.bullets:
                    pygame.draw.rect(self.screen, (0, 255, 255), bullet.rect, 2)

                # Đạn địch – VÀNG CAM
                for bullet in self.enemy_bullets:
                    pygame.draw.rect(self.screen, (255, 180, 0), bullet.rect, 2)

                # Chữ thông báo đẹp lung linh
                debug_text = get_font(28).render("F3: ẨN HITBOX DEBUG", True, (255, 255, 100))
                text_rect = debug_text.get_rect(topright=(self.settings.screen_width - 20, 10))
                pygame.draw.rect(self.screen, (0, 0, 0, 180), text_rect.inflate(20, 10))
                self.screen.blit(debug_text, text_rect)

    # ================== HIỆN ẢNH YOU WIN KHI THẮNG ==================
    def _load_youwin_image(self):
        """Tải ảnh YOU WIN"""
        possible_paths = [
            "src/backgrounds/youWin.jpg",
            "src/backgrounds/youwin.jpg",
            "src/backgrounds/YouWin.jpg",
            "src/backgrounds/YOUWIN.jpg",
            "assets/youWin.jpg",
        ]
        for p in possible_paths:
            path = Path(p)
            if path.exists():
                try:
                    img = pygame.image.load(path).convert_alpha()
                    print(f"ĐÃ TẢI ẢNH THẮNG: {path}")
                    return img
                except Exception as e:
                    print(f"Lỗi tải ảnh thắng {path}: {e}")
        print("Không tìm thấy ảnh youWin.jpg → không hiện ảnh thắng")
        return None

    def show_youwin_screen(self):
        """Hiển thị ảnh YOU WIN + giữ nguyên ảnh đến khi bấm nút"""
        if not hasattr(self, 'youwin_image') or not self.youwin_image:
            self.youwin_image = self._load_youwin_image()
        if not self.youwin_image:
            return

        # Phát nhạc thắng
        self.play_sound("youWin")

        # Scale ảnh vừa full màn hình (hoặc hơi to hơn cho hoành tráng)
        win_img = pygame.transform.smoothscale(
            self.youwin_image,
            (self.settings.screen_width + 100, self.settings.screen_height + 100)
        )
        rect = win_img.get_rect(center=self.screen.get_rect().center)

        # Lưu ảnh vào thuộc tính để _update_screen() vẽ lại mỗi frame
        self.current_win_image = win_img
        self.current_win_rect = rect

        # Hiệu ứng fade-in nhẹ (từ trong suốt → hiện rõ)
        clock = pygame.time.Clock()
        alpha = 0
        while alpha < 255:
            self.screen.fill((0, 0, 0))
            img = self.current_win_image.copy()
            img.set_alpha(alpha)
            self.screen.blit(img, self.current_win_rect)
            pygame.display.flip()
            alpha += 10
            clock.tick(60)

        # Giữ nguyên ảnh đến khi người chơi bấm nút (không tự mất nữa!)
        # → ảnh sẽ được vẽ lại liên tục trong _update_screen()
        

        # zoom từ 0.3 → 1.1 trong ~1 giây

        # Giữ ảnh 2 giây
        pygame.time.wait(2000)
        
    def show_gameover_screen(self):
        """Hiển thị ảnh GAME OVER full màn + hiệu ứng fade in"""
        # Tìm ảnh game over
        possible_paths = [
            "src/backgrounds/game_over.jpg",
            "src/backgrounds/gameover.jpg",
            "src/backgrounds/gameOver.jpg",
            "src/backgrounds/GAMEOVER.jpg",
            "src/backgrounds/game_over.png",
            "assets/game_over.jpg",
        ]
        gameover_image = None
        for p in possible_paths:
            path = Path(p)
            if path.exists():
                try:
                    gameover_image = pygame.image.load(path).convert_alpha()
                    print(f"ĐÃ TẢI ẢNH GAME OVER: {path}")
                    break
                except Exception as e:
                    print(f"Lỗi tải {path}: {e}")

        if not gameover_image:
            print("Không tìm thấy ảnh game over → dùng chữ thôi")
            return

        # Scale + hiệu ứng fade in
        img = pygame.transform.smoothscale(
            gameover_image,
            (self.settings.screen_width + 120, self.settings.screen_height + 120)
        )
        rect = img.get_rect(center=self.screen.get_rect().center)

        self.current_gameover_image = img
        self.current_gameover_rect = rect

        # Fade in mượt mà
        clock = pygame.time.Clock()
        alpha = 0
        while alpha < 255:
            self.screen.fill((0, 0, 0))
            temp = img.copy()
            temp.set_alpha(alpha)
            self.screen.blit(temp, rect)
            pygame.display.flip()
            alpha += 12
            clock.tick(60)
            
    def resize_all_backgrounds(self):
        """Scale lại TẤT CẢ background (menu mới + menu cũ hoài cổ + gameplay + win + gameover)"""
        w = self.screen.get_width()
        h = self.screen.get_height()

        # 1. MENU BACKGROUND MỚI (luôn có)
        if hasattr(self, 'menu_bg_original') and self.menu_bg_original:
            self.menu_bg_scaled = pygame.transform.smoothscale(self.menu_bg_original, (w, h))

        # 2. MENU BACKGROUND CŨ – HOÀI CỔ SIÊU ĐẸP (mới thêm)
        if hasattr(self, 'menu_bg_old_original') and self.menu_bg_old_original:
            self.menu_bg_old_scaled = pygame.transform.smoothscale(self.menu_bg_old_original, (w, h))
        else:
            self.menu_bg_old_scaled = None  # không có thì thôi

        # 3. Gameplay background
        if self.gameplay_bg_original:
            self.gameplay_bg = pygame.transform.smoothscale(self.gameplay_bg_original, (w, h))

        # 4. You Win image
        if hasattr(self, 'youwin_image') and self.youwin_image:
            img = pygame.transform.smoothscale(self.youwin_image, (w + 120, h + 120))
            self.current_win_image = img
            self.current_win_rect = img.get_rect(center=(w//2, h//2))

        # 5. Game Over image
        if hasattr(self, 'current_gameover_image') and self.current_gameover_image:
            img = pygame.transform.smoothscale(self.current_gameover_image, (w + 120, h + 120))
            self.current_gameover_image = img
            self.current_gameover_rect = img.get_rect(center=(w//2, h//2))
if __name__ == "__main__":
    game = AlienInvasion()
    game.run_game()