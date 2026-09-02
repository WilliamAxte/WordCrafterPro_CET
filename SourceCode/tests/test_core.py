# ==============================================================================
# WordCrafter 核心逻辑回归测试（无 GUI，纯 Python）
# 运行: python -m unittest discover -s tests -v
# ==============================================================================
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import wordcrafter.core.repository as repo


class IsolatedDataTestCase(unittest.TestCase):
    """把数据文件指向临时目录并切 CWD（避免回退命中真实文件）。"""

    def setUp(self):
        self._old_dir = repo.DATA_DIR
        self._old_cwd = os.getcwd()
        self._td = tempfile.TemporaryDirectory()
        repo.DATA_DIR = self._td.name
        os.chdir(self._td.name)

    def tearDown(self):
        os.chdir(self._old_cwd)
        repo.DATA_DIR = self._old_dir
        self._td.cleanup()


class SrsEngineTest(unittest.TestCase):
    def test_new_card_fields(self):
        from wordcrafter.core import srs
        card = srs.new_card("Apple")
        self.assertEqual(card["word"], "apple")
        self.assertEqual(card["state"], srs.STATE_NEW)
        # FSRS 升级预留字段
        for key in ("first_seen", "last_review", "next_review", "review_count",
                    "lapse_count", "interval_days", "stability", "difficulty",
                    "state", "rating_last"):
            self.assertIn(key, card)

    def test_forget_resets_then_progresses(self):
        from wordcrafter.core import srs
        card = srs.new_card("serendipity")
        srs.review(card, "forget")
        self.assertEqual(card["interval_days"], 1)
        self.assertEqual(card["lapse_count"], 1)
        self.assertIn(card["state"], (srs.STATE_LEARNING, srs.STATE_RELEARNING))
        srs.review(card, "good")
        srs.review(card, "good")
        srs.review(card, "easy")
        self.assertEqual(card["review_count"], 4)
        self.assertGreaterEqual(card["interval_days"], 1)
        self.assertGreater(card["next_review"], card["last_review"])

    def test_relearning_after_repeated_lapse(self):
        from wordcrafter.core import srs
        card = srs.new_card("x")
        srs.review(card, "forget")
        srs.review(card, "forget")
        self.assertEqual(card["state"], srs.STATE_RELEARNING)


class StudyRepositoryTest(IsolatedDataTestCase):
    def _repo(self):
        from wordcrafter.core.study import StudyRepository
        return StudyRepository()

    def test_record_and_persist(self):
        r = self._repo()
        card = r.record_review("Serendipity", "good")
        self.assertEqual(card["review_count"], 1)
        r2 = self._repo()
        self.assertEqual(r2.get("serendipity")["review_count"], 1)

    def test_stats_and_session(self):
        r = self._repo()
        words = ["alpha", "beta", "gamma"]
        r.record_review("alpha", "good")
        r.record_review("beta", "forget")
        # 制造一条到期复习：把 beta 的 next_review 置为过去
        r.data["beta"]["next_review"] = 0
        r.save()
        stats = r.stats(words)
        # alpha 学习中(未到期)；beta 到期复习；gamma 新词
        self.assertEqual(stats["new"], 1)
        self.assertGreaterEqual(stats["due"], 1)
        queue = r.build_session(words, daily_new=10, max_review=30)
        self.assertIn("beta", queue)   # 到期复习优先
        self.assertIn("gamma", queue)  # 新词补充
        self.assertNotIn("alpha", queue)


class TextUtilsTest(unittest.TestCase):
    def test_parse_words(self):
        from wordcrafter.core.text_utils import parse_words
        self.assertEqual(parse_words("Hello, world! 你好,hello"),
                         ["hello", "world"])

    def test_read_any_encoding(self):
        from wordcrafter.core.text_utils import read_text_any_encoding
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "a.txt")
            with open(p, "w", encoding="gbk") as f:
                f.write("中文,hello")
            content, ok = read_text_any_encoding(p)
            self.assertTrue(ok)
            self.assertIn("hello", content)


