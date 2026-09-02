# ==============================================================================
# 文件路径: wordcrafter/core/folders.py
# Sidebar 文件夹系统（历史记录分组）
#  folder: id/name/parent_id/sort_index/created_at
#  会话条目通过 session.folder_id 归属（在 SessionRepository 处理）
# ==============================================================================
import time
import uuid

from .repository import data_path, _load_json, _save_json

FOLDERS_FILE = "folders.json"


def new_id():
    return uuid.uuid4().hex[:12]


class FolderRepository:
    def __init__(self):
        self.path = data_path(FOLDERS_FILE)
        data = _load_json(self.path, [])
        self.folders = data if isinstance(data, list) else []

    def save(self):
        _save_json(self.path, self.folders)

    def create(self, name, parent_id=None):
        f = {"id": new_id(), "name": str(name).strip() or "未命名",
             "parent_id": parent_id, "sort_index": len(self.folders),
             "created_at": time.time()}
        self.folders.append(f)
        self.save()
        return f

    def get(self, fid):
        for f in self.folders:
            if f["id"] == fid:
                return f
        return None

    def rename(self, fid, name):
        f = self.get(fid)
        if f:
            f["name"] = str(name).strip() or f["name"]
            self.save()
            return True
        return False

    def delete(self, fid):
        """删除文件夹及其后代（会话条目会回到未归档，不删除内容）。"""
        before = len(self.folders)
        ids = {fid}
        changed = True
        while changed:
            changed = False
            for f in self.folders:
                if f.get("parent_id") in ids and f["id"] not in ids:
                    ids.add(f["id"])
                    changed = True
        self.folders = [f for f in self.folders if f["id"] not in ids]
        if len(self.folders) != before:
            self.save()
            return ids
        return set()

    def list_all(self):
        return list(self.folders)
