# ==============================================================================
# 文件路径: ui_components.py
# 统一聚合导出入口
# ==============================================================================
from ui_base import ModernTextBox, WordTranslationCard, FullscreenReader, UpdateDialog
from ui_vocab_manager import ModernWordCard, VocabManagerWindow
from ui_cards import CollapsibleCard
from ui_music import AppleMusicDrawer

__all__ = [
    "ModernTextBox",
    "WordTranslationCard",
    "FullscreenReader",
    "UpdateDialog",
    "ModernWordCard",
    "VocabManagerWindow",
    "CollapsibleCard",
    "AppleMusicDrawer"
]