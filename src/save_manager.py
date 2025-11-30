# src/save_manager.py
import json
import os

class SaveManager:
    SAVE_FILE = "save_data.json"

    @staticmethod
    def load():
        if os.path.exists(SaveManager.SAVE_FILE):
            try:
                with open(SaveManager.SAVE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {
                    'unlocked_levels': data.get('unlocked_levels', [1, 2, 3, 4]),
                    'high_score': data.get('high_score', 0)
                }
            except:
                pass
        return {'unlocked_levels': [1, 2, 3, 4], 'high_score': 0}

    @staticmethod
    def save(unlocked_levels, high_score):
        data = {
            'unlocked_levels': unlocked_levels,
            'high_score': high_score
        }
        with open(SaveManager.SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)