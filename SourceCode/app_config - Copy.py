import os
import sys
import customtkinter as ctk
from repository import ConfigRepository, VocabRepository

class AppConfig:
    def __init__(self):
        self.config_repo = ConfigRepository()
        self.vocab_repo = VocabRepository()

        # 全局统一字体系列名称
        self.font_family = "Microsoft YaHei UI"

        self.apply_gpu_acceleration()
        self.update_font_metrics()

        # -------------------------------------------------------------
        # 极光青蓝 (Nordic Cyan) 磨砂微光调色板
        # -------------------------------------------------------------
        self.c_primary = ("#0284C7", "#38BDF8")
        self.c_primary_hover = ("#0369A1", "#0EA5E9")
        self.c_on_primary = ("#FFFFFF", "#0F172A")

        self.c_secondary = ("#E0F2FE", "#0C4A6E")
        self.c_on_secondary = ("#0369A1", "#BAE6FD")

        # Apple Music 标志性粉红/红色调
        self.c_music_accent = ("#FA2D48", "#FF3B5C")
        self.c_music_bg = ("#FFF1F2", "#2B1118")

        self.c_bg_window = ("#F8FAFC", "#0F172A")
        self.c_surface = ("#F1F5F9", "#1E293B")
        self.c_surface_variant = ("#E2E8F0", "#334155")
        self.c_input_bg = ("#FFFFFF", "#0B0F19")

        self.c_border = ("#CBD5E1", "#334155")
        self.c_border_light = ("#E2E8F0", "#1E293B")

        self.c_btn = ("#E2E8F0", "#334155")
        self.c_btn_hover = ("#CBD5E1", "#475569")
        self.c_btn_del = ("#FEE2E2", "#451A1A")
        self.c_btn_del_hover = ("#FECACA", "#5C2424")

        self.c_success = ("#10B981", "#34D399")
        self.c_success_bg = ("#D1FAE5", "#064E3B")
        self.c_error = ("#EF4444", "#F87171")
        self.c_error_bg = ("#FEE2E2", "#451A1A")

        self.c_text = ("#0F172A", "#F8FAFC")
        self.c_text_secondary = ("#64748B", "#94A3B8")

    def update_font_metrics(self):
        """依据用户设定的比例动态计算全局字号"""
        scale_str = self.config_repo.data.get("font_size_scale", "标准 (100%)")
        if "小" in scale_str:
            m = 0.90
        elif "大" in scale_str and "特大" not in scale_str:
            m = 1.12
        elif "特大" in scale_str:
            m = 1.25
        else:
            m = 1.00

        fam = self.font_family
        self.font_headline = ctk.CTkFont(family=fam, size=int(16 * m), weight="bold")
        self.font_title = ctk.CTkFont(family=fam, size=int(13 * m), weight="bold")
        self.font_normal = ctk.CTkFont(family=fam, size=int(12 * m), weight="normal")
        self.font_bold = ctk.CTkFont(family=fam, size=int(12 * m), weight="bold")
        self.font_small = ctk.CTkFont(family=fam, size=int(11 * m), weight="normal")
        self.font_reader = ctk.CTkFont(family=fam, size=int(14 * m), weight="normal")

    def apply_gpu_acceleration(self):
        if self.gpu_enabled:
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            os.environ["__NV_PRIME_RENDER_OFFLOAD"] = "1"
            os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"
            os.environ["DRI_PRIME"] = "1"
            os.environ["QSG_RENDER_LOOP"] = "basic"
            os.environ["PYTHONOPTIMIZE"] = "1"

    @property
    def gpu_enabled(self):
        return bool(self.config_repo.data.get("gpu_acceleration", True))

    @property
    def wallpaper_path(self):
        return self.config_repo.data.get("wallpaper_path", "")

    @property
    def wallpaper_blur(self):
        return int(self.config_repo.data.get("wallpaper_blur", 12))

    @property
    def wallpaper_opacity(self):
        return float(self.config_repo.data.get("wallpaper_opacity", 0.45))

    @property
    def appearance_mode(self):
        mode = self.config_repo.data.get("appearance_mode", "深色模式")
        if mode == "浅色模式":
            return "Light"
        elif mode == "跟随系统":
            return "System"
        return "Dark"

    @property
    def translate_engine(self):
        return self.config_repo.data.get("translate_engine", "AI 智能模型")

    @property
    def ms_translator_key(self):
        return self.config_repo.data.get("ms_translator_key", "")

    @property
    def ms_translator_region(self):
        return self.config_repo.data.get("ms_translator_region", "global")

    @property
    def ms_speech_key(self):
        return self.config_repo.data.get("ms_speech_key", "")

    @property
    def ms_speech_region(self):
        return self.config_repo.data.get("ms_speech_region", "eastasia")

    @property
    def ms_voice_name(self):
        return self.config_repo.data.get("ms_voice_name", "en-US-JennyNeural")

    @property
    def api_url(self):
        return self.config_repo.data.get("api_url", "")

    @property
    def api_key(self):
        return self.config_repo.data.get("api_key", "")

    @property
    def model_name(self):
        return self.config_repo.data.get("model_name", "deepseek-chat")

    @property
    def difficulty(self):
        return self.config_repo.data.get("difficulty", "初高中/日常通俗 (周围词汇极简)")

    # Apple Music 属性
    @property
    def apple_music_dev_token(self):
        return self.config_repo.data.get("apple_music_dev_token", "")

    @property
    def apple_music_user_token(self):
        return self.config_repo.data.get("apple_music_user_token", "")

    @property
    def apple_music_storefront(self):
        return self.config_repo.data.get("apple_music_storefront", "cn")

    @property
    def vocab_history(self):
        return self.vocab_repo.history

    @property
    def vocab_cache(self):
        return self.vocab_repo.cache

    def save_config(self, url, key, model, diff):
        self.config_repo.save(url, key, model, diff)