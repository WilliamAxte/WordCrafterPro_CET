# ==============================================================================
# Web UI 端到端测试（本地回环，无需真实网络）
# 运行: python -m unittest discover -s tests -v
# ==============================================================================
import json
import os
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import wordcrafter.core.repository as repo


class WebUITest(unittest.TestCase):
    def setUp(self):
        self._old_dir = repo.DATA_DIR
        self._old_cwd = os.getcwd()
        self._td = tempfile.TemporaryDirectory()
        repo.DATA_DIR = self._td.name
        os.chdir(self._td.name)

        from wordcrafter.qt.context import QtConfig
        from wordcrafter.core.study import StudyRepository
        from wordcrafter.core.deck import DeckRepository, DailyLogs
        from wordcrafter.core.session import SessionRepository
        from wordcrafter.webui import WebServer, WebState

        self.cfg = QtConfig()
        self.study = StudyRepository()
        self.decks = DeckRepository()
        self.logs = DailyLogs()
        self.sessions = SessionRepository()
        self.cfg.vocab_repo.add_words(["zeta", "nova"])
        self.cfg.vocab_repo.cache["zeta"] = {"word": "zeta", "phonetic": "/z/",
                                             "pos_def": "n. 第六个希腊字母",
                                             "example": "Zeta is a letter."}
        self.sessions.add("reading", "网页历史", summary="s",
                          content={"en": "Hello web.", "zh": "你好网页。"})
        state = WebState(self.cfg, self.study, self.decks, self.logs, self.sessions)
        self.server = WebServer(state, port=0, token="testtok")
        self.assertTrue(self.server.start())
        self.base = f"http://127.0.0.1:{self.server.port}"

    def tearDown(self):
        self.server.stop()
        os.chdir(self._old_cwd)
        repo.DATA_DIR = self._old_dir
        self._td.cleanup()

    def _get(self, path):
        req = urllib.request.Request(self.base + path,
                                     headers={"X-Token": "testtok"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post(self, path, payload):
        req = urllib.request.Request(
            self.base + path, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-Token": "testtok"},
            method="POST")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_auth_required(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(self.base + "/api/summary", timeout=8)
        self.assertEqual(cm.exception.code, 401)

    def test_index_page(self):
        req = urllib.request.Request(self.base + "/",
                                     headers={"X-Token": "testtok"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode("utf-8")
        self.assertIn("WordCrafter Web", body)
        self.assertIn("学习", body)

    def test_summary_and_study_review(self):
        s = self._get("/api/summary")
        self.assertGreaterEqual(s["vocab_total"], 2)
        # 创建一张到期卡 → 应进入复习
        self.study.record_review("zeta", "good")
        self.study.data["zeta"]["next_review"] = 0
        self.study.data["zeta"]["state"] = "LEARNING"
        self.study.save()
        sess = self._get("/api/study/session?mode=review")
        words = [w["word"] for w in sess["queue"]]
        self.assertIn("zeta", words)
        r = self._post("/api/study/review",
                       {"word": "zeta", "rating": "good"})
        self.assertTrue(r.get("ok"))
        self.assertGreaterEqual(self.study.get("zeta")["review_count"], 2)
        # 日志已记录并落盘
        from wordcrafter.core.deck import DailyLogs
        self.assertGreaterEqual(DailyLogs().get_day().get("total", 0), 1)

    def test_vocab_lookup_history(self):
        v = self._get("/api/vocab")
        self.assertGreaterEqual(len(v["words"]), 2)
        lk = self._get("/api/lookup?word=zeta")
        self.assertIn("希腊字母", lk.get("pos_def", ""))
        h = self._get("/api/history")
        self.assertGreaterEqual(h["total"], 1)
        d = self._get("/api/history?id=" + h["items"][0]["id"])
        self.assertEqual(d["en"], "Hello web.")

    def test_query_token_works(self):
        # 前端首页 URL 携带 ?token= 时，接口也必须可用（header 之外的第二条路径）
        req = urllib.request.Request(self.base + "/api/summary?token=testtok")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("vocab_total", data)

    def test_full_backend_flows(self):
        # 生词库删除
        r = self._post("/api/vocab/delete", {"word": "nova"})
        self.assertTrue(r.get("ok"))
        self.assertNotIn("nova", self.cfg.vocab_history)
        # 新建并切换学习计划
        r = self._post("/api/decks/create",
                       {"name": "Web计划", "source": "custom",
                        "words": ["alpha", "beta"]})
        self.assertTrue(r.get("ok"))
        decks = self._get("/api/decks")["decks"]
        self.assertTrue(any(d["name"] == "Web计划" and d["is_active"] for d in decks))
        # 历史导出下载
        h = self._get("/api/history")
        sid = h["items"][0]["id"]
        req = urllib.request.Request(self.base + f"/api/history/export?id={sid}&fmt=md",
                                     headers={"X-Token": "testtok"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode("utf-8")
            self.assertIn("Content-Disposition", str(resp.headers))
        self.assertIn("# 网页历史", body)
        # 历史删除
        r = self._post("/api/history/delete", {"id": sid})
        self.assertTrue(r.get("ok"))
        self.assertEqual(self._get("/api/history")["total"], 0)


if __name__ == "__main__":
    unittest.main()
