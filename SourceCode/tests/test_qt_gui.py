# ==============================================================================
# WordCrafter Qt GUI 回归测试（offscreen 无头）
# 运行: python -m unittest discover -s tests -v
# 数据全部写入临时目录；词典查询预填缓存，避免网络。
# ==============================================================================
import importlib.util
import os
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

if importlib.util.find_spec("PySide6") is None:
    raise unittest.SkipTest("PySide6 未安装")

import wordcrafter.core.repository as repo  # noqa: E402

from PySide6.QtWidgets import QApplication  # noqa: E402


def _pump(app, n=15):
    for _ in range(n):
        app.processEvents()


class QtGuiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._old_dir = repo.DATA_DIR
        self._old_cwd = os.getcwd()
        self._td = tempfile.TemporaryDirectory()
        repo.DATA_DIR = self._td.name
        os.chdir(self._td.name)
        self.window = None

    def tearDown(self):
        if self.window is not None:
            try:
                self.window.close()
            except Exception:
                pass
        os.chdir(self._old_cwd)
        repo.DATA_DIR = self._old_dir
        self._td.cleanup()

    def _main(self):
        from wordcrafter.qt.chrome import MainWindow
        self.window = MainWindow()
        self.window.show()
        _pump(self.app)
        return self.window

    def _seed_cache(self, words):
        cache = {w: {"word": w, "phonetic": f"/{w}/",
                     "pos_def": f"n. 释义 {w}", "example": f"Example {w}."}
                 for w in words}
        self.window.config.vocab_repo.cache.update(cache)

    def test_boot_and_modes(self):
        w = self._main()
        self.assertEqual(sorted(w.pages),
                         ["acg", "dictionary", "reading", "settings", "study", "vocab"])
        for m in ("vocab", "study", "reading", "acg", "dictionary", "settings"):
            w.switch_mode(m)
            _pump(self.app)

    def test_study_flow_offline(self):
        w = self._main()
        self._seed_cache(w.config.vocab_history)
        w.switch_mode("study")
        _pump(self.app)
        sp = w.pages["study"]
        sp.start_session()
        _pump(self.app)
        self.assertTrue(sp.queue)
        first = sp.queue[0]
        sp.reveal()
        _pump(self.app, 8)
        self.assertTrue(sp.revealed)
        # 本地缓存命中：释义应出现
        self.assertIn("释义", sp.lbl_answer.text())
        # 评分 → 持久化（临时目录）
        sp.rate("good")
        _pump(self.app)
        from wordcrafter.core.study import StudyRepository
        r = StudyRepository()
        self.assertGreaterEqual(r.get(first)["review_count"], 1)

    def test_reading_autop_render(self):
        w = self._main()
        w.switch_mode("reading")
        _pump(self.app)
        rp = w.pages["reading"]
        rp._en = "A Brave New Start\n\nBody paragraph here."
        rp._zh = "崭新的开始\n\n正文段落。"
        rp.autop = True
        rp.set_state("content")
        _pump(self.app)
        self.assertIs(rp.body_sw.currentWidget(), rp.doc)
        html = rp.doc.toHtml()
        self.assertIn("Body paragraph here", html)

    def test_immersion_fullscreen_toggle(self):
        w = self._main()
        from wordcrafter.qt.immersion import ImmersionReader
        reader = ImmersionReader(w.config, "T", "Hello world.", "你好世界。")
        reader.show()
        reader.showFullScreen()
        _pump(self.app)
        self.assertTrue(reader.isFullScreen())
        reader._toggle_fullscreen()
        _pump(self.app)
        self.assertFalse(reader.isFullScreen())
        reader.close()

    def test_vocab_dialog_opens(self):
        w = self._main()
        self._seed_cache(w.config.vocab_history)
        from wordcrafter.qt.vocab_dialog import VocabManagerDialog
        dlg = VocabManagerDialog(w)
        dlg.show()
        _pump(self.app, 20)
        self.assertGreater(dlg.list_layout.count() - 1, 0)
        # 每一行必须存在 🔊 发音按钮
        first = dlg.list_layout.itemAt(0).widget()
        self.assertTrue(hasattr(first, "btn_voice"))
        self.assertEqual(first.btn_voice.text(), "🔊")
        dlg.close()

    def test_history_persist_restore_and_page_state(self):
        w = self._main()
        rp = w.pages["reading"]
        rp._en = "Restored paragraph one."
        rp._zh = "恢复第一段。"
        w.add_session("reading", "历史文章", summary="摘要",
                      meta={"work": "历史文章", "length": "中篇"},
                      content={"en": rp._en, "zh": rp._zh})
        # 页面切换不丢内容
        w.switch_mode("acg")
        _pump(self.app)
        w.switch_mode("reading")
        _pump(self.app)
        self.assertEqual(rp._en, "Restored paragraph one.")
        # 模拟重启：同临时数据目录重建窗口
        sid = w.sidebar.sessions.sessions[0]["id"]
        w.close()
        self.window = None
        from wordcrafter.qt.chrome import MainWindow
        w2 = MainWindow()
        self.window = w2
        w2.show()
        _pump(self.app)
        sess = w2.sidebar.sessions.get(sid)
        self.assertIsNotNone(sess)
        self.assertTrue(sess.get("content"))
        w2.open_session(sess)
        _pump(self.app)
        rp2 = w2.pages["reading"]
        self.assertEqual(rp2._en, "Restored paragraph one.")
        self.assertTrue(rp2.stack.currentWidget() is rp2.reader)

    def test_study_deck_gate_and_logs(self):
        w = self._main()
        from wordcrafter.core import srs as s
        # 自定义 Deck：zeta 已学待复习、nova 保持新词
        deck = w.decks.create("自定义Unit1", "custom", words=["zeta", "nova"])
        w.decks.set_active(deck["id"])
        w.study.record_review("zeta", "good")
        w.study.data["zeta"]["next_review"] = 0      # 模拟第二天到期
        w.study.data["zeta"]["state"] = s.STATE_LEARNING
        w.study.save()
        w.switch_mode("study")
        _pump(self.app)
        sp = w.pages["study"]
        # 到期>0 → 复习可用、新词锁定
        self.assertTrue(sp.btn_review.isEnabled())
        self.assertFalse(sp.btn_new_words.isEnabled())
        sp.start_review()
        _pump(self.app)
        self.assertTrue(sp.queue)
        self.assertEqual(sp.queue[0], "zeta")
        while sp.queue and sp.pos < len(sp.queue):
            sp.reveal()
            sp.rate("good")
            _pump(self.app)
        # 完成到期复习后新词解锁
        sp.show_overview()
        _pump(self.app)
        self.assertFalse(sp.btn_review.isEnabled())
        self.assertTrue(sp.btn_new_words.isEnabled())
        # 日志持久化 + 树视图
        day = w.logs.get_day()
        self.assertGreaterEqual(day.get("total", 0), 1)
        self.assertGreaterEqual(day.get("review", 0), 1)
        self.assertGreaterEqual(sp.tree.topLevelItemCount(), 1)

    def test_sidebar_folders_and_export(self):
        w = self._main()
        f = w.folders.create("CET-4")
        sess = w.sidebar.add_session_entry(
            "reading", "导出测试", summary="s", content={"en": "Hello.", "zh": "你好。"})
        w.sidebar.sessions.move_to_folder(sess["id"], f["id"])
        w.sidebar.refresh()
        texts = [w.sidebar.list_history.item(i).text()
                 for i in range(w.sidebar.list_history.count())]
        self.assertTrue(any("CET-4" in t for t in texts))
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "out.md")
            w.sidebar.sessions.export_session(sess["id"], p, "md")
            self.assertTrue(os.path.exists(p))
            with open(p, encoding="utf-8") as fh:
                self.assertIn("# 导出测试", fh.read())

    def test_newspaper_columns(self):
        w = self._main()
        from wordcrafter.qt.newspaper import NewspaperReader
        reader = NewspaperReader(w.config, "T", "P1 text.\n\nP2 text.\n\nP3 text.",
                                 "一。\n\n二。\n\n三。")
        reader.show()
        reader.resize(2000, 900)
        _pump(self.app)
        reader.columns_choice = "2"
        reader._rebuild()
        _pump(self.app)
        self.assertEqual(len(reader._column_edits), 2)
        reader.columns_choice = "auto"
        reader.resize(900, 700)
        _pump(self.app)
        self.assertEqual(reader._n_columns(), 1)
        reader.close()

    def test_doc_uses_theme_accent(self):
        w = self._main()
        rp = w.pages["reading"]
        rp._en = "# Accent heading test"
        rp._zh = ""
        rp.autop = True
        rp.set_state("content")
        _pump(self.app)
        from wordcrafter.qt.theme import is_light_mode
        accent = w.config.c_primary[0 if is_light_mode(w.config) else 1].lower()
        self.assertIn(accent, rp.doc.toHtml().lower())
        self.assertIn("accent heading test", rp.doc.toPlainText().lower())


if __name__ == "__main__":
    unittest.main()
