import threading

import customtkinter as ctk
from tkinter import filedialog, messagebox

from services import StreamRouter
from ui_components import FullscreenReader, ModernTextBox


class BilingualContentTab(ctk.CTkFrame):
    """三个双语内容页共享的展示、导出与流式生成逻辑。"""

    fullscreen_title = ""
    export_en_title = "English"
    export_success_message = "已保存。"
    finish_text = "✓ 生成完成"
    fail_text = "✕ 生成失败"

    def __init__(self, master, app_ref):
        super().__init__(master, fg_color="transparent")
        self.app_ref = app_ref
        self.view_mode = ctk.StringVar(value="📖 双语对照")
        self.zh_visible = True

    def build_bilingual_display(self, export_button_text, en_title, zh_title):
        cfg = self.app_ref.config
        display_frame = ctk.CTkFrame(
            self, corner_radius=10, fg_color=cfg.c_surface,
            border_width=1, border_color=cfg.c_border
        )
        display_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=(2, 2))
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_rowconfigure(1, weight=1)

        view_bar = ctk.CTkFrame(display_frame, fg_color="transparent")
        view_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))

        self.seg_view = ctk.CTkSegmentedButton(
            view_bar,
            values=["📖 双语对照", "🔤 纯英文", "🇨🇳 仅看中文"],
            variable=self.view_mode,
            font=cfg.font_small,
            corner_radius=6,
            selected_color=cfg.c_primary,
            unselected_color=cfg.c_surface_variant,
            text_color=cfg.c_text,
            command=self.change_view_mode,
        )
        self.seg_view.pack(side="left")

        for text, command, padx in (
            ("全屏沉浸", self.open_fullscreen, (6, 0)),
            (export_button_text, self.export_article, 0),
        ):
            ctk.CTkButton(
                view_bar, text=text, width=75, height=26, corner_radius=6,
                font=cfg.font_small, fg_color=cfg.c_btn,
                hover_color=cfg.c_btn_hover, text_color=cfg.c_text,
                command=command,
            ).pack(side="right", padx=padx)

        self.cards_frame = ctk.CTkFrame(display_frame, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_rowconfigure(0, weight=1)
        self.cards_frame.grid_rowconfigure(1, weight=1)

        self.card_en = self._build_text_card(
            self.cards_frame, row=0, pady=(0, 3), title=en_title,
            title_color=cfg.c_primary, with_toggle=False
        )
        self.txt_en = ModernTextBox(self.card_en, self.app_ref)
        self.txt_en.grid(row=1, column=0, sticky="nsew")

        self.card_zh = self._build_text_card(
            self.cards_frame, row=1, pady=(3, 0), title=zh_title,
            title_color=cfg.c_text, with_toggle=True
        )
        self.txt_zh = ModernTextBox(self.card_zh, self.app_ref)
        self.txt_zh.grid(row=1, column=0, sticky="nsew")

    def _build_text_card(self, parent, row, pady, title, title_color, with_toggle):
        cfg = self.app_ref.config
        card = ctk.CTkFrame(parent, fg_color="transparent")
        card.grid(row=row, column=0, sticky="nsew", pady=pady)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 2))
        ctk.CTkLabel(
            header, text=title, font=cfg.font_bold, text_color=title_color
        ).pack(side="left")

        if with_toggle:
            self.btn_toggle_zh = ctk.CTkButton(
                header, text="隐藏译文", width=65, height=20, corner_radius=4,
                font=cfg.font_small, fg_color=cfg.c_btn,
                hover_color=cfg.c_btn_hover, text_color=cfg.c_text,
                command=self.toggle_zh,
            )
            self.btn_toggle_zh.pack(side="right")
        return card

    def change_view_mode(self, mode):
        if mode == "📖 双语对照":
            self.card_en.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
            self.card_zh.grid(row=1, column=0, sticky="nsew", pady=(3, 0))
            weights = (1, 1)
        elif mode == "🔤 纯英文":
            self.card_zh.grid_forget()
            self.card_en.grid(row=0, column=0, sticky="nsew", pady=0)
            weights = (1, 0)
        elif mode == "🇨🇳 仅看中文":
            self.card_en.grid_forget()
            self.card_zh.grid(row=0, column=0, sticky="nsew", pady=0)
            weights = (1, 0)
        else:
            return
        self.cards_frame.grid_rowconfigure(0, weight=weights[0])
        self.cards_frame.grid_rowconfigure(1, weight=weights[1])

    def toggle_zh(self):
        if self.zh_visible:
            self.txt_zh.grid_remove()
            self.btn_toggle_zh.configure(text="展开译文")
        else:
            self.txt_zh.grid()
            self.btn_toggle_zh.configure(text="隐藏译文")
        self.zh_visible = not self.zh_visible

    def _content(self):
        return (
            self.txt_en.get("1.0", "end").strip(),
            self.txt_zh.get("1.0", "end").strip(),
        )

    def open_fullscreen(self):
        en, zh = self._content()
        if not en and not zh:
            messagebox.showwarning("提示", "当前无内容。")
            return
        FullscreenReader(self.winfo_toplevel(), self.app_ref, self.fullscreen_title, en, zh)

    def export_article(self):
        en, zh = self._content()
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files", "*.txt")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                f"=== {self.export_en_title} ===\n\n{en}\n\n"
                f"=== Chinese Translation ===\n\n{zh}\n"
            )
        messagebox.showinfo("成功", self.export_success_message)

    def prepare_stream(self, status_text):
        self.btn_run.configure(state="disabled")
        self.status_label.configure(text=status_text, text_color=self.app_ref.config.c_primary)
        self.txt_en.delete("1.0", "end")
        self.txt_zh.delete("1.0", "end")

    def start_worker(self, *args):
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def run_stream(self, generator, *args):
        cfg = self.app_ref.config
        router = StreamRouter(self.txt_en, self.txt_zh)

        def on_token(token):
            self.after(0, router.feed, token)

        try:
            generator(
                *args, cfg.difficulty, cfg.api_key, cfg.api_url, cfg.model_name, on_token
            )
            self.after(0, router.close)
            self.after(0, self._finish)
        except Exception as exc:
            self.after(0, self._handle_error, str(exc))

    def _finish(self):
        self.status_label.configure(
            text=self.finish_text, text_color=self.app_ref.config.c_success
        )
        self.btn_run.configure(state="normal")

    def _handle_error(self, err):
        self.status_label.configure(
            text=self.fail_text, text_color=self.app_ref.config.c_error
        )
        self.btn_run.configure(state="normal")
        messagebox.showerror("生成错误", str(err))
