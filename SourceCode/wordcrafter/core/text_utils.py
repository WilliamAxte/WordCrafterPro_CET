# ==============================================================================
# 文件路径: wordcrafter/core/text_utils.py
# 包含工具: parse_words, read_text_any_encoding
# 供 tabs / ui 等模块共享的文本解析与文件读取逻辑
# ==============================================================================
import re

_WORD_SPLIT_RE = re.compile(r"[,，\n\r\t\s]+")
_NON_WORD_RE = re.compile(r"[^a-zA-Z\-]")
_ENCODINGS = ("utf-8", "gbk", "ansi")


def parse_words(text):
    """将文本按逗号/空格/换行切分，清洗为小写英文单词，去重并保持原有顺序。"""
    words = []
    for part in _WORD_SPLIT_RE.split(text):
        if not part.strip():
            continue
        word = _NON_WORD_RE.sub("", part).lower()
        if word and word not in words:
            words.append(word)
    return words


def read_text_any_encoding(path):
    """依次尝试常见编码读取文本文件，返回 (内容, 是否成功)。"""
    for enc in _ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(), True
        except Exception:
            continue
    return "", False
