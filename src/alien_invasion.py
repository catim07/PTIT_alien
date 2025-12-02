# src/alien_invasion.py ← ĐÂY LÀ FILE CHẠY CHÍNH
import pygame
import sys
import os
from pathlib import Path

# THÊM HÀM TÌM ĐÚNG ĐƯỜNG DẪN KHI BUILD .EXE
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Import class game từ file chính
from alien_invasion_main import AlienInvasion

pygame.init()

def main():
    print("KHỞI ĐỘNG ALIEN INVASION - PHIÊN BẢN HOÀN CHỈNH")
    game = AlienInvasion()
    game.run_game()

if __name__ == "__main__":
    pygame.init()
    main()