class DictionaryStoreTest(IsolatedDataTestCase):
    def test_import_lookup_remove(self):
        from wordcrafter.core.dictionary_store import DictionaryStore
        store = DictionaryStore()
        with tempfile.TemporaryDirectory() as td2:
            src = os.path.join(td2, "dict.json")
            with open(src, "w", encoding="utf-8") as f:
                f.write('{"apple": {"definition": "n. 苹果"}, "pear": {"definition": "n. 梨"}}')
            rec = store.import_file(src)
            self.assertEqual(rec["count"], 2)
            self.assertEqual(store.get("apple")["pos_def"], "n. 苹果")
            store.remove_file(rec["filename"])
            self.assertIsNone(store.get("apple"))

    def test_batch(self):
        from wordcrafter.core.dictionary_store import DictionaryStore
        store = DictionaryStore()
        store.set_batch_entries({"hello": {"pos_def": "你好"}})
        self.assertEqual(store.get("Hello")["pos_def"], "你好")
        store.clear_batch()
        self.assertIsNone(store.get("hello"))

    def test_import_wordbook_tolerant(self):
        from wordcrafter.core.dictionary_store import DictionaryStore
        store = DictionaryStore()
        with tempfile.TemporaryDirectory() as td2:
            src = os.path.join(td2, "wordbook.json")
            with open(src, "w", encoding="utf-8") as f:
                f.write('{"words": ["apple", {"word": "banana", "phonetic": "/b/", '
                        '"translation": "香蕉"}]}')
            rec = store.import_wordbook(src, label="CET4")
            self.assertGreaterEqual(rec["count"], 2)
            self.assertIn("apple", store._load_file_entries(rec))
            self.assertEqual(store.get("banana")["pos_def"], "香蕉")

    def test_version_is_2_0(self):
        from wordcrafter.services.updater import CURRENT_VERSION
        self.assertTrue(CURRENT_VERSION.startswith("v2."))


class SessionRepoTest(IsolatedDataTestCase):
    def test_crud_grouped(self):
        from wordcrafter.core.session import SessionRepository
        s = SessionRepository()
        s.add("reading", "测试文章", "摘要", {"a": 1})
        self.assertEqual(s.count(), 1)
        item = s.sessions[0]
        s.rename(item["id"], "新标题")
        self.assertEqual(s.get(item["id"])["title"], "新标题")
        s.toggle_favorite(item["id"])
        self.assertTrue(s.sessions[0]["favorite"])
        s.delete(item["id"])
        self.assertEqual(s.count(), 0)


class ConfigDefaultsTest(IsolatedDataTestCase):
    def test_defaults_include_new_keys(self):
        from wordcrafter.core.repository import ConfigRepository
        cfg = ConfigRepository()
        self.assertEqual(cfg.data.get("daily_new_words"), 10)
        self.assertEqual(cfg.data.get("daily_max_reviews"), 30)
        self.assertEqual(cfg.data.get("theme_accent"), "indigo")


class RendererTest(unittest.TestCase):
    def test_render_html_structures(self):
        from wordcrafter.qt.renderer import render_html
        en = "Title\n\nFirst para.\n\n- item a\n- item b\n\n> quote here"
        zh = "标题\n\n第一段。"
        h = render_html(en, zh, px=18, mode="dual", theme_key="light")
        self.assertIn("<h3>Title</h3>", h)
        self.assertIn("<p class='zh'>", h)
        self.assertIn("<blockquote>", h)
        self.assertIn("• item a", h)
        # 原文不被修改
        self.assertIn("First para.", h)

    def test_zh_only_and_en_only(self):
        from wordcrafter.qt.renderer import render_html
        en = "English text"
        zh = "中文文本"
        he = render_html(en, zh, mode="en", theme_key="dark")
        self.assertIn("English text", he)
        self.assertNotIn("中文文本", he)
        hz = render_html(en, zh, mode="zh", theme_key="dark")
        self.assertIn("中文文本", hz)


class TypographyTest(IsolatedDataTestCase):
    def test_steps(self):
        from wordcrafter.qt.typography import SIZE_STEPS, step_size
        self.assertEqual(step_size(None, "k", 18, -1), 16)
        self.assertEqual(step_size(None, "k", 18, 1), 20)
        self.assertIn(18, SIZE_STEPS)

    def test_save_load(self):
        from wordcrafter.qt.context import QtConfig
        from wordcrafter.qt.typography import get_saved_size, save_size
        cfg = QtConfig()
        save_size(cfg, "reading_font_size", 22)
        self.assertEqual(get_saved_size(cfg, "reading_font_size"), 22)
        save_size(cfg, "reading_font_size", 18)


class PronunciationTest(IsolatedDataTestCase):
    def test_play_dispatch(self):
        from wordcrafter.qt.context import QtConfig
        from wordcrafter.services import pronunciation as pron
        cfg = QtConfig()
        with mock.patch.object(pron.MicrosoftSpeechService, "speak_async") as m:
            pron.PronunciationService.play("hello", cfg)
            m.assert_called_once()
            args = m.call_args.args
            self.assertEqual(args[0], "hello")
            self.assertEqual(args[1], cfg.ms_speech_key)


if __name__ == "__main__":
    unittest.main()
