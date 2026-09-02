# ==============================================================================
# 文件路径: wordcrafter/core/dictionary_store.py
# 包含组件: DictionaryStore, normalize_entry, 词典文件导入/查询/统计
#
# 词典仓储 = 本地词典数据的统一入口，包含两部分：
#   1. batch —— 从在线公益词典源批量导入的生词库词条缓存（word -> 词条）
#   2. files —— 用户导入的离线词典 JSON 文件注册表（WordNet / kaikki.org 等公开数据）
# 词条统一 schema: {"word", "phonetic", "pos_def", "example", "source"}
# ==============================================================================
import json
import os
import re
import time

from .repository import DATA_DIR, data_path, _load_json, _save_json

STORE_FILE = "dictionary_store.json"
DICT_FOLDER = "dictionaries"
MAX_IMPORT_BYTES = 200 * 1024 * 1024  # 200MB 上限，防止误导入超大文件拖垮内存

_PHONETIC_KEYS = ("phonetic", "phonetics", "pronunciation", "ipa")
_POS_KEYS = ("pos_def", "definition", "meaning", "gloss", "definitions", "shortdef", "short_def")
_EXAMPLE_KEYS = ("example", "examples")
_WORD_KEYS = ("word", "term", "headword", "lemma")
_TEXT_KEYS = ("text", "definition", "example", "ipa", "pronunciation", "gloss", "displayTarget", "target")


def _pick_text(value):
    """从字符串/列表/字典中取第一段可用文本。"""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        for v in value:
            t = _pick_text(v)
            if t:
                return t
        return ""
    if isinstance(value, dict):
        for k in _TEXT_KEYS:
            v = value.get(k)
            if v:
                t = _pick_text(v)
                if t:
                    return t
        return ""
    return ""


def _collect_defs(value, limit=3):
    """收集释义文本（支持字符串、列表、嵌套对象），最多 limit 条。"""
    defs = []
    if isinstance(value, str):
        defs = [d.strip() for d in value.split("\n") if d.strip()]
    elif isinstance(value, (list, tuple)):
        for v in value:
            t = _pick_text(v)
            if t:
                defs.append(t)
            if len(defs) >= limit:
                break
    elif value:
        t = _pick_text(value)
        if t:
            defs.append(t)
    return defs[:limit]


def normalize_entry(word, raw, source=None):
    """把任意来源/格式的原始词条统一为 {word, phonetic, pos_def, example, source}。"""
    if not isinstance(raw, dict):
        raw = {"pos_def": str(raw) if raw else ""}

    phonetic = _pick_text(raw.get("phonetic")
                          or raw.get("phonetics")
                          or raw.get("pronunciation")
                          or raw.get("ipa")
                          or "")
    example = _pick_text(raw.get("example") or raw.get("examples") or "")

    pos_value = None
    for k in _POS_KEYS:
        if raw.get(k):
            pos_value = raw[k]
            break
    defs = _collect_defs(pos_value) if pos_value is not None else []
    if not defs:
        # 没有明确释义字段时，尝试 "translation"/"meaning_zh" 等中文注释
        for k in ("translation", "zh", "cn", "meaning_zh"):
            t = _pick_text(raw.get(k))
            if t:
                defs.append(t)
                break

    entry = {
        "word": str(word).strip().lower(),
        "phonetic": phonetic,
        "pos_def": "\n".join(defs),
        "example": example,
    }
    if source:
        entry["source"] = source
    return entry


