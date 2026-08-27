import customtkinter as ctk

from services import AIService
from tab_base import BilingualContentTab

class AuthenticReadingTab(BilingualContentTab):
    fullscreen_title = "经典名篇精读"
    export_en_title = "Authentic English Reading"
    export_success_message = "名篇已保存。"
    finish_text = "✓ 获取完成"
    fail_text = "✕ 获取失败"

    def __init__(self, master, app_ref):
        super().__init__(master, app_ref)
        self.source_type = ctk.StringVar(value="🎙️ 名人经典演讲 (Steve Jobs, Churchill, MLK 等)")
        self.custom_work_var = ctk.StringVar(value="Steve Jobs Stanford Speech / 乔布斯斯坦福演讲")
        self.reading_len_var = ctk.StringVar(value="中篇节选 (~400词)")
        self.custom_len_entry_var = ctk.StringVar(value="1000")
        self.setup_ui()

    def setup_ui(self):
        cfg = self.app_ref.config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctrl_card = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=cfg.c_surface,
            border_width=1,
            border_color=cfg.c_border
        )
        ctrl_card.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 6))

        r1 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        r1.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(r1, text="选读来源", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left", padx=(0, 6))

        self.menu_src = ctk.CTkOptionMenu(
            r1,
            values=[
                "🎙️ 名人经典演讲 (Steve Jobs, Churchill, MLK 等)",
                "📖 世界经典文学名著 (1984, Gatsby, Little Prince 等)",
                "🎬 经典影视/纪录片原声独白与剧本",
                "🪐 哲学与社科深度随笔选读"
            ],
            variable=self.source_type,
            width=230,
            height=28,
            corner_radius=6,
            font=cfg.font_normal,
            dropdown_font=cfg.font_normal,
            fg_color=cfg.c_btn,
            button_color=cfg.c_btn,
            button_hover_color=cfg.c_btn_hover,
            dropdown_fg_color=cfg.c_surface,
            dropdown_text_color=cfg.c_text,
            text_color=cfg.c_text
        )
        self.menu_src.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(r1, text="篇目/演讲者", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left", padx=(0, 6))

        self.entry_work = ctk.CTkEntry(
            r1,
            textvariable=self.custom_work_var,
            placeholder_text="如: 1984 / 独立宣言 / 乔布斯斯坦福演讲",
            height=28,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            font=cfg.font_normal
        )
        self.entry_work.pack(side="left", fill="x", expand=True)

        r2 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        r2.pack(fill="x", padx=12, pady=(2, 10))

        ctk.CTkLabel(r2, text="篇幅", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left", padx=(0, 4))

        self.menu_len = ctk.CTkOptionMenu(
            r2,
            values=["短篇精选 (~200词)", "中篇节选 (~400词)", "长篇深度精读 (~600词)", "千字名篇节选 (~1000词)", "自定义字数"],
            variable=self.reading_len_var,
            width=135,
            height=26,
            corner_radius=6,
            font=cfg.font_normal,
            dropdown_font=cfg.font_normal,
            fg_color=cfg.c_btn,
            button_color=cfg.c_btn,
            button_hover_color=cfg.c_btn_hover,
            dropdown_fg_color=cfg.c_surface,
            dropdown_text_color=cfg.c_text,
            text_color=cfg.c_text,
            command=self.on_len_mode_change
        )
        self.menu_len.pack(side="left", padx=(0, 6))

        self.entry_custom_len = ctk.CTkEntry(
            r2,
            textvariable=self.custom_len_entry_var,
            width=46,
            height=26,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            font=cfg.font_normal
        )

        self.btn_run = ctk.CTkButton(
            r2,
            text="获取名篇精读",
            font=cfg.font_bold,
            height=28,
            corner_radius=6,
            fg_color=cfg.c_primary,
            hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_primary,
            command=self.start_generation
        )
        self.btn_run.pack(side="left", padx=(8, 8))

        self.status_label = ctk.CTkLabel(
            r2,
            text="就绪",
            font=cfg.font_small,
            text_color=cfg.c_text_secondary
        )
        self.status_label.pack(side="left")

        self.build_bilingual_display(
            "导出名篇",
            "原著 / 演讲英文 (右键划词可即时查词/加入生词库)",
            "中文译文对照",
        )

    def on_len_mode_change(self, val):
        if "自定义" in val:
            self.entry_custom_len.pack(side="left", padx=(0, 6), after=self.menu_len)
        else:
            self.entry_custom_len.pack_forget()

    def start_generation(self):
        src_type = self.source_type.get()
        work = self.custom_work_var.get().strip()

        len_mode = self.reading_len_var.get()
        target_len = f"{self.custom_len_entry_var.get().strip()} 词左右" if "自定义" in len_mode else len_mode

        self.prepare_stream("正在获取...")
        self.start_worker(src_type, work, target_len)

    def _worker(self, src_type, work, target_len):
        self.run_stream(AIService.fetch_authentic_reading_stream, src_type, work, target_len)
