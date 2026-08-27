import json
import os

CONFIG_FILE = "user_config.json"
HISTORY_FILE = "vocab_history.json"
CACHE_FILE = "vocab_cache.json"

class ConfigRepository:
    def __init__(self):
        self.default_config = {
            "api_url": "https://api.deepseek.com/v1/chat/completions",
            "api_key": "",
            "model_name": "deepseek-chat",
            "difficulty": "初高中/日常通俗 (周围词汇极简)",
            "appearance_mode": "深色模式",
            "font_size_scale": "标准 (100%)",
            "gpu_acceleration": True,
            "wallpaper_path": "",
            "wallpaper_blur": 12,
            "wallpaper_opacity": 0.45,
            "translate_engine": "AI 智能模型",
            "ms_translator_key": "",
            "ms_translator_region": "global",
            "ms_speech_key": "",
            "ms_speech_region": "eastasia",
            "ms_voice_name": "en-US-JennyNeural",
            # Apple Music 音乐配置
            "apple_music_dev_token": "",
            "apple_music_user_token": "",
            "apple_music_storefront": "cn"
        }
        self.data = self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return {**self.default_config, **cfg}
            except Exception:
                pass
        return self.default_config.copy()

    def save_all(self, data_dict):
        self.data.update(data_dict)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def save(self, api_url, api_key, model_name, difficulty):
        self.save_all({
            "api_url": api_url.strip(),
            "api_key": api_key.strip(),
            "model_name": model_name.strip(),
            "difficulty": difficulty
        })


class VocabRepository:
    def __init__(self):
        self.history = self.load_history()
        self.cache = self.load_cache()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        words = []
                        for item in data:
                            if isinstance(item, str):
                                words.append(item.lower().strip())
                            elif isinstance(item, dict) and "word" in item:
                                words.append(item["word"].lower().strip())
                        return list(dict.fromkeys([w for w in words if w]))
            except Exception:
                pass
        return ["serendipity", "persist", "hesitate", "fragile", "resilient"]

    def save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    def save_cache(self):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_words(self, words):
        added = 0
        for w in words:
            clean = w.strip().lower()
            if clean and clean not in self.history:
                self.history.append(clean)
                added += 1
        if added > 0:
            self.save_history()
        return added

    def remove_word(self, word):
        clean = word.strip().lower()
        if clean in self.history:
            self.history.remove(clean)
            self.save_history()

    def clear_history(self):
        self.history.clear()
        self.save_history()

    def get_stats(self):
        total_words = len(self.history)
        total_letters = sum(len(w) for w in self.history)
        return total_words, total_letters