import customtkinter as ctk
from tkinter import filedialog, messagebox
import random
import re

from services import AIService
from tab_base import BilingualContentTab
from ui_components import CollapsibleCard

class VocabStoryTab(BilingualContentTab):
    fullscreen_title = "情境短文"
    export_en_title = "English Context Story"
    export_success_message = "短文已成功导出。"

    def __init__(self, master, app_ref):
        super().__init__(master, app_ref)
        self.word_mode = ctk.StringVar(value="全部使用")
        self.custom_count_var = ctk.StringVar(value="5")
        self.story_len_var = ctk.StringVar(value="长篇 (~600词)")
        self.custom_len_entry_var = ctk.StringVar(value="1000")
        self.enable_extra_words = ctk.BooleanVar(value=False)
        self.extra_words_count = ctk.StringVar(value="3")

        self.setup_ui()

    def setup_ui(self):
        cfg = self.app_ref.config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 抽屉式输入与参数卡片
        self.drawer_card = CollapsibleCard(
            self, self.app_ref, title="目标生词与生成参数", summary_text="长篇 (~600词) · 全部使用", initial_open=True
        )
        self.drawer_card.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 6))

        # 顶部快捷动作
        top_bar = ctk.CTkFrame(self.drawer_card.body_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=4, pady=(2, 4))

        ctk.CTkLabel(top_bar, text="目标生词 (支持逗号/空格/换行隔开):", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left")

        ctk.CTkButton(
            top_bar, text="清空", width=55, height=22, corner_radius=6,
            font=cfg.font_small, fg_color=cfg.c_btn, hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text, command=self.clear_input
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            top_bar, text="导入 TXT", width=70, height=22, corner_radius=6,
            font=cfg.font_small, fg_color=cfg.c_btn, hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text, command=self.import_txt_file
        ).pack(side="right")

        self.word_input = ctk.CTkTextbox(
            self.drawer_card.body_frame, height=44, font=cfg.font_normal, corner_radius=6,
            border_width=1, border_color=cfg.c_border, fg_color=cfg.c_input_bg,
            text_color=cfg.c_text
        )
        self.word_input.pack(fill="x", padx=4, pady=2)
        self.word_input.insert("1.0", "serendipity, persist, hesitate, fragile, resilient")

        action_bar = ctk.CTkFrame(self.drawer_card.body_frame, fg_color="transparent")
        action_bar.pack(fill="x", padx=4, pady=(6, 2))

        self.btn_run = ctk.CTkButton(
            action_bar, text="🚀 生成情境短文", font=cfg.font_bold, height=28,
            corner_radius=6, fg_color=cfg.c_primary, hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_primary, command=self.start_generation
        )
        self.btn_run.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(action_bar, text="抽词", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left", padx=(0, 4))
        self.menu_word_mode = ctk.CTkOptionMenu(
            action_bar, values=["全部使用", "随机抽取 3 个", "随机抽取 5 个", "随机抽取 8 个", "自定义抽词量"],
            variable=self.word_mode, width=115, height=26, corner_radius=6,
            font=cfg.font_normal, dropdown_font=cfg.font_normal,
            fg_color=cfg.c_btn, button_color=cfg.c_btn, button_hover_color=cfg.c_btn_hover,
            dropdown_fg_color=cfg.c_surface, dropdown_text_color=cfg.c_text,
            text_color=cfg.c_text, command=self.on_word_mode_change
        )
        self.menu_word_mode.pack(side="left", padx=(0, 6))

        self.entry_custom_count = ctk.CTkEntry(
            action_bar, textvariable=self.custom_count_var, width=40, height=26,
            corner_radius=6, border_width=1, border_color=cfg.c_border,
            fg_color=cfg.c_input_bg, text_color=cfg.c_text, font=cfg.font_normal
        )

        ctk.CTkLabel(action_bar, text="篇幅", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="left", padx=(4, 4))
        self.menu_len = ctk.CTkOptionMenu(
            action_bar, values=["短篇 (~200词)", "中篇 (~400词)", "长篇 (~600词)", "千字长篇 (~1000词)", "自定义字数"],
            variable=self.story_len_var, width=125, height=26, corner_radius=6,
            font=cfg.font_normal, dropdown_font=cfg.font_normal,
            fg_color=cfg.c_btn, button_color=cfg.c_btn, button_hover_color=cfg.c_btn_hover,
            dropdown_fg_color=cfg.c_surface, dropdown_text_color=cfg.c_text,
            text_color=cfg.c_text, command=self.on_len_mode_change
        )
        self.menu_len.pack(side="left", padx=(0, 6))

        self.entry_custom_len = ctk.CTkEntry(
            action_bar, textvariable=self.custom_len_entry_var, width=46, height=26,
            corner_radius=6, border_width=1, border_color=cfg.c_border,
            fg_color=cfg.c_input_bg, text_color=cfg.c_text, font=cfg.font_normal
        )

        self.chk_extra = ctk.CTkCheckBox(
            action_bar, text="拓展生词", variable=self.enable_extra_words,
            font=cfg.font_small, checkbox_width=16, checkbox_height=16,
            corner_radius=4, fg_color=cfg.c_primary
        )
        self.chk_extra.pack(side="left", padx=(6, 4))

        self.entry_extra_cnt = ctk.CTkEntry(
            action_bar, textvariable=self.extra_words_count, width=32, height=26,
            corner_radius=6, border_width=1, border_color=cfg.c_border,
            fg_color=cfg.c_input_bg, text_color=cfg.c_text, font=cfg.font_normal
        )
        self.entry_extra_cnt.pack(side="left", padx=(0, 8))

        self.status_label = ctk.CTkLabel(action_bar, text="就绪", font=cfg.font_small, text_color=cfg.c_text_secondary)
        self.status_label.pack(side="left")

        self.build_bilingual_display(
            "导出短文",
            "英文短文 (右键划词可即时查词/朗读/收入生词库)",
            "中文精准对照",
        )

    def on_word_mode_change(self, val):
        if "自定义" in val:
            self.entry_custom_count.pack(side="left", padx=(0, 6), after=self.menu_word_mode)
        else:
            self.entry_custom_count.pack_forget()

    def on_len_mode_change(self, val):
        if "自定义" in val:
            self.entry_custom_len.pack(side="left", padx=(0, 6), after=self.menu_len)
        else:
            self.entry_custom_len.pack_forget()

    def clear_input(self):
        self.word_input.delete("1.0", "end")

    def parse_input_words(self):
        text = self.word_input.get("1.0", "end").strip()
        cleaned = re.split(r'[,，\n\r\t\s]+', text)
        words = [re.sub(r'[^a-zA-Z\-]', '', w).lower() for w in cleaned if w.strip()]
        return list(dict.fromkeys([w for w in words if w]))

    def import_txt_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not path:
            return
        for enc in ["utf-8", "gbk", "ansi"]:
            try:
                with open(path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except Exception:
                continue
        else:
            messagebox.showerror("错误", "编码不支持。")
            return

        words = [re.sub(r'[^a-zA-Z\-]', '', w).lower() for w in re.split(r'[,，\n\r\t\s]+', content) if w.strip()]
        words = list(dict.fromkeys([w for w in words if w]))
        self.word_input.delete("1.0", "end")
        self.word_input.insert("1.0", ", ".join(words))

    def start_generation(self):
        all_words = self.parse_input_words()
        if not all_words:
            messagebox.showwarning("提示", "请输入至少一个单词。")
            return

        mode = self.word_mode.get()
        chosen_words = all_words
        if "3 个" in mode:
            chosen_words = random.sample(all_words, min(3, len(all_words)))
        elif "5 个" in mode:
            chosen_words = random.sample(all_words, min(5, len(all_words)))
        elif "8 个" in mode:
            chosen_words = random.sample(all_words, min(8, len(all_words)))
        elif "自定义" in mode:
            try:
                cnt = int(self.custom_count_var.get().strip())
                chosen_words = random.sample(all_words, max(1, min(cnt, len(all_words))))
            except Exception:
                chosen_words = all_words

        len_mode = self.story_len_var.get()
        target_len = f"{self.custom_len_entry_var.get().strip()} 词左右" if "自定义" in len_mode else len_mode

        extra_cnt = 0
        if self.enable_extra_words.get():
            try:
                extra_cnt = int(self.extra_words_count.get().strip())
            except Exception:
                extra_cnt = 3

        self.app_ref.config.vocab_repo.add_words(chosen_words)
        self.app_ref.update_global_vocab_status()

        self.prepare_stream("正在构思生成...")
        self.start_worker(chosen_words, extra_cnt, target_len)

    def _worker(self, words, extra_cnt, target_len):
        self.run_stream(AIService.generate_vocab_story_stream, words, extra_cnt, target_len)