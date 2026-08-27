# ==============================================================================
# 文件路径: ui_vocab_manager.py
# 包含组件: ModernWordCard, VocabManagerWindow
# ==============================================================================
import re
from tkinter import filedialog, messagebox
import customtkinter as ctk
from services import FreeDictService, MicrosoftSpeechService, MicrosoftTranslatorService


class ModernWordCard(ctk.CTkFrame):
    def __init__(self, master, app_ref, word, index, on_delete_callback):
        cfg = app_ref.config
        super().__init__(master, corner_radius=8, fg_color=cfg.c_input_bg, border_width=1, border_color=cfg.c_border)
        self.app_ref = app_ref
        self.word = word
        self.index = index
        self.on_delete_callback = on_delete_callback
        self.setup_card_ui()
        self.load_definition_async()

    def setup_card_ui(self):
        cfg = self.app_ref.config
        self.grid_columnconfigure(1, weight=1)

        self.idx_badge = ctk.CTkFrame(self, corner_radius=13, fg_color=cfg.c_secondary, width=26, height=26)
        self.idx_badge.grid(row=0, column=0, rowspan=2, padx=(10, 6), pady=10, sticky="n")
        self.idx_badge.grid_propagate(False)
        ctk.CTkLabel(
            self.idx_badge, text=f"{self.index}", font=cfg.font_small, text_color=cfg.c_on_secondary
        ).place(relx=0.5, rely=0.5, anchor="center")

        top_info_row = ctk.CTkFrame(self, fg_color="transparent")
        top_info_row.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(6, 2))

        ctk.CTkLabel(top_info_row, text=self.word, font=cfg.font_bold, text_color=cfg.c_primary).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            top_info_row,
            text="🔊",
            width=22,
            height=20,
            corner_radius=4,
            font=cfg.font_small,
            fg_color=cfg.c_surface,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.play_voice
        ).pack(side="left", padx=(0, 6))

        self.lbl_phonetic = ctk.CTkLabel(top_info_row, text="解析中...", font=cfg.font_small, text_color=cfg.c_text_secondary)
        self.lbl_phonetic.pack(side="left")

        ctk.CTkButton(
            top_info_row,
            text="✕",
            width=22,
            height=22,
            corner_radius=11,
            font=cfg.font_small,
            fg_color="transparent",
            hover_color=cfg.c_btn_del,
            text_color=cfg.c_error,
            command=lambda: self.on_delete_callback(self.word)
        ).pack(side="right")

        self.lbl_meaning = ctk.CTkLabel(
            self,
            text="正在调用词典解析释义...",
            font=cfg.font_normal,
            text_color=cfg.c_text,
            justify="left",
            wraplength=660
        )
        self.lbl_meaning.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=(0, 8))

    def play_voice(self):
        cfg = self.app_ref.config
        MicrosoftSpeechService.speak_async(
            self.word, cfg.ms_speech_key, cfg.ms_speech_region, cfg.ms_voice_name
        )

    def load_definition_async(self):
        cache = self.app_ref.config.vocab_repo.cache.get(self.word)
        if cache and cache.get("pos_def") and "暂未获取" not in cache.get("pos_def"):
            self.update_card_data(cache)
            return

        cfg = self.app_ref.config
        if cfg.translate_engine == "微软必应翻译" and cfg.ms_translator_key:
            import threading

            def _ms_worker():
                try:
                    res = MicrosoftTranslatorService.lookup_word(
                        self.word, cfg.ms_translator_key, cfg.ms_translator_region
                    )
                except Exception:
                    res = FreeDictService.lookup(self.word)
                self.after(0, self._on_fetched, res)

            threading.Thread(target=_ms_worker, daemon=True).start()
        else:
            FreeDictService.submit_lookup(self.word, lambda res: self.after(0, self._on_fetched, res))

    def _on_fetched(self, res):
        self.app_ref.config.vocab_repo.cache[self.word] = res
        self.app_ref.config.vocab_repo.save_cache()
        self.update_card_data(res)

    def update_card_data(self, res):
        if not self.winfo_exists():
            return
        self.lbl_phonetic.configure(text=res.get("phonetic", ""))
        self.lbl_meaning.configure(text=res.get("pos_def", "暂无中文释义").replace("\n", "   ·   "))


