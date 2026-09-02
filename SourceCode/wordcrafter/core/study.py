# ==============================================================================
# 文件路径: wordcrafter/core/study.py
# 学习状态仓储（记单词模块数据层）
#   - 单词集合统一来自 VocabRepository（生词库/阅读收藏/词典加入/导入 共享）
#   - 学习状态单独持久化 study_state.json（schema v1，容错加载，自动兜底）
# ==============================================================================
import datetime
import time

from .repository import data_path, _load_json, _save_json
from . import srs

STUDY_FILE = "study_state.json"


def _day_start(ts):
    return int(datetime.datetime.fromtimestamp(ts).strftime("%Y%m%d"))


class StudyRepository:
    """记单词学习状态：今日统计 / 学习队列 / 复习记录。"""

    def __init__(self):
        self.path = data_path(STUDY_FILE)
        data = _load_json(self.path, {})
        self.data = data if isinstance(data, dict) else {}

    def save(self):
        _save_json(self.path, self.data)

    # ---------- 基础访问 ----------
    def get(self, word):
        key = str(word).strip().lower()
        card = self.data.get(key)
        if card is None or not isinstance(card, dict):
            card = srs.new_card(key)
            self.data[key] = card
        return card

    def record_review(self, word, rating):
        """按用户反馈更新记忆状态并持久化。"""
        now = time.time()
        card = self.get(word)
        srs.review(card, rating, now=now)
        self.data[card["word"]] = card
        self.save()
        return card

    # ---------- 统计 / 队列 ----------
    def _words_state(self, words):
        return {w: self.data.get(w.lower()) for w in words}

    def stats(self, words, now=None):
        """返回今日统计（仅统计传入词表内的词，词表=统一生词库）。"""
        now = now or time.time()
        today = _day_start(now)
        counts = {
            "new": 0, "due": 0, "done_today": 0, "learning": 0,
            "review": 0, "relearning": 0, "mastered": 0,
        }
        for w in words:
            card = self.data.get(str(w).lower())
            if card is None or card.get("state") == srs.STATE_NEW:
                counts["new"] += 1
                continue
            state = card.get("state")
            if state in counts:
                counts[state] += 1
            if card.get("next_review", 0) <= now and state not in (srs.STATE_MASTERED,):
                counts["due"] += 1
            if card.get("last_review") and _day_start(card["last_review"]) == today:
                counts["done_today"] += 1
        return counts

    def build_session(self, words, daily_new=10, max_review=30, now=None):
        """组装一次学习会话：先到期复习，再补新词（受每日上限约束）。"""
        now = now or time.time()
        words = [str(w).strip().lower() for w in words if str(w).strip()]
        reviewed, fresh = [], []
        for w in words:
            card = self.data.get(w)
            if card is None or card.get("state") == srs.STATE_NEW:
                fresh.append(w)
            elif card.get("state") != srs.STATE_MASTERED and card.get("next_review", 0) <= now:
                reviewed.append(w)
        queue = reviewed[:max_review] + fresh[:daily_new]
        return queue

    def reset_word(self, word):
        key = str(word).strip().lower()
        self.data[key] = srs.new_card(key)
        self.save()
