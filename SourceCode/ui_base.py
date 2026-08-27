# ==============================================================================
# 文件路径: ui_base.py
# 包含组件: ModernTextBox, WordTranslationCard, FullscreenReader, UpdateDialog
# ==============================================================================
import re
import tkinter as tk
import webbrowser
import customtkinter as ctk
from services import FreeDictService, MicrosoftSpeechService, MicrosoftTranslatorService


class ModernTextBox(ctk.CTkTextbox):
    """支持划词右键翻译/朗读/加入生词库的高阶富文本框"""

    def __init__(self, master, app_ref, font=None, **kwargs):
        cfg = app_ref.config
        font_obj = font or cfg.font_normal
        super().__init__(
            master,
            font=font_obj,
            corner_radius=8,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text,
            wrap="word",
            **kwargs
        )
        self.app_ref = app_ref

        is_dark = ctk.get_appearance_mode() == "Dark"
        self._textbox.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(
            self,
            tearoff=0,
            font=(cfg.font_family, 12, "normal"),
            bg="#1E293B" if is_dark else "#FFFFFF",
            fg="#F8FAFC" if is_dark else "#0F172A",
            activebackground="#0284C7" if is_dark else "#38BDF8",
            activeforeground="#FFFFFF",
            relief="solid",
            bd=1
        )
        self.context_menu.add_command(label="  🔍  智能查词 / 微软翻译", command=self.on_translate_selected)
        self.context_menu.add_command(label="  🔊  微软原生语音朗读", command=self.on_speak_selected)
        self.context_menu.add_command(label="  ➕  收入本地生词库", command=self.on_add_to_vocab)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="  📋  复制选中文本", command=self.on_copy)

    def get_selected_word(self):
        try:
            sel_text = self._textbox.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            clean_word = re.sub(r"[^a-zA-Z\-]", "", sel_text).lower()
            return clean_word if clean_word else sel_text
        except tk.TclError:
            return ""

    def show_context_menu(self, event):
        word = self.get_selected_word()
        state = "normal" if word else "disabled"
        for i in range(3):
            self.context_menu.entryconfig(i, state=state)
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def on_copy(self):
        try:
            text = self._textbox.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)
        except tk.TclError:
            pass

    def on_speak_selected(self):
        word = self.get_selected_word()
        if word:
            cfg = self.app_ref.config
            MicrosoftSpeechService.speak_async(
                word, cfg.ms_speech_key, cfg.ms_speech_region, cfg.ms_voice_name
            )

    def on_translate_selected(self):
        word = self.get_selected_word()
        if word:
            WordTranslationCard(self.winfo_toplevel(), self.app_ref, word)

    def on_add_to_vocab(self):
        word = self.get_selected_word()
        if word:
            self.app_ref.config.vocab_repo.add_words([word])
            self.app_ref.update_global_vocab_status()


