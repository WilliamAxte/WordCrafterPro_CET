import json
import os
import customtkinter as ctk

CONFIG_FILE = "user_config.json"
HISTORY_FILE = "vocab_history.json"

class AppConfig:
    def __init__(self):
        self.font_normal = ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="normal")
        self.font_body = ctk.CTkFont(family="Microsoft YaHei UI", size=14, weight="normal")
        self.font_small = ctk.CTkFont(family="Microsoft YaHei UI", size=11, weight="normal")
        self.font_reader = ctk.CTkFont(family="Microsoft YaHei UI", size=17, weight="normal")

        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = ""
        self.model_name = "deepseek-chat"
        self.difficulty = "初高中/日常通俗 (周围词汇极简)"

        self.vocab_history = self.load_history()
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.api_url = data.get("api_url", self.api_url)
                    self.api_key = data.get("api_key", self.api_key)
                    self.model_name = data.get("model_name", self.model_name)
                    self.difficulty = data.get("difficulty", self.difficulty)
            except Exception:
                pass

    def save_config(self, url, key, model, diff):
        self.api_url = url.strip()
        self.api_key = key.strip()
        self.model_name = model.strip()
        self.difficulty = diff
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "api_url": self.api_url,
                    "api_key": self.api_key,
                    "model_name": self.model_name,
                    "difficulty": self.difficulty
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return list(dict.fromkeys(data))
            except Exception:
                pass
        return ["serendipity", "persist", "hesitate", "fragile", "resilient"]

    def save_history_to_file(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.vocab_history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_words_to_history(self, new_words):
        added_count = 0
        for w in new_words:
            w_clean = w.strip().lower()
            if w_clean and w_clean not in self.vocab_history:
                self.vocab_history.append(w_clean)
                added_count += 1
        if added_count > 0:
            self.save_history_to_file()
        return added_count

    def clear_all_history(self):
        self.vocab_history.clear()
        self.save_history_to_file()
