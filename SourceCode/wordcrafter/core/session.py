# ==============================================================================
# 文件路径: wordcrafter/core/session.py
# 包含组件: SessionRepository（WorkspaceSession 历史记录）
#
# 轻量的"会话/历史"抽象：记录每次生成任务（标题/摘要/模式参数快照），
# 供侧栏「今天/昨天/更早」分组导航。只新增 session_history.json，
# 不触碰任何既有数据文件。
# ==============================================================================
import datetime
import time
import uuid

from .repository import data_path, _load_json, _save_json

SESSION_FILE = "session_history.json"

KIND_NAMES = {
    "vocab": "情境短文",
    "reading": "经典精读",
    "acg": "ACG 特稿",
    "dictionary": "词典",
    "settings": "设置",
}


def new_id():
    return uuid.uuid4().hex[:12]


def _bucket_label(ts):
    """按时间分桶：今天 / 昨天 / 更早。"""
    now = datetime.date.today()
    d = datetime.date.fromtimestamp(ts)
    if d == now:
        return "今天"
    if d == now - datetime.timedelta(days=1):
        return "昨天"
    return "更早"


class SessionRepository:
    """会话历史仓储：条目只增改删，不做迁移破坏。"""

    def __init__(self):
        self.path = data_path(SESSION_FILE)
        self.sessions = self._load()

    def _load(self):
        data = _load_json(self.path, [])
        if not isinstance(data, list):
            return []
        return [s for s in data if isinstance(s, dict) and s.get("id")]

    def _save(self):
        _save_json(self.path, self.sessions)

    # ---------- CRUD ----------
    def add(self, kind, title, summary="", meta=None, content=None):
        """新建一条工作区会话。
        content: {"en": str, "zh": str} 生成内容（可完整恢复）；
        meta: 参数快照；folder_id 由文件夹模块赋值。"""
        now = time.time()
        item = {
            "id": new_id(),
            "kind": kind,
            "page_type": kind,          # 恢复时跳转的页面
            "title": title,
            "summary": summary or "",
            "content": dict(content) if content else None,
            "parameters": dict(meta) if meta else {},
            "folder_id": None,
            "display_settings": {},
            "favorite": False,
            "created_at": now,
            "updated_at": now,
        }
        self.sessions.insert(0, item)
        self._save()
        return item

    def update_content(self, sid, content=None, title=None, summary=None):
        """生成完成后回写/更新内容（内容较大，仅在需要时更新）。"""
        s = self.get(sid)
        if not s:
            return False
        if content is not None:
            s["content"] = dict(content)
        if title is not None:
            s["title"] = str(title).strip() or s["title"]
        if summary is not None:
            s["summary"] = str(summary)[:500]
        s["updated_at"] = time.time()
        self._save()
        return True

    def move_to_folder(self, sid, folder_id):
        s = self.get(sid)
        if not s:
            return False
        s["folder_id"] = folder_id
        self._save()
        return True

    def get(self, sid):
        for s in self.sessions:
            if s["id"] == sid:
                return s
        return None

    def rename(self, sid, title):
        s = self.get(sid)
        if not s:
            return False
        s["title"] = str(title).strip() or s["title"]
        s["updated_at"] = time.time()
        self._save()
        return True

    def delete(self, sid):
        before = len(self.sessions)
        self.sessions = [s for s in self.sessions if s["id"] != sid]
        if len(self.sessions) != before:
            self._save()
            return True
        return False

    def touch(self, sid, title=None, summary=None, meta=None):
        """更新某条会话（生成完成后回写摘要/参数）。"""
        s = self.get(sid)
        if not s:
            return False
        if title is not None:
            s["title"] = str(title).strip() or s["title"]
        if summary is not None:
            s["summary"] = str(summary)[:500]
        if meta is not None:
            s["meta"].update(meta)
        s["updated_at"] = time.time()
        self._save()
        return True

    def toggle_favorite(self, sid):
        s = self.get(sid)
        if not s:
            return False
        s["favorite"] = not s.get("favorite", False)
        self._save()
        return s["favorite"]

    # ---------- 导出 ----------
    def export_session(self, sid, path, fmt="txt"):
        """把会话内容导出为 TXT 或 Markdown；无内容记录仅导出标题。"""
        s = self.get(sid)
        if not s:
            return None
        content = s.get("content") or {}
        en = (content.get("en") or "").strip()
        zh = (content.get("zh") or "").strip()
        title = s.get("title", "未命名")
        params = s.get("parameters") or {}
        if fmt == "md":
            lines = [f"# {title}", ""]
            if params:
                lines.append("> 参数：" + " · ".join(
                    f"{k}={v}" for k, v in list(params.items())[:6]))
                lines.append("")
            if en:
                lines += ["## English", "", en, ""]
            if zh:
                lines += ["## Chinese", "", zh, ""]
            text = "\n".join(lines)
        else:
            lines = [f"=== {title} ==="]
            if en:
                lines += ["", en]
            if zh:
                lines += ["", "=== Chinese ===", "", zh]
            text = "\n".join(lines)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    # ---------- 查询 / 分组 ----------
    def list_all(self, query=None, favorites_only=False):
        items = self.sessions
        if favorites_only:
            items = [s for s in items if s.get("favorite")]
        if query:
            q = query.lower()
            items = [s for s in items
                     if q in s.get("title", "").lower()
                     or q in s.get("summary", "").lower()
                     or q in KIND_NAMES.get(s.get("kind", ""), "").lower()]
        return list(items)

    def grouped(self, query=None, favorites_only=False):
        """返回 [(分桶名, [item, ...]), ...]，桶顺序 今天/昨天/更早。"""
        items = self.list_all(query=query, favorites_only=favorites_only)
        buckets = {}
        for s in items:
            label = _bucket_label(s.get("created_at", time.time()))
            buckets.setdefault(label, []).append(s)
        order = {"今天": 0, "昨天": 1}
        ordered = sorted(buckets.items(),
                         key=lambda kv: (order.get(kv[0], 2), kv[0]))
        return ordered

    def count(self):
        return len(self.sessions)
