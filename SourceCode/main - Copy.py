import os
import sys

from PIL import Image, ImageFilter

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import customtkinter as ctk

from app_config import AppConfig
from tab_acg import AcgStoryTab
from tab_reading import AuthenticReadingTab
from tab_settings import SettingsTab
from tab_vocab import VocabStoryTab
from ui_components import VocabManagerWindow, CollapsibleCard, AppleMusicDrawer


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = AppConfig()
        cfg = self.config

        ctk.set_appearance_mode(cfg.appearance_mode)
        ctk.set_default_color_theme("blue")
        self.title("WordCrafter Pro")
        self.geometry("1240x940")
        self.minsize(1040, 760)
        self.configure(fg_color=cfg.c_bg_window)

        self.var_api_url = ctk.StringVar(value=cfg.api_url)
        self.var_api_key = ctk.StringVar(value=cfg.api_key)
        self.var_model_name = ctk.StringVar(value=cfg.model_name)
        self.var_difficulty = ctk.StringVar(value=cfg.difficulty)

        self._raw_wallpaper = None
        self._cached_path = None
        self._last_win_size = (0, 0)
        self._last_render_signature = None
        self._resize_timer = None
        self._wallpaper_ctk_image = None

        self.setup_wallpaper_layer()
        self.setup_ui()
        self.after(100, self.render_frosted_wallpaper)

    # ---------- wallpaper ----------

    def setup_wallpaper_layer(self):
        self.bg_wallpaper_label = ctk.CTkLabel(
            self, text="", image=None, fg_color=self.config.c_bg_window, corner_radius=0
        )
        self.bg_wallpaper_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_wallpaper_label.lower()
        self.bind("<Configure>", self._on_window_resize)

    def _on_window_resize(self, event):
        if event.widget != self or event.width <= 1 or event.height <= 1:
            return
        size = (event.width, event.height)
        if size == self._last_win_size:
            return
        self._last_win_size = size

        try:
            self.bg_wallpaper_label.place_configure(x=0, y=0, relwidth=1, relheight=1)
            self.bg_wallpaper_label.lower()
        except Exception:
            pass

        if self._resize_timer is not None:
            try:
                self.after_cancel(self._resize_timer)
            except Exception:
                pass
        self._resize_timer = self.after(60, self._finish_resize)

    def _finish_resize(self):
        self._resize_timer = None
        try:
            self.render_frosted_wallpaper()
        except Exception as exc:
            print(f"[Wallpaper] resize render failed: {exc}")

    def update_wallpaper_source(self):
        self._cached_path = None
        self._raw_wallpaper = None
        self._last_render_signature = None
        self.render_frosted_wallpaper()

    def _load_wallpaper(self, path):
        if self._cached_path != path or self._raw_wallpaper is None:
            with Image.open(path) as source:
                self._raw_wallpaper = source.convert("RGBA")
            self._cached_path = path
        return self._raw_wallpaper

    @staticmethod
    def _cover_image(image, width, height):
        img_w, img_h = image.size
        if img_w <= 0 or img_h <= 0:
            return None
        scale = max(width / img_w, height / img_h)
        new_w, new_h = max(1, int(img_w * scale)), max(1, int(img_h * scale))
        resized = image.resize((new_w, new_h), Image.Resampling.BILINEAR)
        left, top = max(0, (new_w - width) // 2), max(0, (new_h - height) // 2)
        return resized.crop((left, top, left + width, top + height))

    def _wallpaper_surface_color(self):
        mode = self.config.appearance_mode
        is_dark = mode == "Dark" or (mode == "System" and ctk.get_appearance_mode() == "Dark")
        return (15, 23, 42) if is_dark else (248, 250, 252)

    def render_frosted_wallpaper(self):
        cfg = self.config
        path = cfg.wallpaper_path
        if not path or not os.path.exists(path):
            self._wallpaper_ctk_image = None
            self._last_render_signature = None
            self.bg_wallpaper_label.configure(image=None, fg_color=cfg.c_bg_window)
            self.bg_wallpaper_label.lower()
            return

        width, height = self.winfo_width(), self.winfo_height()
        if width < 100 or height < 100:
            return

        signature = (
            path, width, height, cfg.wallpaper_blur, cfg.wallpaper_opacity,
            cfg.appearance_mode, ctk.get_appearance_mode(),
        )
        if signature == self._last_render_signature:
            return

        try:
            cropped = self._cover_image(self._load_wallpaper(path), width, height)
            if cropped is None:
                return

            blur_radius = cfg.wallpaper_blur
            if blur_radius > 0:
                cropped = cropped.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            alpha = max(0, min(255, int(255 * (1.0 - cfg.wallpaper_opacity))))
            mask = Image.new(
                "RGBA", (width, height), self._wallpaper_surface_color() + (alpha,)
            )
            result = Image.alpha_composite(cropped, mask)
            self._wallpaper_ctk_image = ctk.CTkImage(
                light_image=result, dark_image=result, size=(width, height)
            )
            self.bg_wallpaper_label.configure(
                image=self._wallpaper_ctk_image, fg_color=cfg.c_bg_window
            )
            self.bg_wallpaper_label.lower()
            self._last_render_signature = signature
        except Exception as exc:
            print(f"[Wallpaper] render failed: {exc}")
            self.bg_wallpaper_label.configure(fg_color=cfg.c_bg_window)
            self.bg_wallpaper_label.lower()

    # ---------- main UI ----------

    def setup_ui(self):
        cfg = self.config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. 顶部抽屉式配置卡片 (Drawer Card)
        summary = f"[{cfg.model_name}] · {cfg.difficulty.split(' ')[0]}"
        self.top_drawer = CollapsibleCard(
            self, self, title="模型与接口服务配置", summary_text=summary, initial_open=False
        )
        self.top_drawer.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")

        # 生词库入口放在标题右侧
        self.btn_vocab_mgr = ctk.CTkButton(
            self.top_drawer.header_bar,
            text=f"本地生词库 ({len(cfg.vocab_history)})",
            font=cfg.font_normal, width=135, height=26, corner_radius=12,
            fg_color=cfg.c_secondary, hover_color=cfg.c_btn_hover,
            text_color=cfg.c_on_secondary, command=self.open_vocab_manager,
        )
        self.btn_vocab_mgr.pack(side="right", padx=(0, 4))

        # 抽屉内部表单控件
        cfg_row = ctk.CTkFrame(self.top_drawer.body_frame, fg_color="transparent")
        cfg_row.pack(fill="x", padx=4, pady=(2, 6))

        self._add_config_label(cfg_row, "API Key")
        ctk.CTkEntry(
            cfg_row, textvariable=self.var_api_key, show="*", placeholder_text="sk-...",
            width=180, height=28, corner_radius=6, border_width=1,
            border_color=cfg.c_border, fg_color=cfg.c_input_bg,
            text_color=cfg.c_text, font=cfg.font_normal,
        ).pack(side="left", padx=(0, 10))

        self._add_config_label(cfg_row, "API URL")
        ctk.CTkEntry(
            cfg_row, textvariable=self.var_api_url, width=210, height=28,
            corner_radius=6, border_width=1, border_color=cfg.c_border,
            fg_color=cfg.c_input_bg, text_color=cfg.c_text, font=cfg.font_normal,
        ).pack(side="left", padx=(0, 10))

        self._add_config_label(cfg_row, "模型")
        ctk.CTkComboBox(
            cfg_row,
            values=[
                "deepseek-chat", "deepseek-reasoner", "gpt-4o",
                "gpt-4o-mini", "claude-3-7-sonnet", "qwen-max",
            ],
            variable=self.var_model_name, width=155, height=28, corner_radius=6,
            border_width=1, border_color=cfg.c_border, fg_color=cfg.c_input_bg,
            text_color=cfg.c_text, button_color=cfg.c_btn,
            button_hover_color=cfg.c_btn_hover, dropdown_fg_color=cfg.c_surface,
            dropdown_text_color=cfg.c_text, font=cfg.font_normal,
            dropdown_font=cfg.font_normal,
        ).pack(side="left", padx=(0, 10))

        self._add_config_label(cfg_row, "难度")
        ctk.CTkOptionMenu(
            cfg_row,
            values=[
                "初高中/日常通俗 (周围词汇极简)",
                "大学四级 (通顺自然)",
                "考研/六级/雅思 (地道语境)",
            ],
            variable=self.var_difficulty, width=180, height=28, corner_radius=6,
            fg_color=cfg.c_btn, button_color=cfg.c_btn,
            button_hover_color=cfg.c_btn_hover, dropdown_fg_color=cfg.c_surface,
            dropdown_text_color=cfg.c_text, text_color=cfg.c_text,
            font=cfg.font_normal, dropdown_font=cfg.font_normal,
            command=self.on_config_change,
        ).pack(side="left")

        for variable in (self.var_api_key, self.var_api_url, self.var_model_name):
            variable.trace_add("write", self.on_config_change)

        # 2. 中间多标签核心区 (Tabview)
        self.tabview = ctk.CTkTabview(
            self, corner_radius=10, fg_color=cfg.c_surface,
            border_width=1, border_color=cfg.c_border,
            segmented_button_selected_color=cfg.c_primary,
            segmented_button_selected_hover_color=cfg.c_primary_hover,
            segmented_button_unselected_color=cfg.c_surface_variant,
            segmented_button_unselected_hover_color=cfg.c_btn_hover,
            segmented_button_fg_color=cfg.c_surface_variant,
            text_color=cfg.c_text,
        )
        self.tabview.grid(row=1, column=0, padx=16, pady=(4, 6), sticky="nsew")

        pages = (
            ("page_vocab", "单词情境短文", VocabStoryTab),
            ("page_acg", "二次元特稿 (ACG)", AcgStoryTab),
            ("page_reading", "经典名篇与原著精读", AuthenticReadingTab),
            ("page_settings", "⚙️ 偏好设置", SettingsTab),
        )
        for attr, tab_name, page_cls in pages:
            page = page_cls(self.tabview.add(tab_name), self)
            page.pack(fill="both", expand=True)
            setattr(self, attr, page)

        # 3. 底部 Apple Music 播放器抽屉 (Music Drawer)
        self.music_drawer = AppleMusicDrawer(self, self)
        self.music_drawer.grid(row=2, column=0, padx=16, pady=(4, 12), sticky="ew")

    def _add_config_label(self, parent, text):
        cfg = self.config
        ctk.CTkLabel(
            parent, text=text, font=cfg.font_small, text_color=cfg.c_text_secondary
        ).pack(side="left", padx=(0, 4))

    def on_config_change(self, *args):
        self.config.save_config(
            self.var_api_url.get(), self.var_api_key.get(),
            self.var_model_name.get(), self.var_difficulty.get()
        )
        summary = f"[{self.var_model_name.get()}] · {self.var_difficulty.get().split(' ')[0]}"
        self.top_drawer.update_summary(summary)

    def open_vocab_manager(self):
        VocabManagerWindow(self, self)

    def update_global_vocab_status(self):
        self.btn_vocab_mgr.configure(text=f"本地生词库 ({len(self.config.vocab_history)})")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()