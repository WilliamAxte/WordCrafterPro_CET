# ==============================================================================
# 文件路径: ui_cards.py
# 包含组件: CollapsibleCard
# ==============================================================================
import customtkinter as ctk


class CollapsibleCard(ctk.CTkFrame):
    """抽屉式折叠卡片组件：支持一键平滑收起/展开参数面板"""

    def __init__(self, master, app_ref, title="参数配置与操作", summary_text="", initial_open=True, **kwargs):
        cfg = app_ref.config
        super().__init__(
            master,
            corner_radius=10,
            fg_color=cfg.c_surface,
            border_width=1,
            border_color=cfg.c_border,
            **kwargs
        )
        self.app_ref = app_ref
        self.title_text = title
        self.is_expanded = initial_open

        self.grid_columnconfigure(0, weight=1)

        self.header_bar = ctk.CTkFrame(self, fg_color="transparent", height=38)
        self.header_bar.pack(fill="x", padx=12, pady=6)
        self.header_bar.pack_propagate(False)

        self.btn_toggle = ctk.CTkButton(
            self.header_bar,
            text="▼" if initial_open else "▶",
            width=26,
            height=26,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_primary,
            command=self.toggle_collapse
        )
        self.btn_toggle.pack(side="left", padx=(0, 8))

        self.lbl_title = ctk.CTkLabel(self.header_bar, text=title, font=cfg.font_bold, text_color=cfg.c_text)
        self.lbl_title.pack(side="left")

        self.lbl_summary = ctk.CTkLabel(
            self.header_bar, text=summary_text, font=cfg.font_small, text_color=cfg.c_text_secondary
        )
        self.lbl_summary.pack(side="left", padx=12)

        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        if initial_open:
            self.body_frame.pack(fill="x", padx=12, pady=(0, 8))

    def update_summary(self, text):
        self.lbl_summary.configure(text=text)

    def toggle_collapse(self):
        if self.is_expanded:
            self.body_frame.pack_forget()
            self.btn_toggle.configure(text="▶")
            self.is_expanded = False
        else:
            self.body_frame.pack(fill="x", padx=12, pady=(0, 8))
            self.btn_toggle.configure(text="▼")
            self.is_expanded = True