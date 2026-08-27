import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import random
from services import AIService
from ui_components import ModernTextBox, FullscreenReader

class AcgStoryTab(ctk.CTkFrame):
    def __init__(self, master, app_ref):
        super().__init__(master, fg_color="transparent")
        self.app_ref = app_ref

        self.acg_category = ctk.StringVar(value="🎬 动画深度漫评与剧情杂谈")
        self.acg_custom_topic = ctk.StringVar(value="Cyberpunk / 赛博朋克科幻动画")
        self.acg_word_count_var = ctk.StringVar(value="5")
        self.acg_source_type = ctk.StringVar(value="随机从历史词库抽取")
        self.acg_len_var = ctk.StringVar(value="深度特稿 (~600词)")
        self.custom_len_entry_var = ctk.StringVar(value="1000")
        self.enable_extra_words = ctk.BooleanVar(value=False)
        self.extra_words_count = ctk.StringVar(value="3")

        self.view_mode = ctk.StringVar(value="📖 双语对照")
        self.zh_visible = True

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctrl_card = ctk.CTkFrame(self, corner_radius=8)
        ctrl_card.grid(row=0, column=0, sticky="ew", padx=4, pady=(2, 6))

        r1 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        r1.pack(fill="x", padx=10, pady=(6, 4))

        ctk.CTkLabel(r1, text="🎨 ACG 题材类型:", font=self.app_ref.config.font_normal).pack(side="left", padx=(0, 4))
        self.menu_cat = ctk.CTkOptionMenu(
            r1,
            values=[
                "🎬 动画深度漫评与剧情杂谈",
                "🎮 电子游戏世界观与评测报道",
                "🎵 动漫音乐/Galgame配乐/OST赏析",
                "🌆 赛博朋克与科幻二次元随笔",
                "🏆 泛二次元文化与行业观察"
            ],
            variable=self.acg_category,
            width=230,
            font=self.app_ref.config.font_normal,
            dropdown_font=self.app_ref.config.font_normal
        )
        self.menu_cat.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(r1, text="作品/焦点主题:", font=self.app_ref.config.font_normal).pack(side="left", padx=(0, 4))
        self.entry_topic = ctk.CTkEntry(r1, textvariable=self.acg_custom_topic, placeholder_text="如: 边缘行者 / 原神 / 命运石之门", width=260, font=self.app_ref.config.font_normal)
        self.entry_topic.pack(side="left", fill="x", expand=True)

        r2 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        r2.pack(fill="x", padx=10, pady=(2, 8))

        ctk.CTkLabel(r2, text="词源:", font=self.app_ref.config.font_normal).pack(side="left", padx=(0, 2))
        self.menu_source = ctk.CTkOptionMenu(
            r2,
            values=["随机从历史词库抽取", "抽取最近学习的单词", "从第一页当前输入框抽取"],
            variable=self.acg_source_type,
            width=165,
            font=self.app_ref.config.font_normal,
            dropdown_font=self.app_ref.config.font_normal
        )
        self.menu_source.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(r2, text="抽词数:", font=self.app_ref.config.font_small).pack(side="left", padx=(0, 2))
        self.entry_count = ctk.CTkEntry(r2, textvariable=self.acg_word_count_var, width=38, font=self.app_ref.config.font_small)
        self.entry_count.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(r2, text="字数:", font=self.app_ref.config.font_small).pack(side="left", padx=(4, 2))
        self.menu_acg_len = ctk.CTkOptionMenu(
            r2,
            values=["精简漫评 (~200词)", "深度特稿 (~600词)", "千字深度长文 (~1000词)", "自定义字数"],
            variable=self.acg_len_var,
            width=135,
            font=self.app_ref.config.font_small,
            dropdown_font=self.app_ref.config.font_small,
            command=self.on_len_mode_change
        )
        self.menu_acg_len.pack(side="left", padx=(0, 4))
        self.entry_custom_len = ctk.CTkEntry(r2, textvariable=self.custom_len_entry_var, width=50, font=self.app_ref.config.font_small)

        self.chk_extra = ctk.CTkCheckBox(r2, text="🎲 随机引入未学词", variable=self.enable_extra_words, font=self.app_ref.config.font_small)
        self.chk_extra.pack(side="left", padx=(6, 2))
        self.entry_extra_cnt = ctk.CTkEntry(r2, textvariable=self.extra_words_count, width=35, font=self.app_ref.config.font_small)
        self.entry_extra_cnt.pack(side="left", padx=(0, 8))

        self.btn_run = ctk.CTkButton(r2, text="🌸 生成特稿", font=self.app_ref.config.font_normal, height=30, fg_color="#9c27b0", hover_color="#7b1fa2", command=self.start_generation)
        self.btn_run.pack(side="left", padx=(0, 10))

        self.status_label = ctk.CTkLabel(r2, text="就绪", font=self.app_ref.config.font_small, text_color="#888888")
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
        ctk.CTkButton(view_bar, text="💾 导出特稿", width=85, height=24, font=self.app_ref.config.font_small, fg_color="#1f7a8c", hover_color="#175e6b", command=self.export_article).pack(side="right", padx=4)

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
        ctk.CTkLabel(h1, text="🌸 ACG 英文专栏特稿 (右键划词使用必应词典)", font=self.app_ref.config.font_normal, text_color=("#ab47bc", "#ce93d8")).pack(side="left")

        self.txt_en = ModernTextBox(self.card_en, self.app_ref, font=self.app_ref.config.font_body, corner_radius=4, wrap="word")
        self.txt_en.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))

        self.card_zh = ctk.CTkFrame(self.cards_frame, corner_radius=6, fg_color=("gray90", "#242424"))
        self.card_zh.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.card_zh.grid_columnconfigure(0, weight=1)
        self.card_zh.grid_rowconfigure(1, weight=1)

        h2 = ctk.CTkFrame(self.card_zh, fg_color="transparent")
        h2.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 2))
        ctk.CTkLabel(h2, text="🇨🇳 专栏中文译文与对照", font=self.app_ref.config.font_normal, text_color=("#2b7a78", "#80CBC4")).pack(side="left")

        self.btn_toggle_zh = ctk.CTkButton(h2, text="👁️ 隐藏译文", width=75, height=20, font=self.app_ref.config.font_small, fg_color="#555555", hover_color="#444444", command=self.toggle_zh)
        self.btn_toggle_zh.pack(side="right")

        self.txt_zh = ModernTextBox(self.card_zh, self.app_ref, font=self.app_ref.config.font_body, corner_radius=4, wrap="word")
        self.txt_zh.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))

    def on_len_mode_change(self, val):
        if "自定义" in val:
            self.entry_custom_len.pack(side="left", padx=(0, 4), after=self.menu_acg_len)
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
        FullscreenReader(self.winfo_toplevel(), self.app_ref, "二次元 ACG 特稿", en, zh)

    def export_article(self):
        en = self.txt_en.get("1.0", "end").strip()
        zh = self.txt_zh.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"=== ACG English Review ===\n\n{en}\n\n=== Chinese Translation ===\n\n{zh}\n")
            messagebox.showinfo("成功", "二次元特稿已保存！")

    def start_generation(self):
        hist = self.app_ref.config.vocab_history
        if not hist:
            messagebox.showwarning("提示", "词库暂无历史生词，请先在第一页添加！")
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
                messagebox.showwarning("提示", "第一页输入框中没有提取到单词！")
                return
            chosen_words = random.sample(words, min(target_count, len(words)))
        elif "最近学习" in src_type:
            chosen_words = hist[-target_count:] if len(hist) >= target_count else hist
        else:
            chosen_words = random.sample(hist, min(target_count, len(hist)))

        len_mode = self.acg_len_var.get()
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

        topic = self.acg_custom_topic.get().strip() or "Modern ACG Culture Trends"
        category = self.acg_category.get()

        self.btn_run.configure(state="disabled")
        self.status_label.configure(text=f"正在围绕 {len(chosen_words)} 词构思 {target_len} 特稿...", text_color="#9c27b0")
        self.txt_en.delete("1.0", "end")
        self.txt_zh.delete("1.0", "end")

        threading.Thread(target=self._worker, args=(chosen_words, extra_cnt, target_len, category, topic), daemon=True).start()

    def _worker(self, words, extra_cnt, target_len, category, topic):
        cfg = self.app_ref.config
        en, zh = AIService.generate_acg_story(words, extra_cnt, target_len, category, topic, cfg.difficulty, cfg.api_key, cfg.api_url, cfg.model_name)
        self.after(0, self._finish, en, zh)

    def _finish(self, en, zh):
        self.txt_en.insert("1.0", en)
        self.txt_zh.insert("1.0", zh)
        self.status_label.configure(text="🌸 ACG 特稿生成完成", text_color="#9c27b0")
        self.btn_run.configure(state="normal")
