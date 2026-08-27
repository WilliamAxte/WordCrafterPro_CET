# ==============================================================================
# 文件路径: ui_music.py
# 包含组件: AppleMusicDrawer
# ==============================================================================
import base64
import io
from PIL import Image
import customtkinter as ctk
from music_service import AppleMusicStoreService


class AppleMusicDrawer(ctk.CTkFrame):
    """Apple Music 微软商店版全局伴读底栏 (带封面渲染与音量控制)"""

    def __init__(self, master, app_ref):
        cfg = app_ref.config
        super().__init__(
            master, corner_radius=12, fg_color=cfg.c_surface, border_width=1, border_color=cfg.c_border, height=60
        )
        self.app_ref = app_ref
        self._last_art_b64 = None
        self._art_image = None

        self.setup_music_bar()
        AppleMusicStoreService.set_state_listener(self.on_player_state_change)

    def setup_music_bar(self):
        cfg = self.app_ref.config
        self.bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bar_frame.pack(fill="x", padx=10, pady=6)

        # 1. 专辑封面位
        self.lbl_album_art = ctk.CTkLabel(
            self.bar_frame,
            text="🍎",
            font=(cfg.font_family, 18, "bold"),
            width=46,
            height=46,
            corner_radius=8,
            fg_color=cfg.c_music_bg,
            text_color=cfg.c_music_accent
        )
        self.lbl_album_art.pack(side="left", padx=(0, 10))

        # 2. 曲目名称与专辑
        self.info_box = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        self.info_box.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.lbl_title = ctk.CTkLabel(
            self.info_box, text="Apple Music 会话同步就绪", font=cfg.font_bold, text_color=cfg.c_text, anchor="w"
        )
        self.lbl_title.pack(fill="x")

        self.lbl_artist = ctk.CTkLabel(
            self.info_box,
            text="打开商店版 Apple Music 即可在伴读中沉浸畅听",
            font=cfg.font_small,
            text_color=cfg.c_text_secondary,
            anchor="w"
        )
        self.lbl_artist.pack(fill="x")

        # 3. 控制区
        ctrls = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        ctrls.pack(side="right")

        ctk.CTkButton(
            ctrls,
            text="🍎 唤起客户端",
            width=110,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_secondary,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_on_secondary,
            command=AppleMusicStoreService.launch_store_app
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ctrls,
            text="⏮",
            width=30,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=AppleMusicStoreService.prev_track
        ).pack(side="left", padx=2)

        self.btn_play = ctk.CTkButton(
            ctrls,
            text="▶",
            width=34,
            height=28,
            corner_radius=6,
            font=cfg.font_bold,
            fg_color=cfg.c_primary,
            hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_primary,
            command=AppleMusicStoreService.toggle_play
        )
        self.btn_play.pack(side="left", padx=3)

        ctk.CTkButton(
            ctrls,
            text="⏭",
            width=30,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=AppleMusicStoreService.next_track
        ).pack(side="left", padx=2)

        ctk.CTkLabel(ctrls, text="🔊", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left", padx=(6, 2))
        self.slider_vol = ctk.CTkSlider(
            ctrls,
            from_=0,
            to=100,
            number_of_steps=100,
            width=70,
            button_color=cfg.c_primary,
            progress_color=cfg.c_primary,
            command=AppleMusicStoreService.set_system_volume
        )
        self.slider_vol.set(70)
        self.slider_vol.pack(side="left", padx=(0, 4))

    def on_player_state_change(self, state):
        self.after(0, self._update_ui_state, state)

    def _update_ui_state(self, state):
        is_playing = state.get("is_playing", False)
        title = state.get("title", "")
        artist = state.get("artist", "")
        album = state.get("album", "")
        art_b64 = state.get("artwork", "")

        self.btn_play.configure(text="⏸" if is_playing else "▶")
        self.lbl_title.configure(text=title)
        detail_text = f"{artist} · 《{album}》" if album and album != "Apple Music" else artist
        self.lbl_artist.configure(text=detail_text)

        if art_b64 and art_b64 != self._last_art_b64:
            try:
                raw_bytes = base64.b64decode(art_b64)
                img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
                self._art_image = ctk.CTkImage(light_image=img, dark_image=img, size=(46, 46))
                self.lbl_album_art.configure(image=self._art_image, text="")
                self._last_art_b64 = art_b64
            except Exception:
                pass
        elif not art_b64 and self._last_art_b64:
            self.lbl_album_art.configure(image=None, text="🍎")
            self._last_art_b64 = None