class WordTranslationCard(ctk.CTkToplevel):
    def __init__(self, master, app_ref, word):
        super().__init__(master)
        self.app_ref = app_ref
        self.word = word
        cfg = app_ref.config

        self.title(f"词典 · {word}")
        self.geometry("490x360")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=cfg.c_bg_window)
        self.after(10, self.lift)

        card = ctk.CTkFrame(
            self, corner_radius=12, fg_color=cfg.c_surface, border_width=1, border_color=cfg.c_border
        )
        card.pack(fill="both", expand=True, padx=14, pady=14)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(top_row, text=f"{word}", font=cfg.font_headline, text_color=cfg.c_primary).pack(side="left")
        ctk.CTkButton(
            top_row,
            text="🔊 朗读",
            width=65,
            height=26,
            corner_radius=13,
            font=cfg.font_small,
            fg_color=cfg.c_secondary,
            hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_secondary,
            command=self.play_voice
        ).pack(side="left", padx=12)

        engine_name = "微软必应翻译" if cfg.translate_engine == "微软必应翻译" else "智能双语词典"
        ctk.CTkLabel(top_row, text=f"[{engine_name}]", font=cfg.font_small, text_color=cfg.c_text_secondary).pack(side="right")

        self.lbl_phonetic = ctk.CTkLabel(
            card, text="正在解析释义与音标...", font=cfg.font_small, text_color=cfg.c_text_secondary
        )
        self.lbl_phonetic.pack(anchor="w", padx=14, pady=(0, 6))

        self.txt_detail = ModernTextBox(card, self.app_ref)
        self.txt_detail.pack(fill="both", expand=True, padx=14, pady=4)

        bottom_bar = ctk.CTkFrame(card, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=14, pady=(10, 12))

        self.btn_add = ctk.CTkButton(
            bottom_bar,
            text="＋ 收入生词库",
            font=cfg.font_normal,
            width=120,
            height=30,
            corner_radius=6,
            fg_color=cfg.c_primary,
            hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_primary,
            command=self.add_to_vocab
        )
        self.btn_add.pack(side="left")

        ctk.CTkButton(
            bottom_bar,
            text="完成",
            font=cfg.font_normal,
            width=70,
            height=30,
            corner_radius=6,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.destroy
        ).pack(side="right")

        self.fetch_definition()

    def play_voice(self):
        cfg = self.app_ref.config
        MicrosoftSpeechService.speak_async(
            self.word, cfg.ms_speech_key, cfg.ms_speech_region, cfg.ms_voice_name
        )

    def fetch_definition(self):
        cfg = self.app_ref.config
        if cfg.translate_engine == "微软必应翻译" and cfg.ms_translator_key:
            import threading

            def _ms_worker():
                try:
                    res = MicrosoftTranslatorService.lookup_word(
                        self.word, cfg.ms_translator_key, cfg.ms_translator_region
                    )
                except Exception as e:
                    res = {"phonetic": "[微软错误]", "pos_def": f"查询出错：{str(e)}", "example": ""}
                self.after(0, self.update_ui, res)

            threading.Thread(target=_ms_worker, daemon=True).start()
        else:
            FreeDictService.submit_lookup(self.word, lambda res: self.after(0, self.update_ui, res))

    def update_ui(self, res):
        self.lbl_phonetic.configure(text=res.get("phonetic", ""))
        text = f"【核心释义】\n{res.get('pos_def', '')}\n\n【典型例句】\n{res.get('example', '')}"
        self.txt_detail.delete("1.0", "end")
        self.txt_detail.insert("1.0", text)

    def add_to_vocab(self):
        self.app_ref.config.vocab_repo.add_words([self.word])
        self.app_ref.update_global_vocab_status()
        self.btn_add.configure(
            text="✓ 已在生词库",
            state="disabled",
            fg_color=self.app_ref.config.c_success_bg,
            text_color=self.app_ref.config.c_success
        )


