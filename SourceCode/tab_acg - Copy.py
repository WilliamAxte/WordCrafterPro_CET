import customtkinter as ctk
from tkinter import messagebox
import random

from services import AIService
from tab_base import BilingualContentTab

class AcgStoryTab(BilingualContentTab):
    fullscreen_title = "ACG 深度特稿"
    export_en_title = "ACG English Review"
    export_success_message = "特稿已保存。"

    def __init__(self, master, app_ref):
        super().__init__(master, app_ref)
        self.acg_category = ctk.StringVar(value="🎬 动画深度漫评与剧情杂谈")
        self.acg_custom_topic = ctk.StringVar(value="Cyberpunk / 赛博朋克科幻动画")
        self.acg_word_count_var = ctk.StringVar(value="5")
        self.acg_source_type = ctk.StringVar(value="随机从历史词库抽取")
        self.acg_len_var = ctk.StringVar(value="深度特稿 (~600词)")
        self.custom_len_entry_var = ctk.StringVar(value="1000")
        self.enable_extra_words = ctk.BooleanVar(value=False)
        self.extra_words_count = ctk.StringVar(value="3")

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

        ctk.CTkLabel(r1, text="题材分类", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left", padx=(0, 6))

        self.menu_cat = ctk.CTkOptionMenu(
            r1,
            values=[
                "🎬 动画深度漫评与剧情杂谈",
                "🎮 电子游戏世界观与评测报道",
                "🎵 动漫音乐/Galgame配乐/OST赏析",
                "🌆 赛博朋克与科幻随笔",
                "🏆 泛二次元文化观察"
            ],
            variable=self.acg_category,
            width=210,
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
        self.menu_cat.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(r1, text="作品/主题", font=cfg.font_bold, text_color=cfg.c_text).pack(side="left", padx=(0, 6))

        self.entry_topic = ctk.CTkEntry(
            r1,
            textvariable=self.acg_custom_topic,
            placeholder_text="如: 边缘行者 / 原神 / 命运石之门",
            height=28,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            font=cfg.font_normal
        )
        self.entry_topic.pack(side="left", fill="x", expand=True)

        r2 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        r2.pack(fill="x", padx=12, pady=(2, 10))

        ctk.CTkLabel(r2, text="词源", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left", padx=(0, 4))

        self.menu_source = ctk.CTkOptionMenu(
            r2,
            values=["随机从历史词库抽取", "抽取最近学习的单词", "从第一页当前输入框抽取"],
            variable=self.acg_source_type,
            width=150,
            height=26,
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
        self.menu_source.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(r2, text="词数", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left", padx=(0, 4))

        self.entry_count = ctk.CTkEntry(
            r2,
            textvariable=self.acg_word_count_var,
            width=36,
            height=26,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            font=cfg.font_normal
        )
        self.entry_count.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(r2, text="篇幅", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left", padx=(4, 4))

        self.menu_acg_len = ctk.CTkOptionMenu(
            r2,
            values=["精简漫评 (~200词)", "深度特稿 (~600词)", "千字深度长文 (~1000词)", "自定义字数"],
            variable=self.acg_len_var,
            width=125,
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
        self.menu_acg_len.pack(side="left", padx=(0, 6))

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

        self.chk_extra = ctk.CTkCheckBox(
            r2,
            text="拓展词汇",
            variable=self.enable_extra_words,
            font=cfg.font_small,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=4,
            fg_color=cfg.c_primary
        )
        self.chk_extra.pack(side="left", padx=(6, 4))

        self.entry_extra_cnt = ctk.CTkEntry(
            r2,
            textvariable=self.extra_words_count,
            width=32,
            height=26,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            font=cfg.font_normal
        )
        self.entry_extra_cnt.pack(side="left", padx=(0, 8))

        self.btn_run = ctk.CTkButton(
            r2,
            text="生成二次元特稿",
            font=cfg.font_bold,
            height=28,
            corner_radius=6,
            fg_color=cfg.c_primary,
            hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_primary,
            command=self.start_generation
        )
        self.btn_run.pack(side="left", padx=(0, 8))

        self.status_label = ctk.CTkLabel(
            r2,
            text="就绪",
            font=cfg.font_small,
            text_color=cfg.c_text_secondary
        )
        self.status_label.pack(side="left")

        self.build_bilingual_display(
            "导出特稿",
            "ACG 英文专栏 (右键划词可即时查词/加入生词库)",
            "专栏中文译文对照",
        )

    def on_len_mode_change(self, val):
        if "自定义" in val:
            self.entry_custom_len.pack(side="left", padx=(0, 6), after=self.menu_acg_len)
        else:
            self.entry_custom_len.pack_forget()

    def start_generation(self):
        hist = self.app_ref.config.vocab_history
        if not hist:
            messagebox.showwarning("提示", "词库暂无历史生词。")
            return

        try:
            target_count = int(self.acg_word_count_var.get().strip())
            target_count = max(1, target_count)
        except Exception:
            target_count = 5

        src_type = self.acg_source_type.get()
        if "第一页" in src_type:
            words = self.app_ref.page_vocab.parse_input_words()
            if not words:
                messagebox.showwarning("提示", "第一页输入框中无单词。")
                return
            chosen_words = random.sample(words, min(target_count, len(words)))
        elif "最近学习" in src_type:
            chosen_words = hist[-target_count:] if len(hist) >= target_count else hist
        else:
            chosen_words = random.sample(hist, min(target_count, len(hist)))

        len_mode = self.acg_len_var.get()
        target_len = f"{self.custom_len_entry_var.get().strip()} 词左右" if "自定义" in len_mode else len_mode

        extra_cnt = 0
        if self.enable_extra_words.get():
            try:
                extra_cnt = int(self.extra_words_count.get().strip())
            except Exception:
                extra_cnt = 3

        topic = self.acg_custom_topic.get().strip() or "Modern ACG Culture Trends"
        category = self.acg_category.get()

        self.prepare_stream("正在构思...")
        self.start_worker(chosen_words, extra_cnt, target_len, category, topic)

    def _worker(self, words, extra_cnt, target_len, category, topic):
        self.run_stream(
            AIService.generate_acg_story_stream,
            words, extra_cnt, target_len, category, topic,
        )