class VocabManagerWindow(ctk.CTkToplevel):
    def __init__(self, master, app_ref):
        super().__init__(master)
        self.app_ref = app_ref
        cfg = app_ref.config

        self.title("本地生词库")
        self.geometry("880x680")
        self.minsize(740, 540)
        self.attributes("-topmost", True)
        self.configure(fg_color=cfg.c_bg_window)
        self.after(10, self.lift)

        self.page = 1
        self.page_size = 20
        self.filtered_words = []

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        cfg = self.app_ref.config
        top_card = ctk.CTkFrame(self, corner_radius=10, fg_color=cfg.c_surface, border_width=1, border_color=cfg.c_border)
        top_card.pack(fill="x", padx=14, pady=(12, 6))

        self.lbl_stats = ctk.CTkLabel(top_card, text="", font=cfg.font_headline, text_color=cfg.c_text)
        self.lbl_stats.pack(side="left", padx=14, pady=10)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.on_search_change())
        ctk.CTkEntry(
            top_card,
            textvariable=self.search_var,
            placeholder_text="🔍 搜索生词...",
            width=180,
            height=30,
            corner_radius=15,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            font=cfg.font_normal
        ).pack(side="right", padx=14, pady=8)

        self.scroll_container = ctk.CTkScrollableFrame(
            self, corner_radius=10, fg_color=cfg.c_surface, border_width=1, border_color=cfg.c_border
        )
        self.scroll_container.pack(fill="both", expand=True, padx=14, pady=4)
        self.scroll_container.grid_columnconfigure(0, weight=1)

        self.page_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.page_bar.pack(fill="x", padx=14, pady=4)

        self.btn_prev = ctk.CTkButton(
            self.page_bar,
            text="◀ 上一页",
            width=75,
            height=26,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.prev_page
        )
        self.btn_prev.pack(side="left")

        self.lbl_page_info = ctk.CTkLabel(
            self.page_bar, text="第 1 / 1 页", font=cfg.font_small, text_color=cfg.c_text_secondary
        )
        self.lbl_page_info.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(
            self.page_bar,
            text="下一页 ▶",
            width=75,
            height=26,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.next_page
        )
        self.btn_next.pack(side="left")

        bot_bar = ctk.CTkFrame(self, fg_color="transparent")
        bot_bar.pack(fill="x", padx=14, pady=(4, 12))

        ctk.CTkButton(
            bot_bar,
            text="导出 TXT",
            width=80,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.export_vocab
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            bot_bar,
            text="导入 TXT",
            width=80,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.import_vocab
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            bot_bar,
            text="清空生词",
            width=80,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn_del,
            hover_color=cfg.c_btn_del_hover,
            text_color=cfg.c_error,
            command=self.clear_vocab
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            bot_bar,
            text="完成",
            width=70,
            height=28,
            corner_radius=6,
            font=cfg.font_normal,
            fg_color=cfg.c_primary,
            hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_primary,
            command=self.destroy
        ).pack(side="right")

    def on_search_change(self):
        self.page = 1
        self.refresh_data()

    def refresh_data(self):
        all_words = self.app_ref.config.vocab_history
        kw = self.search_var.get().strip().lower()
        self.filtered_words = [w for w in all_words if kw in w.lower()] if kw else list(all_words)
        total_words, total_letters = self.app_ref.config.vocab_repo.get_stats()
        self.lbl_stats.configure(text=f"生词库 · {total_words} 词 ({total_letters} 字母)")
        self.render_current_page()

    def render_current_page(self):
        for widget in self.scroll_container.winfo_children():
            widget.destroy()

        total = len(self.filtered_words)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.page = max(1, min(self.page, total_pages))

        self.lbl_page_info.configure(text=f"第 {self.page} / {total_pages} 页 (共 {total} 词)")
        self.btn_prev.configure(state="normal" if self.page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.page < total_pages else "disabled")

        if not self.filtered_words:
            ctk.CTkLabel(
                self.scroll_container,
                text="📭 词库暂无匹配生词",
                font=self.app_ref.config.font_normal,
                text_color=self.app_ref.config.c_text_secondary
            ).pack(pady=40)
            return

        start = (self.page - 1) * self.page_size
        for i, word in enumerate(self.filtered_words[start : start + self.page_size]):
            ModernWordCard(self.scroll_container, self.app_ref, word, start + i + 1, self.delete_single_word).pack(
                fill="x", padx=4, pady=3
            )

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.render_current_page()

    def next_page(self):
        total_pages = max(1, (len(self.filtered_words) + self.page_size - 1) // self.page_size)
        if self.page < total_pages:
            self.page += 1
            self.render_current_page()

    def delete_single_word(self, word):
        self.app_ref.config.vocab_repo.remove_word(word)
        self.app_ref.update_global_vocab_status()
        self.refresh_data()

    def export_vocab(self):
        words = self.app_ref.config.vocab_history
        if not words:
            messagebox.showinfo("提示", "词库暂无词汇。")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(", ".join(words))
            messagebox.showinfo("成功", f"已成功导出 {len(words)} 个单词。")

    def import_vocab(self):
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

        words = [re.sub(r"[^a-zA-Z\-]", "", w).lower() for w in re.split(r"[,，\n\r\t\s]+", content) if w.strip()]
        cnt = self.app_ref.config.vocab_repo.add_words(list(dict.fromkeys([w for w in words if w])))
        self.app_ref.update_global_vocab_status()
        self.refresh_data()
        messagebox.showinfo("成功", f"已成功导入 {cnt} 个新词汇。")

    def clear_vocab(self):
        if messagebox.askyesno("确认", "确定清空本地所有生词吗？"):
            self.app_ref.config.vocab_repo.clear_history()
            self.app_ref.update_global_vocab_status()
            self.refresh_data()