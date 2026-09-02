import json
import os
import sys

CONFIG_FILE = "user_config.json"
HISTORY_FILE = "vocab_history.json"
CACHE_FILE = "vocab_cache.json"


def _data_dir():
    """数据文件根目录：
    - PyInstaller 打包运行时：exe 所在目录（保证可写）
    - 源码运行时：项目根目录（main.py 所在目录，即本文件上溯两级包目录）
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


DATA_DIR = _data_dir()


def data_path(name):
    """优先使用应用数据目录下的文件，兼容旧版本保存于工作目录(CWD)的文件。"""
    app_path = os.path.join(DATA_DIR, name)
    if os.path.exists(app_path) or not os.path.exists(name):
        return app_path
    return name


def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, type(default)):
                return data
    except Exception:
        pass
    return default


def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class ConfigRepository:
    def __init__(self):
        self.default_config = {
            "api_url": "https://api.deepseek.com/v1/chat/completions",
            "api_key": "",
            "model_name": "deepseek-chat",
            "difficulty": "初高中/日常通俗 (周围词汇极简)",
            "appearance_mode": "深色模式",
            "font_size_scale": "标准 (100%)",
            "theme_accent": "indigo",
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
            # 词典系统（公益公开词典源 + 离线词典导入）
            "dictionary_enabled_sources": ["wiktionary", "freedict"],
            "merriam_key": "",
            # 记单词（每日上限）
            "daily_new_words": 10,
            "daily_max_reviews": 30,
            # Web UI（局域网访问）
            "web_enabled": False,
            "web_port": 8765,
            "web_token": "",
        }
        self.path = data_path(CONFIG_FILE)
        self.data = self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if isinstance(cfg, dict):
                        return {**self.default_config, **cfg}
            except Exception:
                pass
        return self.default_config.copy()

    def save_all(self, data_dict):
        self.data.update(data_dict)
        _save_json(self.path, self.data)

    def save(self, api_url, api_key, model_name, difficulty):
        self.save_all({
            "api_url": api_url.strip(),
            "api_key": api_key.strip(),
            "model_name": model_name.strip(),
            "difficulty": difficulty
        })


class VocabRepository:
    def __init__(self):
        self.history_path = data_path(HISTORY_FILE)
        self.cache_path = data_path(CACHE_FILE)
        self.history = self.load_history()
        self.cache = self.load_cache()

    def load_history(self):
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    words = []
                    for item in data:
                        if isinstance(item, str):
                            word = item.lower().strip()
                        elif isinstance(item, dict) and "word" in item:
                            word = item["word"].lower().strip()
                        else:
                            continue
                        if word and word not in words:
                            words.append(word)
                    return words
            except Exception:
                pass
        return ["serendipity", "persist", "hesitate", "fragile", "resilient"]

    def save_history(self):
        _save_json(self.history_path, self.history)

    def load_cache(self):
        return _load_json(self.cache_path, {})

    def save_cache(self):
        _save_json(self.cache_path, self.cache)

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
