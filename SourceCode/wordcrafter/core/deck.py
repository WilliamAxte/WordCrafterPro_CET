# ==============================================================================
# 文件路径: wordcrafter/core/deck.py
# 学习计划 StudyDeck + 每日学习日志（记单词模块数据层 v2）
# ==============================================================================
import time
import uuid

from .repository import data_path, _load_json, _save_json

DECKS_FILE = "decks.json"
LOGS_FILE = "daily_logs.json"

RATING_KEYS = ("forget", "hard", "good", "easy")


def new_id():
    return uuid.uuid4().hex[:12]


class DeckRepository:
    """StudyDeck：学习计划（多来源，独立于 VocabRepository 的已学词卡）。"""

    def __init__(self):
        self.path = data_path(DECKS_FILE)
        data = _load_json(self.path, [])
        self.decks = data if isinstance(data, list) else []

    def save(self):
        _save_json(self.path, self.decks)

    def create(self, name, source_type, source_id=None, words=None, config=None):
        d = {
            "id": new_id(),
            "name": str(name).strip() or "新计划",
            "source_type": source_type,          # vocab | custom | local_dict
            "source_id": source_id,              # 词典文件 filename 等
            "words": [str(w).strip().lower() for w in (words or []) if str(w).strip()],
            "config": dict(config or {}),
            "daily_new_limit": 10,
            "daily_review_limit": 30,
            "created_at": time.time(),
            "updated_at": time.time(),
            "is_active": False,
        }
        self.decks.append(d)
        self.save()
        return d

    def get(self, did):
        for d in self.decks:
            if d["id"] == did:
                return d
        return None

    def set_active(self, did):
        for d in self.decks:
            d["is_active"] = (d["id"] == did)
        self.save()

    def active(self):
        for d in self.decks:
            if d.get("is_active"):
                return d
        return self.decks[0] if self.decks else None

    def delete(self, did):
        before = len(self.decks)
        self.decks = [d for d in self.decks if d["id"] != did]
        if len(self.decks) != before:
            self.save()
            return True
        return False

    def word_set(self, deck, cfg):
        """解析来源得到学习词表（生词库实时 / 自定义 / 本地词典词书）。"""
        if not deck:
            return []
        src = deck.get("source_type")
        if src == "vocab":
            return [str(w).strip().lower() for w in cfg.vocab_history]
        if src == "custom":
            return list(deck.get("words", []))
        if src == "local_dict":
            # 取已导入离线词典文件中的全部词条作为词书
            store = cfg.dictionary_store
            for rec in store.list_files():
                if rec["filename"] == deck.get("source_id"):
                    entries = store._load_file_entries(rec)
                    return [w for w in entries if isinstance(w, str)]
            return list(deck.get("words", []))
        return [str(w).strip().lower() for w in cfg.vocab_history]


class DailyLogs:
    """每日学习日志：date -> {new, review, total, forget, hard, good, easy, words:[]}"""

    def __init__(self):
        self.path = data_path(LOGS_FILE)
        data = _load_json(self.path, {})
        self.data = data if isinstance(data, dict) else {}

    def save(self):
        _save_json(self.path, self.data)

    @staticmethod
    def _key(ts):
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    def record(self, ts, is_new, rating, word):
        k = self._key(ts)
        day = self.data.setdefault(k, {"new": 0, "review": 0, "total": 0,
                                       "forget": 0, "hard": 0, "good": 0,
                                       "easy": 0, "words": []})
        if is_new:
            day["new"] += 1
        else:
            day["review"] += 1
        day["total"] += 1
        if rating in RATING_KEYS:
            day[rating] += 1
        if word not in day["words"]:
            day["words"].append(word)
        self.save()

    def get_day(self, ts=None):
        import time as _t
        return self.data.get(self._key(ts if ts is not None else _t.time()), {})

    def recent(self, days=7):
        import datetime
        out = []
        for i in range(days - 1, -1, -1):
            k = (datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            out.append((k, self.data.get(k, {})))
        return out
