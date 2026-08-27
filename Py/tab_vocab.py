import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import random
import re
from services import AIService
from ui_components import ModernTextBox, FullscreenReader

class VocabStoryTab(ctk.CTkFrame):
    def __init__(self, master, app_ref):
        super().__init__(master, fg_color="transparent")
        self.app_ref = app_ref
        
        self.word_mode = ctk.StringVar(value="全部使用")
        self.custom_count_var = ctk.StringVar(value="5")
        self.story_len_var = ctk.StringVar(value="长篇 (~600词)")
        self.custom_len_entry_var = ctk.StringVar(value="1000")
        self.enable_extra_words = ctk.BooleanVar(value=False)
        self.extra_words_count = ctk.StringVar(value="3")

        self.view_mode = ctk.StringVar(value="📖 双语对照")
        self.zh_visible = True

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        input_card = ctk.CTkFrame(self, corner_radius=8)
        input_card.grid(row=0, column=0, sticky="ew", padx=4, pady=(2, 6))

        top_bar = ctk.CTkFrame(input_card, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(top_bar, text="🎯 目标生词输入 (支持逗号、空格或换行隔开):", font=self.app_ref.config.font_normal).pack(side="left")

        ctk.CTkButton(top_bar, text="清空输入", width=65, height=24, font=self.app_ref.config.font_small, fg_color="#555555", hover_color="#333333", command=self.clear_input).pack(side="right", padx=(4, 0))
        ctk.CTkButton(top_bar, text="📂 导入 TXT", width=80, height=24, font=self.app_ref.config.font_small, fg_color="#2b7a78", hover_color="#205e5c", command=self.import_txt_file).pack(side="right", padx=4)

        self.word_input = ctk.CTkTextbox(input_card, height=50, font=self.app_ref.config.font_body, corner_radius=6)
        self.word_input.pack(fill="x", padx=10, pady=4)
        self.word_input.insert("1.0", "serendipity, persist, hesitate, fragile, resilient")

        action_bar = ctk.CTkFrame(input_card, fg_color="transparent")
        action_bar.pack(fill="x", padx=10, pady=(2, 6))

        self.btn_run = ctk.CTkButton(action_bar, text="✨ 生成情境短文", font=self.app_ref.config.font_normal, height=30, command=self.start_generation)
        self.btn_run.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(action_bar, text="用词数:", font=self.app_ref.config.font_small).pack(side="left", padx=(0, 2))
        self.menu_word_mode = ctk.CTkOptionMenu(
            action_bar,
            values=["全部使用", "随机抽取 3 个", "随机抽取 5 个", "随机抽取 8 个", "自定义抽词量"],
            variable=self.word_mode,
            width=115,
            font=self.app_ref.config.font_small,
            dropdown_font=self.app_ref.config.font_small,
            command=self.on_word_mode_change
        )
        self.menu_word_mode.pack(side="left", padx=(0, 4))
        self.entry_custom_count = ctk.CTkEntry(action_bar, textvariable=self.custom_count_var, width=40, font=self.app_ref.config.font_small)

        ctk.CTkLabel(action_bar, text="目标字数:", font=self.app_ref.config.font_small).pack(side="left", padx=(6, 2))
        self.menu_len = ctk.CTkOptionMenu(
            action_bar,
            values=["短篇 (~200词)", "中篇 (~400词)", "长篇 (~600词)", "千字长篇 (~1000词)", "自定义字数"],
            variable=self.story_len_var,
            width=135,
            font=self.app_ref.config.font_small,
            dropdown_font=self.app_ref.config.font_small,
            command=self.on_len_mode_change
        )
        self.menu_len.pack(side="left", padx=(0, 4))
        self.entry_custom_len = ctk.CTkEntry(action_bar, textvariable=self.custom_len_entry_var, width=50, font=self.app_ref.config.font_small)

        self.chk_extra = ctk.CTkCheckBox(action_bar, text="🎲 随机引入未学词", variable=self.enable_extra_words, font=self.app_ref.config.font_small)
        self.chk_extra.pack(side="left", padx=(8, 2))
        self.entry_extra_cnt = ctk.CTkEntry(action_bar, textvariable=self.extra_words_count, width=35, font=self.app_ref.config.font_small)
        self.entry_extra_cnt.pack(side="left", padx=(0, 8))

        self.status_label = ctk.CTkLabel(action_bar, text="就绪", font=self.app_ref.config.font_small, text_color="#888888")
        self.status_label.pack(side="left")

        display_frame = ctk.CTkFrame(self, corner_radius=8)
        display_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_rowconfigure(1, weight=1)

        view_bar = ctk.CTkFrame(display_frame, fg_color="transparent")
        view_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 4))

        ctk.CTkLabel(view_bar, text="📖 阅读模式:", font=self.app_ref.config.font_normal).pack(side="left", padx=(0, 8))
        self.seg_view = ctk.CTkSegmentedButton(
            view_bar,
            values=["📖 双语对照", "🔤 纯英文沉浸", "🇨🇳 仅看中文"],
            variable=self.view_mode,
            font=self.app_ref.config.font_small,
            command=self.change_view_mode
        )
        self.seg_view.pack(side="left")

        ctk.CTkButton(view_bar, text="⛶ 全屏阅读", width=85, height=24, font=self.app_ref.config.font_small, fg_color="#673ab7", hover_color="#512da8", command=self.open_fullscreen).pack(side="right", padx=(4, 0))
        ctk.CTkButton(view_bar, text="💾 导出文章", width=85, height=24, font=self.app_ref.config.font_small, fg_color="#1f7a8c", hover_color="#175e6b", command=self.export_article).pack(side="right", padx=4)

        self.cards_frame = ctk.CTkFrame(display_frame, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 6))
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_rowconfigure(0, weight=1)
        self.cards_frame.grid_rowconfigure(1, weight=1)

        self.card_en = ctk.CTkFrame(self.cards_frame, corner_radius=6, fg_color=("gray90", "#242424"))
        self.card_en.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        self.card_en.grid_columnconfigure(0, weight=1)
        self.card_en.grid_rowconfigure(1, weight=1)

        h1 = ctk.CTkFrame(self.card_en, fg_color="transparent")
        h1.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 2))
        ctk.CTkLabel(h1, text="🔤 极简语境短文 (选词右键可必应查词/加入词库)", font=self.app_ref.config.font_normal, text_color=("#1f538d", "#64B5F6")).pack(side="left")

        self.txt_en = ModernTextBox(self.card_en, self.app_ref, font=self.app_ref.config.font_body, corner_radius=4, wrap="word")
        self.txt_en.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))

        self.card_zh = ctk.CTkFrame(self.cards_frame, corner_radius=6, fg_color=("gray90", "#242424"))
        self.card_zh.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.card_zh.grid_columnconfigure(0, weight=1)
        self.card_zh.grid_rowconfigure(1, weight=1)

        h2 = ctk.CTkFrame(self.card_zh, fg_color="transparent")
        h2.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 2))
        ctk.CTkLabel(h2, text="🇨🇳 全文精准双语对照", font=self.app_ref.config.font_normal, text_color=("#2b7a78", "#80CBC4")).pack(side="left")

        self.btn_toggle_zh = ctk.CTkButton(h2, text="👁️ 隐藏译文", width=75, height=20, font=self.app_ref.config.font_small, fg_color="#555555", hover_color="#444444", command=self.toggle_zh)
        self.btn_toggle_zh.pack(side="right")

        self.txt_zh = ModernTextBox(self.card_zh, self.app_ref, font=self.app_ref.config.font_body, corner_radius=4, wrap="word")
        self.txt_zh.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))

    def on_word_mode_change(self, val):
        if "自定义" in val:
            self.entry_custom_count.pack(side="left", padx=(0, 4), after=self.menu_word_mode)
        else:
            self.entry_custom_count.pack_forget()

    def on_len_mode_change(self, val):
        if "自定义" in val:
            self.entry_custom_len.pack(side="left", padx=(0, 4), after=self.menu_len)
        else:
            self.entry_custom_len.pack_forget()

    def change_view_mode(self, mode):
        if mode == "📖 双语对照":
            self.card_en.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
            self.card_zh.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
            self.cards_frame.grid_rowconfigure(0, weight=1)
            self.cards_frame.grid_rowconfigure(1, weight=1)
        elif mode == "🔤 纯英文沉浸":
            self.card_zh.grid_forget()
            self.card_en.grid(row=0, column=0, sticky="nsew", pady=0)
            self.cards_frame.grid_rowconfigure(0, weight=1)
            self.cards_frame.grid_rowconfigure(1, weight=0)
        elif mode == "🇨🇳 仅看中文":
            self.card_en.grid_forget()
            self.card_zh.grid(row=0, column=0, sticky="nsew", pady=0)
            self.cards_frame.grid_rowconfigure(0, weight=1)
            self.cards_frame.grid_rowconfigure(1, weight=0)

    def toggle_zh(self):
        if self.zh_visible:
            self.txt_zh.grid_remove()
            self.btn_toggle_zh.configure(text="👁️ 展开译文")
        else:
            self.txt_zh.grid()
            self.btn_toggle_zh.configure(text="👁️ 隐藏译文")
        self.zh_visible = not self.zh_visible

    def open_fullscreen(self):
        en = self.txt_en.get("1.0", "end").strip()
        zh = self.txt_zh.get("1.0", "end").strip()
        if not en and not zh:
            messagebox.showwarning("提示", "当前没有生成内容可全屏阅读！")
            return
        FullscreenReader(self.winfo_toplevel(), self.app_ref, "单词情境短文", en, zh)

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
            messagebox.showerror("错误", "无法识别该文件编码！")
            return

        words = [re.sub(r'[^a-zA-Z\-]', '', w).lower() for w in re.split(r'[,，\n\r\t\s]+', content) if w.strip()]
        words = list(dict.fromkeys([w for w in words if w]))
        self.word_input.delete("1.0", "end")
        self.word_input.insert("1.0", ", ".join(words))

    def export_article(self):
        en = self.txt_en.get("1.0", "end").strip()
        zh = self.txt_zh.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"=== English Context Story ===\n\n{en}\n\n=== Chinese Translation ===\n\n{zh}\n")
            messagebox.showinfo("成功", "短文已成功导出！")

    def start_generation(self):
        all_words = self.parse_input_words()
        if not all_words:
            messagebox.showwarning("提示", "请输入至少一个英文单词！")
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
        if "自定义" in len_mode:
            target_len = f"{self.custom_len_entry_var.get().strip()} 词左右"
        else:
            target_len = len_mode

        extra_cnt = 0
        if self.enable_extra_words.get():
            try:
                extra_cnt = int(self.extra_words_count.get().strip())
            except Exception:
                extra_cnt = 3

        self.app_ref.config.add_words_to_history(chosen_words)
        self.app_ref.update_global_vocab_status()

        self.btn_run.configure(state="disabled")
        self.status_label.configure(text=f"正在串联 {len(chosen_words)} 词生成 {target_len} 短文...", text_color="#3a7ebf")
        self.txt_en.delete("1.0", "end")
        self.txt_zh.delete("1.0", "end")

        threading.Thread(target=self._worker, args=(chosen_words, extra_cnt, target_len), daemon=True).start()

    def _worker(self, words, extra_cnt, target_len):
        cfg = self.app_ref.config
        en, zh = AIService.generate_vocab_story(words, extra_cnt, target_len, cfg.difficulty, cfg.api_key, cfg.api_url, cfg.model_name)
        self.after(0, self._finish, en, zh)

    def _finish(self, en, zh):
        self.txt_en.insert("1.0", en)
        self.txt_zh.insert("1.0", zh)
        self.status_label.configure(text="✅ 短文生成完成", text_color="#2b7a78")
        self.btn_run.configure(state="normal")
