import tkinter as tk
import customtkinter as ctk
import re
import threading
from tkinter import filedialog, messagebox
from services import FreeDictService

class ModernTextBox(ctk.CTkTextbox):
    def __init__(self, master, app_ref, **kwargs):
        super().__init__(master, **kwargs)
        self.app_ref = app_ref
        
        self._textbox.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(self, tearoff=0, font=("Microsoft YaHei UI", 10))
        self.context_menu.add_command(label="🔍 微软必应即时查词 (Translate)", command=self.on_translate_selected)
        self.context_menu.add_command(label="➕ 添加到生词库 (Add to Vocab)", command=self.on_add_to_vocab)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 复制 (Copy)", command=self.on_copy)

    def get_selected_word(self):
        try:
            sel_text = self._textbox.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            clean_word = re.sub(r'[^a-zA-Z\-]', '', sel_text).lower()
            return clean_word if clean_word else sel_text
        except tk.TclError:
            return ""

    def show_context_menu(self, event):
        word = self.get_selected_word()
        if word:
            self.context_menu.entryconfig(0, state="normal")
            self.context_menu.entryconfig(1, state="normal")
        else:
            self.context_menu.entryconfig(0, state="disabled")
            self.context_menu.entryconfig(1, state="disabled")
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def on_copy(self):
        try:
            text = self._textbox.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)
        except tk.TclError:
            pass

    def on_translate_selected(self):
        word = self.get_selected_word()
        if word:
            WordTranslationCard(self.winfo_toplevel(), self.app_ref, word)

    def on_add_to_vocab(self):
        word = self.get_selected_word()
        if word:
            self.app_ref.config.add_words_to_history([word])
            self.app_ref.update_global_vocab_status()


class WordTranslationCard(ctk.CTkToplevel):
    def __init__(self, master, app_ref, word):
        super().__init__(master)
        self.app_ref = app_ref
        self.word = word

        self.title(f"微软必应查词 - {word}")
        self.geometry("450x320")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.after(10, self.lift)

        card = ctk.CTkFrame(self, corner_radius=10)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(10, 2))

        self.lbl_word = ctk.CTkLabel(top_row, text=f"{word}", font=ctk.CTkFont(family="Microsoft YaHei UI", size=19, weight="normal"), text_color=("#1f538d", "#64B5F6"))
        self.lbl_word.pack(side="left")

        ctk.CTkLabel(top_row, text="🌐 必应免Key免费词典", font=self.app_ref.config.font_small, text_color="#888888").pack(side="right")

        self.lbl_phonetic = ctk.CTkLabel(card, text="正在查询音标与释义...", font=self.app_ref.config.font_small, text_color="#2b7a78")
        self.lbl_phonetic.pack(anchor="w", padx=16, pady=(0, 4))

        self.txt_detail = ctk.CTkTextbox(card, font=self.app_ref.config.font_normal, corner_radius=6, height=125, wrap="word")
        self.txt_detail.pack(fill="both", expand=True, padx=16, pady=4)

        bottom_bar = ctk.CTkFrame(card, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=16, pady=(8, 10))

        self.btn_add = ctk.CTkButton(
            bottom_bar,
            text="➕ 加入本地生词库",
            font=self.app_ref.config.font_small,
            width=130,
            height=28,
            fg_color="#2b7a78",
            hover_color="#205e5c",
            command=self.add_to_vocab
        )
        self.btn_add.pack(side="left")

        ctk.CTkButton(
            bottom_bar,
            text="关闭",
            font=self.app_ref.config.font_small,
            width=70,
            height=28,
            fg_color="#555555",
            hover_color="#444444",
            command=self.destroy
        ).pack(side="right")

        threading.Thread(target=self.fetch_trans, daemon=True).start()

    def fetch_trans(self):
        res = FreeDictService.lookup(self.word)
        self.after(0, self.update_ui, res)

    def update_ui(self, res):
        self.lbl_phonetic.configure(text=res.get("phonetic", ""))
        text = f"【核心释义】:\n{res.get('pos_def', '')}\n\n【双语例句】:\n{res.get('example', '')}"
        self.txt_detail.delete("1.0", "end")
        self.txt_detail.insert("1.0", text)

    def add_to_vocab(self):
        self.app_ref.config.add_words_to_history([self.word])
        self.app_ref.update_global_vocab_status()
        self.btn_add.configure(text="✅ 已在词库中", state="disabled", fg_color="#388e3c")


