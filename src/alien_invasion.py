# src/alien_invasion.py
import pygame
import sys
from pathlib import Path

print("KIỂM TRA HỆ THỐNG:")
print(f"   Python: {sys.version.split()[0]}")
print(f"   Pygame: {pygame.version.ver}")
print(f"   OS: {'NT' if sys.platform.startswith('win') else sys.platform.upper()}")
print(f"   Save file: {'Có' if Path('save_data.json').exists() else 'Không'}")

try:
    from alien_invasion_main import AlienInvasion
except ImportError as e:
    print(f"LỖI IMPORT: {e}")
    sys.exit(1)

def main():
    print("KHỞI ĐỘNG ALIEN INVASION - ULTRA EDITION")
    pygame.init()
    game = AlienInvasion()
    print("GAME READY! Chạy với 1200x800 @ 60FPS")
    try:
        game.run_game()
    except Exception as e:
        print(f"LỖI CHẠY GAME: {e}")
        import traceback
        traceback.print_exc()
        input("Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()