class FullscreenReader(ctk.CTkToplevel):
    def __init__(self, master, app_ref, title_text, en_content, zh_content):
        super().__init__(master)
        self.app_ref = app_ref
        cfg = app_ref.config

        self.title(f"专注阅读 · {title_text}")
        self.geometry("1100x800")
        self.configure(fg_color=cfg.c_bg_window)
        self.bind("<Escape>", lambda e: self.destroy())

        top_bar = ctk.CTkFrame(
            self,
            height=46,
            corner_radius=10,
            fg_color=cfg.c_surface,
            border_width=1,
            border_color=cfg.c_border
        )
        top_bar.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(top_bar, text=f"📖 {title_text}", font=cfg.font_headline, text_color=cfg.c_text).pack(side="left", padx=14)
        ctk.CTkButton(
            top_bar,
            text="✕ 退出 (Esc)",
            width=85,
            height=26,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.destroy
        ).pack(side="right", padx=12)

        self.btn_toggle_mode = ctk.CTkSegmentedButton(
            top_bar,
            values=["📖 双语对照", "🔤 纯英文", "🇨🇳 纯中文"],
            font=cfg.font_small,
            corner_radius=8,
            selected_color=cfg.c_primary,
            unselected_color=cfg.c_surface_variant,
            text_color=cfg.c_text,
            command=self.change_mode
        )
        self.btn_toggle_mode.set("📖 双语对照")
        self.btn_toggle_mode.pack(side="right", padx=12)

        self.read_container = ctk.CTkFrame(self, fg_color="transparent")
        self.read_container.pack(fill="both", expand=True, padx=14, pady=(4, 14))
        self.read_container.grid_columnconfigure(0, weight=1)
        self.read_container.grid_rowconfigure(0, weight=1)
        self.read_container.grid_rowconfigure(1, weight=1)

        self.txt_en = ModernTextBox(self.read_container, self.app_ref, font=cfg.font_reader)
        self.txt_en.grid(row=0, column=0, sticky="nsew", pady=3)
        self.txt_en.insert("1.0", en_content)

        self.txt_zh = ModernTextBox(self.read_container, self.app_ref, font=cfg.font_reader)
        self.txt_zh.grid(row=1, column=0, sticky="nsew", pady=3)
        self.txt_zh.insert("1.0", zh_content)

    def change_mode(self, mode):
        if mode == "📖 双语对照":
            self.txt_en.grid(row=0, column=0, sticky="nsew", pady=3)
            self.txt_zh.grid(row=1, column=0, sticky="nsew", pady=3)
            self.read_container.grid_rowconfigure(0, weight=1)
            self.read_container.grid_rowconfigure(1, weight=1)
        elif mode == "🔤 纯英文":
            self.txt_zh.grid_forget()
            self.txt_en.grid(row=0, column=0, sticky="nsew", pady=0)
            self.read_container.grid_rowconfigure(0, weight=1)
            self.read_container.grid_rowconfigure(1, weight=0)
        elif mode == "🇨🇳 纯中文":
            self.txt_en.grid_forget()
            self.txt_zh.grid(row=0, column=0, sticky="nsew", pady=0)
            self.read_container.grid_rowconfigure(0, weight=1)
            self.read_container.grid_rowconfigure(1, weight=0)


class UpdateDialog(ctk.CTkToplevel):
    """发现新版本时的更新特性说明弹窗"""

    def __init__(self, master, app_ref, release_info):
        super().__init__(master)
        self.app_ref = app_ref
        self.release_info = release_info
        cfg = app_ref.config

        self.title("发现新版本")
        self.geometry("520x420")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=cfg.c_bg_window)
        self.after(10, self.lift)

        card = ctk.CTkFrame(self, corner_radius=12, fg_color=cfg.c_surface, border_width=1, border_color=cfg.c_border)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            top_row,
            text=f"🚀 发现新版本 {release_info.get('tag', '')}",
            font=cfg.font_headline,
            text_color=cfg.c_primary
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=f"发布于 {release_info.get('published_at', '')}",
            font=cfg.font_small,
            text_color=cfg.c_text_secondary
        ).pack(side="right")

        ctk.CTkLabel(card, text="更新内容与修复日志:", font=cfg.font_small, text_color=cfg.c_text).pack(anchor="w", padx=14, pady=(6, 2))

        txt_body = ctk.CTkTextbox(
            card,
            font=cfg.font_normal,
            corner_radius=6,
            border_width=1,
            border_color=cfg.c_border,
            fg_color=cfg.c_input_bg,
            text_color=cfg.c_text
        )
        txt_body.pack(fill="both", expand=True, padx=14, pady=4)
        txt_body.insert("1.0", release_info.get("body", "暂无详细说明"))
        txt_body.configure(state="disabled")

        bot_bar = ctk.CTkFrame(card, fg_color="transparent")
        bot_bar.pack(fill="x", padx=14, pady=(10, 12))

        ctk.CTkButton(
            bot_bar,
            text="稍后提醒",
            width=80,
            height=28,
            corner_radius=6,
            font=cfg.font_small,
            fg_color=cfg.c_btn,
            hover_color=cfg.c_btn_hover,
            text_color=cfg.c_text,
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            bot_bar,
            text="🌐 前往 GitHub 下载更新",
            width=160,
            height=28,
            corner_radius=6,
            font=cfg.font_bold,
            fg_color=cfg.c_primary,
            hover_color=cfg.c_primary_hover,
            text_color=cfg.c_on_primary,
            command=lambda: [webbrowser.open(release_info.get("html_url")), self.destroy()]
        ).pack(side="right")