class VocabManagerWindow(ctk.CTkToplevel):
    def __init__(self, master, app_ref):
        super().__init__(master)
        self.app_ref = app_ref
        self.title("📚 本地生词库中心与单词统计")
        self.geometry("780x620")
        self.minsize(650, 480)
        self.attributes("-topmost", True)
        self.after(10, self.lift)

        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        top_card = ctk.CTkFrame(self, corner_radius=8)
        top_card.pack(fill="x", padx=16, pady=(12, 6))

        self.lbl_stats = ctk.CTkLabel(top_card, text="", font=self.app_ref.config.font_body, text_color=("#1f538d", "#64B5F6"))
        self.lbl_stats.pack(side="left", padx=12, pady=8)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_list())
        ctk.CTkLabel(top_card, text="🔍 搜索词汇:", font=self.app_ref.config.font_small).pack(side="left", padx=(15, 4))
        self.entry_search = ctk.CTkEntry(top_card, textvariable=self.search_var, placeholder_text="输入筛选...", width=140, font=self.app_ref.config.font_small)
        self.entry_search.pack(side="left", padx=(0, 10))

        self.txt_vocab_list = ctk.CTkTextbox(self, font=self.app_ref.config.font_body, corner_radius=8, wrap="word")
        self.txt_vocab_list.pack(fill="both", expand=True, padx=16, pady=6)

        bot_bar = ctk.CTkFrame(self, fg_color="transparent")
        bot_bar.pack(fill="x", padx=16, pady=(6, 12))

        ctk.CTkButton(bot_bar, text="📤 导出 TXT", width=90, height=28, font=self.app_ref.config.font_small, fg_color="#3b5998", hover_color="#2d4373", command=self.export_vocab).pack(side="left", padx=(0, 6))
        ctk.CTkButton(bot_bar, text="📂 导入 TXT", width=90, height=28, font=self.app_ref.config.font_small, fg_color="#2b7a78", hover_color="#205e5c", command=self.import_vocab).pack(side="left", padx=6)
        ctk.CTkButton(bot_bar, text="🗑️ 清空词库", width=90, height=28, font=self.app_ref.config.font_small, fg_color="#c62828", hover_color="#8e0000", command=self.clear_vocab).pack(side="left", padx=6)
        ctk.CTkButton(bot_bar, text="关闭", width=70, height=28, font=self.app_ref.config.font_small, fg_color="#555555", hover_color="#444444", command=self.destroy).pack(side="right")

    def refresh_list(self):
        all_words = self.app_ref.config.vocab_history
        keyword = self.search_var.get().strip().lower()
        if keyword:
            filtered = [w for w in all_words if keyword in w.lower()]
        else:
            filtered = all_words

        total_words = len(all_words)
        total_letters = sum(len(w) for w in all_words)
        self.lbl_stats.configure(text=f"📚 已学总词数: {total_words} 个  |  总字符数: {total_letters} 字母")

        self.txt_vocab_list.delete("1.0", "end")
        if not filtered:
            self.txt_vocab_list.insert("1.0", "（词库为空或没有匹配的单词）")
            return

        lines = []
        for i, w in enumerate(filtered, 1):
            lines.append(f"{i:>3}.  {w}")
        self.txt_vocab_list.insert("1.0", "\n".join(lines))

    def export_vocab(self):
        words = self.app_ref.config.vocab_history
        if not words:
            messagebox.showinfo("提示", "词库暂无词汇可导出。")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(", ".join(words))
            messagebox.showinfo("成功", f"已成功导出 {len(words)} 个单词！")

    def import_vocab(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            with open(path, "r", encoding="gbk") as f:
                content = f.read()
        raw_words = re.split(r'[,，\n\r\t\s]+', content)
        words = [re.sub(r'[^a-zA-Z\-]', '', w).lower() for w in raw_words if w.strip()]
        words = list(dict.fromkeys([w for w in words if w]))
        cnt = self.app_ref.config.add_words_to_history(words)
        self.refresh_list()
        self.app_ref.update_global_vocab_status()
        messagebox.showinfo("成功", f"成功导入 {cnt} 个新词汇！")

    def clear_vocab(self):
        if messagebox.askyesno("确认清空", "确定要清空本地所有已学习的生词吗？此操作不可逆！"):
            self.app_ref.config.clear_all_history()
            self.refresh_list()
            self.app_ref.update_global_vocab_status()


class FullscreenReader(ctk.CTkToplevel):
    def __init__(self, master, app_ref, title_text, en_content, zh_content):
        super().__init__(master)
        self.app_ref = app_ref
        self.title(f"专注阅读模式 - {title_text}")
        self.geometry("1100x780")

        self.bind("<Escape>", lambda e: self.destroy())

        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", padx=16, pady=(10, 4))

        ctk.CTkLabel(top_bar, text=f"📖 {title_text}", font=self.app_ref.config.font_normal).pack(side="left", padx=10)
        ctk.CTkButton(top_bar, text="✖ 退出阅读 (Esc)", width=110, height=26, font=self.app_ref.config.font_small, fg_color="#c62828", hover_color="#8e0000", command=self.destroy).pack(side="right", padx=10)

        self.btn_toggle_mode = ctk.CTkSegmentedButton(
            top_bar,
            values=["📖 双语对照", "🔤 纯英文沉浸", "🇨🇳 纯中文对照"],
            font=self.app_ref.config.font_small,
            command=self.change_mode
        )
        self.btn_toggle_mode.set("📖 双语对照")
        self.btn_toggle_mode.pack(side="right", padx=15)

        self.read_container = ctk.CTkFrame(self, corner_radius=8)
        self.read_container.pack(fill="both", expand=True, padx=16, pady=(4, 14))
        self.read_container.grid_columnconfigure(0, weight=1)
        self.read_container.grid_rowconfigure(0, weight=1)
        self.read_container.grid_rowconfigure(1, weight=1)

        self.txt_en = ModernTextBox(self.read_container, self.app_ref, font=self.app_ref.config.font_reader, wrap="word")
        self.txt_en.grid(row=0, column=0, sticky="nsew", padx=12, pady=6)
        self.txt_en.insert("1.0", en_content)

        self.txt_zh = ModernTextBox(self.read_container, self.app_ref, font=self.app_ref.config.font_reader, wrap="word")
        self.txt_zh.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        self.txt_zh.insert("1.0", zh_content)

    def change_mode(self, mode):
        if mode == "📖 双语对照":
            self.txt_en.grid(row=0, column=0, sticky="nsew", padx=12, pady=6)
            self.txt_zh.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
            self.read_container.grid_rowconfigure(0, weight=1)
            self.read_container.grid_rowconfigure(1, weight=1)
        elif mode == "🔤 纯英文沉浸":
            self.txt_zh.grid_forget()
            self.txt_en.grid(row=0, column=0, sticky="nsew", padx=12, pady=6)
            self.read_container.grid_rowconfigure(0, weight=1)
            self.read_container.grid_rowconfigure(1, weight=0)
        elif mode == "🇨🇳 纯中文对照":
            self.txt_en.grid_forget()
            self.txt_zh.grid(row=0, column=0, sticky="nsew", padx=12, pady=6)
            self.read_container.grid_rowconfigure(0, weight=1)
            self.read_container.grid_rowconfigure(1, weight=0)