def _extract_entries(obj):
    """把导入文件的 JSON 解析为 {word_lower: entry}。支持 词条映射 / 词条列表 两种格式。"""
    if isinstance(obj, dict):
        # 兼容 {"entries": {...}} / {"words": [...]} 包装结构
        if isinstance(obj.get("entries"), dict):
            obj = obj["entries"]
        elif isinstance(obj.get("words"), list):
            obj = obj["words"]
        elif isinstance(obj.get("data"), dict):
            obj = obj["data"]

    word_map = {}
    if isinstance(obj, dict):
        for w, v in obj.items():
            if not isinstance(v, dict):
                continue
            entry = normalize_entry(w, v)
            if entry["pos_def"] or entry["example"] or entry["phonetic"]:
                word_map[entry["word"]] = entry
    elif isinstance(obj, list):
        for item in obj:
            if not isinstance(item, dict):
                continue
            w = None
            for k in _WORD_KEYS:
                if item.get(k):
                    w = str(item[k])
                    break
            if not w:
                continue
            entry = normalize_entry(w, item)
            if entry["pos_def"] or entry["example"] or entry["phonetic"]:
                word_map.setdefault(entry["word"], entry)
    return word_map


class DictionaryStore:
    """本地词典数据仓储：批量导入词条 + 离线词典文件注册。"""

    def __init__(self):
        self.path = data_path(STORE_FILE)
        self._data = self._load()
        self._file_cache = {}

    # ---------- 基础 ----------
    def _load(self):
        data = _load_json(self.path, {}) or {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("batch", {})
        data.setdefault("files", [])
        return data

    def save(self):
        _save_json(self.path, self._data)

    def dict_folder(self):
        folder = os.path.join(DATA_DIR, DICT_FOLDER)
        os.makedirs(folder, exist_ok=True)
        return folder

    # ---------- 批量词条 ----------
    def batch_entries(self):
        return self._data["batch"]

    def batch_count(self):
        return len(self._data["batch"])

    def set_batch_entries(self, word_map):
        self._data["batch"] = dict(word_map)
        self.save()

    def clear_batch(self):
        self._data["batch"] = {}
        self.save()

    # ---------- 离线词典文件 ----------
    def list_files(self):
        return list(self._data["files"])

    def file_count(self):
        return len(self._data["files"])

    def import_file(self, src_path, label=None):
        """导入并规范化一个词典 JSON 文件（复制到数据目录并注册）。返回注册记录。"""
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"文件不存在：{src_path}")
        size = os.path.getsize(src_path)
        if size > MAX_IMPORT_BYTES:
            raise ValueError(f"词典文件过大（{size // 1024 // 1024} MB），暂不支持超过 "
                             f"{MAX_IMPORT_BYTES // 1024 // 1024} MB 的文件。")

        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
            try:
                obj = json.load(f)
            except Exception:
                raise ValueError("无法解析 JSON：文件不是有效的 JSON 词典。")

        word_map = _extract_entries(obj)
        # 也允许把 KyleBing 的顺序 JSON 当作“我的词典”导入。
        if not word_map:
            word_map = {}
            for item in self._extract_any_words(obj):
                w, entry = self._wordbook_entry(item)
                if w and entry:
                    word_map[w] = entry
        if not word_map:
            raise ValueError("未解析到任何词条。请使用词条映射或词条列表格式，参见窗口内格式说明。")

        folder = self.dict_folder()
        base = os.path.basename(src_path)
        dest = os.path.join(folder, base)
        if os.path.abspath(src_path) != os.path.abspath(dest) and os.path.exists(dest):
            stem, ext = os.path.splitext(base)
            dest = os.path.join(folder, f"{stem}_{int(time.time())}{ext}")

        # 规范化后紧凑写入，保证后续查询无需再解析原始结构
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(word_map, f, ensure_ascii=False)

        record = {
            "filename": os.path.relpath(dest, DATA_DIR),
            "label": (label or os.path.splitext(base)[0]),
            "count": len(word_map),
            "kind": "local",
            "imported_at": time.time(),
        }
        self._data["files"].append(record)
        self._file_cache[record["filename"]] = word_map
        self.save()
        return record

    def import_text_file(self, src_path, label=None, kind="local", source=None):
        """导入“单词<TAB>释义”格式的本地词典/词表。"""
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"文件不存在：{src_path}")
        content = ""
        for enc in ("utf-8", "gbk", "ansi"):
            try:
                with open(src_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except Exception:
                continue
        if not content:
            raise ValueError("无法读取本地词典文件。")

        word_map = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = re.split(r"\t+", line, maxsplit=1)
            if len(parts) < 2:
                parts = re.split(r"\s{2,}", line, maxsplit=1)
            word = re.match(r"[A-Za-z][A-Za-z-]*", parts[0].strip())
            if not word:
                continue
            meaning = parts[1].strip() if len(parts) > 1 else ""
            word_map[word.group(0).lower()] = {
                "word": word.group(0).lower(), "pos_def": meaning
            }
        if not word_map:
            raise ValueError("未解析到词条。请使用“单词<TAB>释义”格式。")

        folder = self.dict_folder()
        base = os.path.basename(src_path)
        dest = os.path.join(folder, base)
        if os.path.abspath(src_path) != os.path.abspath(dest) and os.path.exists(dest):
            stem, ext = os.path.splitext(base)
            dest = os.path.join(folder, f"{stem}_{int(time.time())}{ext}")
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(word_map, f, ensure_ascii=False)
        record = {
            "filename": os.path.relpath(dest, DATA_DIR),
            "label": label or os.path.splitext(base)[0],
            "count": len(word_map),
            "kind": kind,
            "imported_at": time.time(),
        }
        if source:
            record["source"] = source
        self._data["files"].append(record)
        self._file_cache[record["filename"]] = word_map
        self.save()
        return record

    def import_jsonl_file(self, src_path, label=None, kind="local", source=None):
        """导入一词一行 JSONL 词典（KyleBing full_line_jsonl 格式）。"""
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"文件不存在：{src_path}")
        word_map = {}
        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                w, entry = self._wordbook_entry(item)
                if w and entry:
                    word_map[w] = entry
        if not word_map:
            raise ValueError("未解析到 JSONL 词条。")
        return self._save_imported_map(word_map, src_path, label, kind, source)

    def import_tsv_file(self, src_path, label=None, kind="local", source=None):
        """导入 full_line_tsv：支持 simple、sentence、full 三种列数。"""
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"文件不存在：{src_path}")
        content = ""
        for enc in ("utf-8", "gbk", "ansi"):
            try:
                with open(src_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except Exception:
                continue
        if not content:
            raise ValueError("无法读取 TSV 词典文件。")

        def unescape(value):
            return (value.replace("\\\\", "\0").replace("\\n", "\n")
                    .replace("\\t", "\t").replace("\0", "\\"))

        def cells(value):
            return [unescape(x) for x in value.split("¦") if x]

        def parts(value):
            return value.split("::")

        word_map = {}
        for line in content.splitlines():
            cols = line.rstrip("\r").split("\t")
            if not cols:
                continue
            word_match = re.match(r"[A-Za-z][A-Za-z-]*", cols[0].strip())
            if not word_match:
                continue
            word = word_match.group(0).lower()
            if len(cols) >= 6:  # sentence/full：word, us, uk, translations, phrases, sentences
                phonetic = " / ".join(x for x in (cols[1], cols[2]) if x)
                translations, phrases, sentences = cols[3], cols[4], cols[5]
            else:  # simple：word, translations, phrases
                phonetic, translations = "", cols[1] if len(cols) > 1 else ""
                phrases = cols[2] if len(cols) > 2 else ""
                sentences = ""
            defs = []
            for raw in cells(translations):
                seg = parts(raw)
                if len(seg) >= 2 and seg[1]:
                    defs.append(f"{seg[0]}. {seg[1]}" if seg[0] else seg[1])
            examples = []
            for raw in cells(phrases):
                seg = parts(raw)
                if seg and seg[0]:
                    examples.append(f"{seg[0]} — {seg[1]}" if len(seg) > 1 and seg[1] else seg[0])
            for raw in cells(sentences):
                seg = parts(raw)
                if seg and seg[0]:
                    examples.append(f"{seg[0]} — {seg[1]}" if len(seg) > 1 and seg[1] else seg[0])
            entry = {"word": word}
            if phonetic:
                entry["phonetic"] = phonetic
            if defs:
                entry["pos_def"] = "\n".join(defs[:4])
            if examples:
                entry["example"] = "\n".join(examples[:4])
            word_map[word] = entry
        if not word_map:
            raise ValueError("未解析到 TSV 词条。")
        return self._save_imported_map(word_map, src_path, label, kind, source)

    def _save_imported_map(self, word_map, src_path, label, kind="local", source=None):
        """保存已解析词典的通用注册逻辑。"""
        folder = self.dict_folder()
        base = os.path.basename(src_path)
        dest = os.path.join(folder, base)
        if os.path.abspath(src_path) != os.path.abspath(dest) and os.path.exists(dest):
            stem, ext = os.path.splitext(base)
            dest = os.path.join(folder, f"{stem}_{int(time.time())}{ext}")
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(word_map, f, ensure_ascii=False)
        record = {
            "filename": os.path.relpath(dest, DATA_DIR),
            "label": label or os.path.splitext(base)[0],
            "count": len(word_map),
            "kind": kind,
            "imported_at": time.time(),
        }
        if source:
            record["source"] = source
        self._data["files"].append(record)
        self._file_cache[record["filename"]] = word_map
        self.save()
        return record

    def remove_file(self, filename):
        """从注册表移除并删除已复制的词典文件。"""
        for i, reg in enumerate(self._data["files"]):
            if reg["filename"] == filename:
                del self._data["files"][i]
                self._file_cache.pop(filename, None)
                try:
                    full = os.path.join(DATA_DIR, filename)
                    if os.path.exists(full):
                        os.remove(full)
                except Exception:
                    pass
                self.save()
                return True
        return False

    def _load_file_entries(self, record):
        filename = record["filename"]
        if filename in self._file_cache:
            return self._file_cache[filename]
        full = os.path.join(DATA_DIR, filename)
        entries = {}
        try:
            with open(full, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if isinstance(obj, dict):
                entries = obj
        except Exception:
            entries = {}
        self._file_cache[filename] = entries
        return entries

    # ---------- 词书导入（单词列表，可含无释义的词） ----------
    @staticmethod
    def _extract_any_words(obj):
        """从多种词书结构提取词条：
        数组['word',...] / 数组[{word,phonetic,meaning...}] /
        映射 {'n': {...}} / 带 data/words/list/items 包装。"""
        if isinstance(obj, dict):
            for k in ("data", "words", "list", "items"):
                if isinstance(obj.get(k), (list, dict)):
                    return DictionaryStore._extract_any_words(obj[k])
            if obj.get("word") or obj.get("headword") or obj.get("word_en"):
                return [obj]
            out = []
            for v in obj.values():
                if isinstance(v, dict) and (v.get("word") or v.get("headword")
                                            or v.get("word_en")):
                    out.append(v)
            return out
        if isinstance(obj, list):
            out = []
            for item in obj:
                if isinstance(item, dict):
                    if item.get("word") or item.get("headword") or item.get("word_en"):
                        out.append(item)
                elif isinstance(item, str) and item.strip():
                    out.append(item.strip())
            return out
        return []

    @staticmethod
    def _wordbook_entry(item):
        """把 KyleBing 顺序 JSON 的 translations/phrases 转成本地词条。"""
        if isinstance(item, str):
            word = item.strip().lower()
            return word, {"word": word} if word else None
        if not isinstance(item, dict):
            return "", None
        word = str(item.get("word") or item.get("headword")
                   or item.get("word_en") or "").strip().lower()
        if not word:
            return "", None

        entry = {"word": word}
        phonetic = (item.get("phonetic") or item.get("phonetics")
                    or item.get("pronunciation") or item.get("usphone")
                    or item.get("ukphone") or item.get("us") or item.get("uk"))
        if isinstance(phonetic, dict):
            phonetic = phonetic.get("us") or phonetic.get("uk") or phonetic.get("text")
        if phonetic:
            entry["phonetic"] = _pick_text(phonetic)

        defs = []
        translations = item.get("translations") or item.get("translation")
        if isinstance(translations, (list, tuple)):
            for trans in translations:
                if isinstance(trans, dict):
                    text = _pick_text(trans.get("translation") or trans.get("meaning")
                                      or trans.get("text"))
                    pos = _pick_text(trans.get("type") or trans.get("partOfSpeech"))
                    if text:
                        defs.append(f"{pos}. {text}" if pos else text)
                else:
                    text = _pick_text(trans)
                    if text:
                        defs.append(text)
        elif translations:
            text = _pick_text(translations)
            if text:
                defs.append(text)
        if not defs:
            for key in ("meaning", "chinese", "释义", "pos_def", "definition"):
                if item.get(key):
                    defs = _collect_defs(item[key], limit=4)
                    if defs:
                        break
        if defs:
            entry["pos_def"] = "\n".join(defs[:4])

        phrases = item.get("phrases") or []
        examples = []
        if isinstance(phrases, (list, tuple)):
            for phrase in phrases[:3]:
                if isinstance(phrase, dict):
                    p = _pick_text(phrase.get("phrase") or phrase.get("text"))
                    t = _pick_text(phrase.get("translation") or phrase.get("meaning"))
                    if p:
                        examples.append(f"{p} — {t}" if t else p)
                else:
                    text = _pick_text(phrase)
                    if text:
                        examples.append(text)
        sentences = item.get("sentences") or item.get("sentence") or []
        if isinstance(sentences, (list, tuple)):
            for sentence in sentences[:3]:
                if isinstance(sentence, dict):
                    en = _pick_text(sentence.get("sentence") or sentence.get("text")
                                    or sentence.get("english"))
                    zh = _pick_text(sentence.get("translation") or sentence.get("chinese")
                                    or sentence.get("meaning"))
                    if en:
                        examples.append(f"{en} — {zh}" if zh else en)
                else:
                    text = _pick_text(sentence)
                    if text:
                        examples.append(text)
        elif sentences:
            text = _pick_text(sentences)
            if text:
                examples.append(text)
        if not examples:
            example = _pick_text(item.get("example") or item.get("examples"))
            if example:
                examples.append(example)
        if examples:
            entry["example"] = "\n".join(examples)
        return word, entry

    def import_wordbook(self, src_path, label=None):
        """导入纯单词书（词表可无释义），注册为本地词书，供学习计划选择。"""
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"文件不存在：{src_path}")
        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
            try:
                obj = json.load(f)
            except Exception:
                raise ValueError("无法解析 JSON：文件不是有效的词书。")
        items = self._extract_any_words(obj)
        if not items:
            raise ValueError("未解析到任何单词。")
        word_map = {}
        for it in items:
            w, entry = DictionaryStore._wordbook_entry(it)
            if w and entry:
                word_map[w] = entry
        folder = self.dict_folder()
        base = os.path.basename(src_path)
        dest = os.path.join(folder, base)
        if os.path.exists(dest) and os.path.abspath(src_path) != os.path.abspath(dest):
            stem, ext = os.path.splitext(base)
            dest = os.path.join(folder, f"{stem}_{int(time.time())}{ext}")
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(word_map, f, ensure_ascii=False)
        record = {
            "filename": os.path.relpath(dest, DATA_DIR),
            "label": label or os.path.splitext(base)[0],
            "count": len(word_map),
            "kind": "online",
            "source": "KyleBing/english-vocabulary",
            "imported_at": time.time(),
        }
        self._data["files"].append(record)
        self._file_cache[record["filename"]] = word_map
        self.save()
        return record

    # ---------- 查词 ----------
    def get(self, word):
        """按 批量词条 → 各离线文件 的顺序查找。返回词条 dict 或 None。"""
        w = str(word).strip().lower()
        entry = self._data["batch"].get(w)
        if entry:
            return entry
        for record in self._data["files"]:
            entries = self._load_file_entries(record)
            entry = entries.get(w)
            if entry:
                return entry
        return None

    def stats(self):
        """返回 {"batch": int, "files": [(label, count), ...], "total": int}"""
        files = [(r.get("label", r["filename"]), r.get("count", 0)) for r in self._data["files"]]
        total = self.batch_count() + sum(c for _, c in files)
        return {"batch": self.batch_count(), "files": files, "total": total}
