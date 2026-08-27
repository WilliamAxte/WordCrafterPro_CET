import os
import shutil

# 清理旧的编译缓存
for root, dirs, files in os.walk("."):
    for d in dirs:
        if d == "__pycache__":
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)

modules = {
"app_config.py": '''import json
import os
import customtkinter as ctk

CONFIG_FILE = "user_config.json"
HISTORY_FILE = "vocab_history.json"
CACHE_FILE = "vocab_cache.json"

class AppConfig:
    def __init__(self):
        self.font_normal = ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="normal")
        self.font_body = ctk.CTkFont(family="Microsoft YaHei UI", size=14, weight="normal")
        self.font_bold = ctk.CTkFont(family="Microsoft YaHei UI", size=15, weight="normal")
        self.font_small = ctk.CTkFont(family="Microsoft YaHei UI", size=11, weight="normal")
        self.font_reader = ctk.CTkFont(family="Microsoft YaHei UI", size=17, weight="normal")

        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = ""
        self.model_name = "deepseek-chat"
        self.difficulty = "初高中/日常通俗 (周围词汇极简)"

        self.vocab_history = self.load_history()
        self.vocab_cache = self.load_cache()
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.api_url = data.get("api_url", self.api_url)
                    self.api_key = data.get("api_key", self.api_key)
                    self.model_name = data.get("model_name", self.model_name)
                    self.difficulty = data.get("difficulty", self.difficulty)
            except Exception:
                pass

    def save_config(self, url, key, model, diff):
        self.api_url = url.strip()
        self.api_key = key.strip()
        self.model_name = model.strip()
        self.difficulty = diff
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "api_url": self.api_url,
                    "api_key": self.api_key,
                    "model_name": self.model_name,
                    "difficulty": self.difficulty
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # 兼容字符串或对象数据结构
                        words = []
                        for item in data:
                            if isinstance(item, str):
                                words.append(item.lower().strip())
                            elif isinstance(item, dict) and "word" in item:
                                words.append(item["word"].lower().strip())
                        return list(dict.fromkeys(words))
            except Exception:
                pass
        return ["serendipity", "persist", "hesitate", "fragile", "resilient"]

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_cache(self):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.vocab_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def save_history_to_file(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.vocab_history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_words_to_history(self, new_words):
        added_count = 0
        for w in new_words:
            w_clean = w.strip().lower()
            if w_clean and w_clean not in self.vocab_history:
                self.vocab_history.append(w_clean)
                added_count += 1
        if added_count > 0:
            self.save_history_to_file()
        return added_count

    def remove_word_from_history(self, word):
        w_clean = word.strip().lower()
        if w_clean in self.vocab_history:
            self.vocab_history.remove(w_clean)
            self.save_history_to_file()

    def clear_all_history(self):
        self.vocab_history.clear()
        self.save_history_to_file()
''',

"services.py": '''import json
import re
import urllib.request
import urllib.parse
import urllib.error
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

class FreeDictService:
    """微软必应词典精准抓取引擎"""
    @classmethod
    def lookup(cls, word):
        word_clean = word.strip().lower()
        if not word_clean:
            return {"word": word, "phonetic": "", "pos_def": "未输入单词", "example": ""}

        try:
            url = f"https://cn.bing.com/dict/search?q={urllib.parse.quote(word_clean)}"
            req = urllib.request.Request(
                url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            phonetic = ""
            us_match = re.search(r'class="hd_prUS"[^>]*>\\\\[(.*?)\\\\]', html)
            if us_match:
                phonetic = f"美 [{us_match.group(1)}]"
            else:
                pr_match = re.search(r'class="hd_pr"[^>]*>\\\\[(.*?)\\\\]', html)
                if pr_match:
                    phonetic = f"[{pr_match.group(1)}]"

            # 抓取词性及中文翻译
            defs = []
            pos_matches = re.findall(r'<span class="pos[^"]*">([^<]+)</span><span class="def[^"]*"><span>([^<]+)</span></span>', html)
            for pos, definition in pos_matches[:4]:
                defs.append(f"{pos} {definition.strip()}")
            
            # 若常规类名未匹配到，匹配速查释义
            if not defs:
                quick_match = re.findall(r'<li><span class="pos">([^<]+)</span><span class="def">([^<]+)</span></li>', html)
                for pos, definition in quick_match[:4]:
                    defs.append(f"{pos} {definition.strip()}")

            pos_def_str = "\\n".join(defs) if defs else ""

            # 抓取双语例句
            example_str = ""
            en_sen = re.search(r'<div class="sen_en">([^<]+)</div>', html)
            cn_sen = re.search(r'<div class="sen_cn">([^<]+)</div>', html)
            if en_sen and cn_sen:
                example_str = f"{en_sen.group(1).strip()}\\n{cn_sen.group(1).strip()}"

            if pos_def_str:
                return {
                    "word": word_clean,
                    "phonetic": phonetic or "[微软必应词典]",
                    "pos_def": pos_def_str,
                    "example": example_str or "（暂无精选双语例句）"
                }
        except Exception:
            pass

        # 降级备选
        return {
            "word": word_clean,
            "phonetic": "[标准发音]",
            "pos_def": f"已收录生词: {word_clean}",
            "example": f"This is an illustrative example sentence containing '{word_clean}'."
        }


class AIService:
    @staticmethod
    def request_llm(prompt, api_key, api_url, model_name, temp=0.6):
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a professional English tutor, literary scholar, and ACG editorial writer. Follow all output structure and word count requirements strictly."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temp
        }
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=80) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    @classmethod
    def generate_vocab_story(cls, words, extra_count, length_target, difficulty, api_key, api_url, model_name):
        if not api_key:
            words_fmt = ", ".join([f"【{w}】" for w in words])
            en = f"Tom was an ordinary student. Whenever he faced a challenge, he would often {' and '.join(words_fmt)} with patience.\\n\\nHe realized that language learning is about steady steps and genuine curiosity."
            zh = f"Tom 是一个普通学生。每当面对挑战时，他总会以充满耐心的方式经历 {', '.join(words)}。\\n\\n他意识到语言学习在于沉稳的步伐与真正的好奇心。"
            return en, zh

        extra_instruction = ""
        if extra_count > 0:
            extra_instruction = f"4. 随机未学生词拓展：请在故事中额外自然融入 {extra_count} 个地道中高级新单词（使用 〖*word*〗 格式醒目标出）。"

        prompt = f"""
请根据【目标生词列表】编写一段通俗生动的短文与中文翻译。

【核心目标生词】：{", ".join(words)} (共 {len(words)} 个)
【目标生成字数】：严格生成大约 {length_target} 个英文单词（请充分展开情节与描写，确保篇幅达标！）
【难度标准】：{difficulty}

【严格原则与排版】：
1. 词汇门槛严格控制：除【核心目标生词】外，全文其他所有词汇必须使用初高中/日常高频简单词，严禁生僻词与晦涩长难句。
2. 英文短文中每次出现核心目标生词，必须用 【word】 醒目标出。
3. 篇幅严控：请按照 {length_target} 字的要求充分展开叙事，不得敷衍简短！
{extra_instruction}
5. 严格使用指定标记输出，严禁输出任何 Markdown 标题符号（如 ###）：

<<<ENGLISH_STORY>>>
(这里输出纯英文故事)
<<<CHINESE_TRANSLATION>>>
(这里输出流畅双语中文翻译，核心生词用【中文】标出，拓展词用〖中文〗标出)
"""
        res = cls.request_llm(prompt, api_key, api_url, model_name)
        return cls._split_content(res)

    @classmethod
    def generate_acg_story(cls, words, extra_count, length_target, category, topic, difficulty, api_key, api_url, model_name):
        if not api_key:
            en = f"Title: The World of {topic}\\n\\nIn modern animation, creators know how to 【{words[0]}】 in moments of intense drama. Works like {topic} highlight deep emotion and artful music."
            zh = f"标题：《{topic}》的艺术世界\\n\\n在现代动漫中，创作者懂得如何在剧烈冲突中展现【{words[0]}】。如《{topic}》这般作品凸显了深层情感与配乐魅力。"
            return en, zh

        extra_instruction = ""
        if extra_count > 0:
            extra_instruction = f"4. 随机未学词拓展：在特稿中额外融入 {extra_count} 个影视与视听鉴赏相关的地道新词（用 〖*word*〗 标出）。"

        prompt = f"""
请以二次元专栏特稿/漫评随笔风格，围绕主题撰写一篇充满 ACG 氛围的英文深度特稿并提供双语翻译。

【专栏类型】：{category}
【作品/焦点主题】：{topic}
【融入核心生词】：{", ".join(words)} (共 {len(words)} 个)
【目标生成字数】：严格生成大约 {length_target} 个英文单词（论述深刻、细节充分，确保字数达标！）
【难度标准】：{difficulty}

【严格原则与排版】：
1. 文风地道生动，结合作品设定、视听艺术或受众心境深度展开。
2. 核心生词使用 【WORD】 醒目标注。
3. 篇幅严控：必须达到大约 {length_target} 字的深度专栏体量。
{extra_instruction}
5. 严格使用指定标记输出，严禁输出任何 Markdown 标题符号（如 ###）：

<<<ENGLISH_STORY>>>
(这里输出英文专栏特稿)
<<<CHINESE_TRANSLATION>>>
(这里输出中文对照翻译，目标词对应使用【中文】标出)
"""
        res = cls.request_llm(prompt, api_key, api_url, model_name)
        return cls._split_content(res)

    @classmethod
    def fetch_authentic_reading(cls, source_type, custom_work, length_target, difficulty, api_key, api_url, model_name):
        if not api_key:
            en = (
                "Title: Stay Hungry, Stay Foolish (Steve Jobs)\\n\\n"
                "Your time is limited, so don't waste it living someone else's life. "
                "Don't be trapped by dogma — which is living with the results of other people's thinking. "
                "Don't let the noise of others' opinions drown out your own inner voice. "
                "And most importantly, have the courage to follow your heart and intuition."
            )
            zh = (
                "标题：求知若饥，虚心若愚（史蒂夫·乔布斯）\\n\\n"
                "你们的时间很有限，所以不要浪费时间去过别人的生活。"
                "不要被教条所束缚——那是在按别人的思考结果活着。"
                "不要让别人的意见噪音淹没你自己内心的声音。"
                "最重要的是，要有勇气去跟随你的内心和直觉。"
            )
            return en, zh

        prompt = f"""
你是一位世界文学与英语经典名篇研究专家。请从【{source_type}】中挑选或节选一段经典段落（若指定了作品：{custom_work}，则优先围绕该作品），并提供精准流畅的双语对照。

【选篇来源类型】：{source_type}
【指定作品/演讲者】：{custom_work or '挑选该领域最具代表性的经典名篇'}
【目标字数】：生成约 {length_target} 词的经典原著/演讲节选精读
【语言难度】：{difficulty}

【严格要求】：
1. 保持原文地道原汁原味的文采与语言节奏。
2. 提炼出文中最具启发性的经典修辞与句式。
3. 严格使用指定标记输出，严禁输出任何多余的 Markdown 标题（如 ###）：

<<<ENGLISH_STORY>>>
(这里输出经典篇章英文正文，首行附带篇名与作者)
<<<CHINESE_TRANSLATION>>>
(这里输出全文流畅优美的中文对照翻译)
"""
        res = cls.request_llm(prompt, api_key, api_url, model_name)
        return cls._split_content(res)

    @staticmethod
    def _split_content(raw):
        if "<<<ENGLISH_STORY>>>" in raw and "<<<CHINESE_TRANSLATION>>>" in raw:
            parts = raw.split("<<<CHINESE_TRANSLATION>>>")
            en = parts[0].replace("<<<ENGLISH_STORY>>>", "").strip()
            zh = parts[1].strip()
        else:
            en, zh = raw.strip(), "（未能自动切分翻译部分，请直接阅读原文）"
        en = re.sub(r'^```[a-zA-Z]*\\n', '', en)
        en = re.sub(r'\\n```$', '', en).strip()
        zh = re.sub(r'^```[a-zA-Z]*\\n', '', zh)
        zh = re.sub(r'\\n```$', '', zh).strip()
        return en, zh
''',

"ui_components.py": '''import tkinter as tk
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
            clean_word = re.sub(r'[^a-zA-Z\\-]', '', sel_text).lower()
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
        self.app_ref.config.vocab_cache[self.word] = res
        self.app_ref.config.save_cache()
        self.after(0, self.update_ui, res)

    def update_ui(self, res):
        self.lbl_phonetic.configure(text=res.get("phonetic", ""))
        text = f"【核心释义】:\\n{res.get('pos_def', '')}\\n\\n【双语例句】:\\n{res.get('example', '')}"
        self.txt_detail.delete("1.0", "end")
        self.txt_detail.insert("1.0", text)

    def add_to_vocab(self):
        self.app_ref.config.add_words_to_history([self.word])
        self.app_ref.update_global_vocab_status()
        self.btn_add.configure(text="✅ 已在词库中", state="disabled", fg_color="#388e3c")


class ModernWordCard(ctk.CTkFrame):
    """具有悬浮高亮动效与音标中文对照的独立单词卡片组件"""
    def __init__(self, master, app_ref, word, index, on_delete_callback):
        self.default_bg = ("#f4f5f7", "#232428")
        self.hover_bg = ("#e8ebf0", "#2d3036")
        
        super().__init__(master, corner_radius=10, fg_color=self.default_bg, border_width=1, border_color=("gray80", "#363840"))
        self.app_ref = app_ref
        self.word = word
        self.index = index
        self.on_delete_callback = on_delete_callback

        self.setup_card_ui()
        self.bind_hover_effects(self)
        self.load_definition_async()

    def setup_card_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # 序号徽章
        self.lbl_idx = ctk.CTkLabel(self, text=f"#{self.index:02d}", font=self.app_ref.config.font_small, text_color="#888888", width=35)
        self.lbl_idx.grid(row=0, column=0, rowspan=2, padx=(10, 5), pady=8, sticky="n")

        # 单词标题与音标栏
        top_info_row = ctk.CTkFrame(self, fg_color="transparent")
        top_info_row.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(8, 2))

        self.lbl_word = ctk.CTkLabel(top_info_row, text=self.word, font=self.app_ref.config.font_bold, text_color=("#1f538d", "#64B5F6"))
        self.lbl_word.pack(side="left", padx=(0, 10))

        self.lbl_phonetic = ctk.CTkLabel(top_info_row, text="加载中...", font=self.app_ref.config.font_small, text_color="#2b7a78")
        self.lbl_phonetic.pack(side="left")

        # 删除按钮
        self.btn_del = ctk.CTkButton(
            top_info_row,
            text="✕",
            width=24,
            height=24,
            font=self.app_ref.config.font_small,
            fg_color="transparent",
            hover_color=("#ffcdd2", "#b71c1c"),
            text_color=("gray40", "gray70"),
            command=lambda: self.on_delete_callback(self.word)
        )
        self.btn_del.pack(side="right")

        # 中文释义与例句栏
        self.lbl_meaning = ctk.CTkLabel(
            self,
            text="正在从微软必应解析释义...",
            font=self.app_ref.config.font_normal,
            text_color=("gray20", "gray85"),
            justify="left",
            wraplength=700
        )
        self.lbl_meaning.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=(0, 8))

    def bind_hover_effects(self, widget):
        widget.bind("<Enter>", self.on_hover_enter)
        widget.bind("<Leave>", self.on_hover_leave)
        for child in widget.winfo_children():
            if not isinstance(child, ctk.CTkButton):
                self.bind_hover_effects(child)

    def on_hover_enter(self, event=None):
        self.configure(fg_color=self.hover_bg, border_color=("#3b82f6", "#60a5fa"))

    def on_hover_leave(self, event=None):
        self.configure(fg_color=self.default_bg, border_color=("gray80", "#363840"))

    def load_definition_async(self):
        # 优先读缓存
        cache = self.app_ref.config.vocab_cache.get(self.word)
        if cache and cache.get("pos_def"):
            self.update_card_data(cache)
            return

        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        res = FreeDictService.lookup(self.word)
        self.app_ref.config.vocab_cache[self.word] = res
        self.app_ref.config.save_cache()
        self.after(0, self.update_card_data, res)

    def update_card_data(self, res):
        self.lbl_phonetic.configure(text=res.get("phonetic", ""))
        meaning_text = res.get("pos_def", "暂无中文释义").replace("\\n", "  |  ")
        self.lbl_meaning.configure(text=meaning_text)


class VocabManagerWindow(ctk.CTkToplevel):
    """支持卡片瀑布流布局、级联动画与必应中英对照的生词库中心"""
    def __init__(self, master, app_ref):
        super().__init__(master)
        self.app_ref = app_ref
        self.title("📚 本地生词库中心 (卡片视图 & 微软必应对照)")
        self.geometry("860x660")
        self.minsize(720, 520)
        self.attributes("-topmost", True)
        self.after(10, self.lift)

        self.cards_list = []
        self.setup_ui()
        self.refresh_cards_animated()

    def setup_ui(self):
        # 顶部统计与搜索栏
        top_card = ctk.CTkFrame(self, corner_radius=10)
        top_card.pack(fill="x", padx=16, pady=(12, 6))

        self.lbl_stats = ctk.CTkLabel(top_card, text="", font=self.app_ref.config.font_bold, text_color=("#1f538d", "#64B5F6"))
        self.lbl_stats.pack(side="left", padx=14, pady=10)

        # 实时搜索框
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_cards())
        ctk.CTkLabel(top_card, text="🔍 筛选:", font=self.app_ref.config.font_small).pack(side="left", padx=(15, 4))
        self.entry_search = ctk.CTkEntry(top_card, textvariable=self.search_var, placeholder_text="搜索词汇...", width=140, font=self.app_ref.config.font_small)
        self.entry_search.pack(side="left", padx=(0, 10))

        # 中部卡片滚动容器
        self.scroll_container = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray95", "#1a1b1e"))
        self.scroll_container.pack(fill="both", expand=True, padx=16, pady=6)
        self.scroll_container.grid_columnconfigure(0, weight=1)

        # 底部操作栏
        bot_bar = ctk.CTkFrame(self, fg_color="transparent")
        bot_bar.pack(fill="x", padx=16, pady=(6, 12))

        ctk.CTkButton(bot_bar, text="📤 导出生词 TXT", width=110, height=28, font=self.app_ref.config.font_small, fg_color="#3b5998", hover_color="#2d4373", command=self.export_vocab).pack(side="left", padx=(0, 6))
        ctk.CTkButton(bot_bar, text="📂 导入单词 TXT", width=110, height=28, font=self.app_ref.config.font_small, fg_color="#2b7a78", hover_color="#205e5c", command=self.import_vocab).pack(side="left", padx=6)
        ctk.CTkButton(bot_bar, text="🗑️ 清空所有生词", width=110, height=28, font=self.app_ref.config.font_small, fg_color="#c62828", hover_color="#8e0000", command=self.clear_vocab).pack(side="left", padx=6)
        ctk.CTkButton(bot_bar, text="关闭窗口", width=80, height=28, font=self.app_ref.config.font_small, fg_color="#555555", hover_color="#444444", command=self.destroy).pack(side="right")

    def refresh_cards_animated(self):
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
        self.cards_list.clear()

        all_words = self.app_ref.config.vocab_history
        total_words = len(all_words)
        total_letters = sum(len(w) for w in all_words)
        self.lbl_stats.configure(text=f"📚 词库总计: {total_words} 个单词  |  总字符数: {total_letters} 字母")

        if not all_words:
            lbl_empty = ctk.CTkLabel(self.scroll_container, text="📭 暂无生词记录，快去添加新单词吧！", font=self.app_ref.config.font_normal, text_color="#888888")
            lbl_empty.pack(pady=40)
            return

        # 阶梯式平滑级联入场动画 (Staggered Animation)
        for i, word in enumerate(all_words):
            card = ModernWordCard(self.scroll_container, self.app_ref, word, i + 1, self.delete_single_word)
            self.cards_list.append((word, card))
            self.after(i * 25, self._animate_pack_card, card)

    def _animate_pack_card(self, card):
        if card.winfo_exists():
            card.pack(fill="x", padx=6, pady=4)

    def filter_cards(self):
        kw = self.search_var.get().strip().lower()
        for word, card in self.cards_list:
            if not kw or kw in word.lower():
                card.pack(fill="x", padx=6, pady=4)
            else:
                card.pack_forget()

    def delete_single_word(self, word):
        self.app_ref.config.remove_word_from_history(word)
        self.app_ref.update_global_vocab_status()
        self.refresh_cards_animated()

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
        raw_words = re.split(r'[,，\\n\\r\\t\\s]+', content)
        words = [re.sub(r'[^a-zA-Z\\-]', '', w).lower() for w in raw_words if w.strip()]
        words = list(dict.fromkeys([w for w in words if w]))
        cnt = self.app_ref.config.add_words_to_history(words)
        self.refresh_cards_animated()
        self.app_ref.update_global_vocab_status()
        messagebox.showinfo("成功", f"成功导入 {cnt} 个新词汇并生成卡片！")

    def clear_vocab(self):
        if messagebox.askyesno("确认清空", "确定要清空本地所有已学习的生词吗？此操作不可逆！"):
            self.app_ref.config.clear_all_history()
            self.refresh_cards_animated()
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
''',

"tab_vocab.py": '''import customtkinter as ctk
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
        cleaned = re.split(r'[,，\\n\\r\\t\\s]+', text)
        words = [re.sub(r'[^a-zA-Z\\-]', '', w).lower() for w in cleaned if w.strip()]
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

        words = [re.sub(r'[^a-zA-Z\\-]', '', w).lower() for w in re.split(r'[,，\\n\\r\\t\\s]+', content) if w.strip()]
        words = list(dict.fromkeys([w for w in words if w]))
        self.word_input.delete("1.0", "end")
        self.word_input.insert("1.0", ", ".join(words))

    def export_article(self):
        en = self.txt_en.get("1.0", "end").strip()
        zh = self.txt_zh.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"=== English Context Story ===\\n\\n{en}\\n\\n=== Chinese Translation ===\\n\\n{zh}\\n")
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
''',

"tab_acg.py": '''import customtkinter as ctk
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
                f.write(f"=== ACG English Review ===\\n\\n{en}\\n\\n=== Chinese Translation ===\\n\\n{zh}\\n")
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
''',

"tab_reading.py": '''import customtkinter as ctk
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
                f.write(f"=== Authentic English Reading ===\\n\\n{en}\\n\\n=== Chinese Translation ===\\n\\n{zh}\\n")
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
''',

"main.py": '''import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import customtkinter as ctk
from app_config import AppConfig
from tab_vocab import VocabStoryTab
from tab_acg import AcgStoryTab
from tab_reading import AuthenticReadingTab
from ui_components import VocabManagerWindow

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = AppConfig()

        self.title("WordCrafter Pro - 英语情境短文、ACG 特稿与原著精读工坊")
        self.geometry("1200x940")
        self.minsize(1020, 760)

        self.var_api_url = ctk.StringVar(value=self.config.api_url)
        self.var_api_key = ctk.StringVar(value=self.config.api_key)
        self.var_model_name = ctk.StringVar(value=self.config.model_name)
        self.var_difficulty = ctk.StringVar(value=self.config.difficulty)

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 顶部全局配置栏
        config_card = ctk.CTkFrame(self, corner_radius=10)
        config_card.grid(row=0, column=0, padx=16, pady=(10, 4), sticky="ew")

        top_r0 = ctk.CTkFrame(config_card, fg_color="transparent")
        top_r0.pack(fill="x", padx=14, pady=(6, 2))

        ctk.CTkLabel(top_r0, text="⚙️ 全局模型与接口配置 (自动保存配置)", font=self.config.font_normal).pack(side="left")

        # 点击即可打开卡片式生词库中心
        self.btn_vocab_mgr = ctk.CTkButton(
            top_r0,
            text=f"📚 打开本地生词库 (已学 {len(self.config.vocab_history)} 词)",
            font=self.config.font_small,
            width=190,
            height=26,
            fg_color="#2b7a78",
            hover_color="#205e5c",
            command=self.open_vocab_manager
        )
        self.btn_vocab_mgr.pack(side="right")

        cfg_row = ctk.CTkFrame(config_card, fg_color="transparent")
        cfg_row.pack(fill="x", padx=14, pady=(2, 8))

        ctk.CTkLabel(cfg_row, text="API Key:", font=self.config.font_normal).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(cfg_row, textvariable=self.var_api_key, show="*", placeholder_text="填入 API Key", width=180, font=self.config.font_normal).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(cfg_row, text="API URL:", font=self.config.font_normal).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(cfg_row, textvariable=self.var_api_url, width=210, font=self.config.font_normal).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(cfg_row, text="模型:", font=self.config.font_normal).pack(side="left", padx=(0, 4))
        ctk.CTkComboBox(
            cfg_row,
            values=[
                "deepseek-chat",
                "deepseek-reasoner",
                "gpt-4o",
                "gpt-4o-mini",
                "o3-mini",
                "claude-3-7-sonnet",
                "claude-3-5-sonnet",
                "qwen-max",
                "qwen-plus"
            ],
            variable=self.var_model_name,
            width=175,
            font=self.config.font_normal,
            dropdown_font=self.config.font_normal
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(cfg_row, text="难度:", font=self.config.font_normal).pack(side="left", padx=(0, 4))
        ctk.CTkOptionMenu(
            cfg_row, 
            values=["初高中/日常通俗 (周围词汇极简)", "大学四级 (通顺自然)", "考研/六级/雅思 (地道语境)"],
            variable=self.var_difficulty,
            width=200,
            font=self.config.font_normal,
            dropdown_font=self.config.font_normal,
            command=self.on_config_change
        ).pack(side="left")

        self.var_api_key.trace_add("write", lambda *args: self.on_config_change())
        self.var_api_url.trace_add("write", lambda *args: self.on_config_change())
        self.var_model_name.trace_add("write", lambda *args: self.on_config_change())

        # 主多标签页
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=16, pady=(4, 10), sticky="nsew")

        tab1 = self.tabview.add("📝 单词情境短文 (自定义长篇)")
        tab2 = self.tabview.add("🌸 二次元专区 (ACG 深度特稿)")
        tab3 = self.tabview.add("📖 名篇名作与经典演讲精读")

        self.page_vocab = VocabStoryTab(tab1, self)
        self.page_vocab.pack(fill="both", expand=True)

        self.page_acg = AcgStoryTab(tab2, self)
        self.page_acg.pack(fill="both", expand=True)

        self.page_reading = AuthenticReadingTab(tab3, self)
        self.page_reading.pack(fill="both", expand=True)

    def on_config_change(self, *args):
        self.config.save_config(
            self.var_api_url.get(),
            self.var_api_key.get(),
            self.var_model_name.get(),
            self.var_difficulty.get()
        )

    def open_vocab_manager(self):
        VocabManagerWindow(self, self)

    def update_global_vocab_status(self):
        cnt = len(self.config.vocab_history)
        self.btn_vocab_mgr.configure(text=f"📚 打开本地生词库 (已学 {cnt} 词)")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
'''
}

for name, code in modules.items():
    with open(name, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"✅ 已写入模块: {name}")

print("\n🚀 所有模块及动效生词库已全部配置完成！")
