import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from services import AIService
from ui_components import ModernTextBox, FullscreenReader

class AuthenticReadingTab(ctk.CTkFrame):
    def __init__(self, master, app_ref):
        super().__init__(master, fg_color="transparent")
        self.app_ref = app_ref

        self.source_type = ctk.StringVar(value="🎙️ 名人经典演讲 (Steve Jobs, Churchill, MLK 等)")
        self.custom_work_var = ctk.StringVar(value="Steve Jobs Stanford Speech / 乔布斯斯坦福演讲")
        self.reading_len_var = ctk.StringVar(value="中篇节选 (~400词)")
        self.custom_len_entry_var = ctk.StringVar(value="1000")
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

        ctk.CTkLabel(r1, text="📚 选读来源:", font=self.app_ref.config.font_normal).pack(side="left", padx=(0, 4))
        self.menu_src = ctk.CTkOptionMenu(
            r1,
            values=[
                "🎙️ 名人经典演讲 (Steve Jobs, Churchill, MLK 等)",
                "📖 世界经典文学名著 (1984, Gatsby, Little Prince 等)",
                "🎬 经典影视/纪录片原声独白与剧本",
                "🪐 哲学与社科深度随笔选读"
            ],
            variable=self.source_type,
            width=260,
            font=self.app_ref.config.font_normal,
            dropdown_font=self.app_ref.config.font_normal
        )
        self.menu_src.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(r1, text="指定作品/演讲者 (可选):", font=self.app_ref.config.font_normal).pack(side="left", padx=(0, 4))
        self.entry_work = ctk.CTkEntry(r1, textvariable=self.custom_work_var, placeholder_text="如: 1984 / 独立宣言 / 奥巴马胜选演讲", width=280, font=self.app_ref.config.font_normal)
        self.entry_work.pack(side="left", fill="x", expand=True)

        r2 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        r2.pack(fill="x", padx=10, pady=(2, 8))

        ctk.CTkLabel(r2, text="篇幅字数:", font=self.app_ref.config.font_small).pack(side="left", padx=(0, 4))
        self.menu_len = ctk.CTkOptionMenu(
            r2,
            values=["短篇精选 (~200词)", "中篇节选 (~400词)", "长篇深度精读 (~600词)", "千字名篇节选 (~1000词)", "自定义字数"],
            variable=self.reading_len_var,
            width=155,
            font=self.app_ref.config.font_small,
            dropdown_font=self.app_ref.config.font_small,
            command=self.on_len_mode_change
        )
        self.menu_len.pack(side="left", padx=(0, 4))
        self.entry_custom_len = ctk.CTkEntry(r2, textvariable=self.custom_len_entry_var, width=50, font=self.app_ref.config.font_small)

        self.btn_run = ctk.CTkButton(r2, text="📖 获取原著精读篇章", font=self.app_ref.config.font_normal, height=30, fg_color="#00897b", hover_color="#00695c", command=self.start_generation)
        self.btn_run.pack(side="left", padx=(10, 10))

        self.status_label = ctk.CTkLabel(r2, text="准备就绪", font=self.app_ref.config.font_small, text_color="#888888")
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
        ctk.CTkButton(view_bar, text="💾 导出名篇", width=85, height=24, font=self.app_ref.config.font_small, fg_color="#1f7a8c", hover_color="#175e6b", command=self.export_article).pack(side="right", padx=4)

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
        ctk.CTkLabel(h1, text="📖 原著/演讲英文精读 (右键划词使用必应词典)", font=self.app_ref.config.font_normal, text_color=("#00897b", "#80cbc4")).pack(side="left")

        self.txt_en = ModernTextBox(self.card_en, self.app_ref, font=self.app_ref.config.font_body, corner_radius=4, wrap="word")
        self.txt_en.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))

        self.card_zh = ctk.CTkFrame(self.cards_frame, corner_radius=6, fg_color=("gray90", "#242424"))
        self.card_zh.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.card_zh.grid_columnconfigure(0, weight=1)
        self.card_zh.grid_rowconfigure(1, weight=1)

        h2 = ctk.CTkFrame(self.card_zh, fg_color="transparent")
        h2.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 2))
        ctk.CTkLabel(h2, text="🇨🇳 精准双语翻译与对照", font=self.app_ref.config.font_normal, text_color=("#2b7a78", "#80CBC4")).pack(side="left")

        self.btn_toggle_zh = ctk.CTkButton(h2, text="👁️ 隐藏译文", width=75, height=20, font=self.app_ref.config.font_small, fg_color="#555555", hover_color="#444444", command=self.toggle_zh)
        self.btn_toggle_zh.pack(side="right")

        self.txt_zh = ModernTextBox(self.card_zh, self.app_ref, font=self.app_ref.config.font_body, corner_radius=4, wrap="word")
        self.txt_zh.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))

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
            messagebox.showwarning("提示", "当前没有内容可全屏阅读！")
            return
        FullscreenReader(self.winfo_toplevel(), self.app_ref, "名篇名著精读", en, zh)

    def export_article(self):
        en = self.txt_en.get("1.0", "end").strip()
        zh = self.txt_zh.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"=== Authentic English Reading ===\n\n{en}\n\n=== Chinese Translation ===\n\n{zh}\n")
            messagebox.showinfo("成功", "精读文章已保存！")

    def start_generation(self):
        src_type = self.source_type.get()
        work = self.custom_work_var.get().strip()

        len_mode = self.reading_len_var.get()
        if "自定义" in len_mode:
            target_len = f"{self.custom_len_entry_var.get().strip()} 词左右"
        else:
            target_len = len_mode

        self.btn_run.configure(state="disabled")
        self.status_label.configure(text=f"正在调取 {target_len} 名篇节选...", text_color="#00897b")
        self.txt_en.delete("1.0", "end")
        self.txt_zh.delete("1.0", "end")

        threading.Thread(target=self._worker, args=(src_type, work, target_len), daemon=True).start()

    def _worker(self, src_type, work, target_len):
        cfg = self.app_ref.config
        en, zh = AIService.fetch_authentic_reading(src_type, work, target_len, cfg.difficulty, cfg.api_key, cfg.api_url, cfg.model_name)
        self.after(0, self._finish, en, zh)

    def _finish(self, en, zh):
        self.txt_en.insert("1.0", en)
        self.txt_zh.insert("1.0", zh)
        self.status_label.configure(text="📖 名篇调取完毕", text_color="#00897b")
        self.btn_run.configure(state="normal")
