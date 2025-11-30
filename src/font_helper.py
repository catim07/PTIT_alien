import pygame


def get_font(size):
    """Return a pygame Font that prefers system fonts known to support Vietnamese.

    Tries common font family names via SysFont, then falls back to default font file.
    """
    pref_names = ["Segoe UI", "Arial", "Tahoma", "DejaVu Sans", "Noto Sans", "Arial Unicode MS"]
    for name in pref_names:
        try:
            font = pygame.font.SysFont(name, size)
            if font:
                return font
        except Exception:
            continue

    try:
        default_name = pygame.font.get_default_font()
        return pygame.font.Font(default_name, size)
    except Exception:
        return pygame.font.Font(None, size)
