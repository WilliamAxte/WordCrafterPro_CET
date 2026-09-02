# ==============================================================================
# 文件路径: wordcrafter/core/srs.py
# 间隔重复引擎（SM-2 类算法，数据结构兼容未来升级 FSRS）
#
# 学习记录字段（均持久化）：
#   word, first_seen, last_review, next_review, review_count, lapse_count,
#   interval_days, stability(≈interval), difficulty(≈ease), state, rating_last
# 状态: NEW / LEARNING / REVIEW / RELEARNING / MASTERED
# 反馈映射: forget=1(重学) hard=3 good=4 easy=5
# ==============================================================================
import time

STATE_NEW = "NEW"
STATE_LEARNING = "LEARNING"
STATE_REVIEW = "REVIEW"
STATE_RELEARNING = "RELEARNING"
STATE_MASTERED = "MASTERED"

STATE_NAMES_CN = {
    STATE_NEW: "新词",
    STATE_LEARNING: "学习中",
    STATE_REVIEW: "复习中",
    STATE_RELEARNING: "待加强",
    STATE_MASTERED: "已掌握",
}

QUALITY = {"forget": 1, "hard": 3, "good": 4, "easy": 5}
DAY = 86400


def new_card(word, now=None):
    now = now or time.time()
    return {
        "word": str(word).strip().lower(),
        "state": STATE_NEW,
        "first_seen": now,
        "last_review": None,
        "next_review": now,          # 新词立即可以学习
        "review_count": 0,
        "lapse_count": 0,
        "repetitions": 0,            # 连续通过次数（SM-2 内部）
        "interval_days": 0,
        "stability": 0.0,
        "difficulty": 2.5,           # ease（SM-2）
        "rating_last": None,
    }


def review(card, rating, now=None):
    """执行一次复习反馈。card 就地更新；返回 card。"""
    now = now or time.time()
    q = QUALITY.get(rating, 3)
    ease = float(card.get("difficulty", 2.5) or 2.5)

    card["review_count"] = int(card.get("review_count", 0)) + 1
    card["last_review"] = now
    card["rating_last"] = rating

    if q < 3:
        # 失败：立即重学
        card["lapse_count"] = int(card.get("lapse_count", 0)) + 1
        card["repetitions"] = 0
        card["interval_days"] = 1
        card["state"] = STATE_RELEARNING if card["lapse_count"] >= 2 else STATE_LEARNING
    else:
        # SM-2 间隔：1 → 6 → 递增
        reps = int(card.get("repetitions", 0)) + 1
        prev_ivl = float(card.get("interval_days", 0) or 0)
        if reps == 1:
            ivl = 1
        elif reps == 2:
            ivl = 6
        else:
            ivl = max(1, round(prev_ivl * ease))
        card["repetitions"] = reps
        card["interval_days"] = ivl
        # ease 调整（q: 1..5）
        ease = max(1.3, min(3.0, ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))))
        card["difficulty"] = round(ease, 3)
        card["stability"] = float(ivl)
        if q == 5 and ivl >= 90:
            card["state"] = STATE_MASTERED
        else:
            card["state"] = STATE_REVIEW

    card["next_review"] = now + float(card.get("interval_days", 1)) * DAY
    return card
