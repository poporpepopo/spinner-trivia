#!/usr/bin/env python3
"""SessionStart hook: 豆知識の一覧から選び、スピナーの表示を差し替える。

- ~/.claude/spinner-trivia/verbs/*.txt → settings.json の spinnerVerbs
  （1行1件、# 始まりと空行は無視）。spinnerTipsOverride.label もここで選び直す
- ~/.claude/spinner-trivia/tips/*.txt → ~/.claude/spinner-tips.json
  （1行1件で「id 本文」。settings.json の spinnerTipsOverride.tipsFile が読む）

一度選んだものは state.json に記録し、一覧を1周するまではまだ選んでいないものから選ぶ。
1周したら記録をリセットする。

settings.json は読めなかったら触らず、書き込みは一時ファイル経由で置き換える。
"""
import json
import os
import random
import sys
import tempfile
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
POOL_DIR = CLAUDE_DIR / "spinner-trivia"
STATE_FILE = POOL_DIR / "state.json"
SETTINGS = CLAUDE_DIR / "settings.json"
TIPS_FILE = CLAUDE_DIR / "spinner-tips.json"

# スピナーは表示のたびにこのリストから1件を選ぶので、セッションごとの入れ替え分だけ持てばよい
VERB_PICK = 100
# Claude Code が tipsFile から読むのは200件まで
TIP_PICK = 200
TIP_COOLDOWN_SESSIONS = 20
# Tips の頭に付くラベル。スピナーの文言とは無関係な話だとわかるように、話題を変える言葉にする。
# ラベルは設定に1つしか持てないので、セッションごとに選び直す
TIP_LABELS = ["ところで", "余談", "ちなみに", "それはそうと", "話は変わって", "ついでに"]


def load_lines(kind):
    lines = []
    for path in sorted((POOL_DIR / kind).glob("*.txt")):
        for s in path.read_text(encoding="utf-8").splitlines():
            s = s.strip()
            if s and not s.startswith("#"):
                lines.append(s)
    return lines


def write_json(path, data, mode=None):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}.", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    if mode is not None:
        os.chmod(tmp, mode)
    os.replace(tmp, path)


def load_state():
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def pick(keys, seen, n):
    """まだ選んでいないものから n 件選び、(選んだもの, 新しい既出の記録) を返す。

    未選択が n 件に足りなければ残りを全部選び、記録をリセットして不足分を補う。
    """
    seen = set(seen) & set(keys)
    unseen = [k for k in keys if k not in seen]
    if len(unseen) >= n:
        picked = random.sample(unseen, n)
        return picked, seen | set(picked)
    rest = [k for k in keys if k not in set(unseen)]
    fill = random.sample(rest, min(n - len(unseen), len(rest)))
    return unseen + fill, set(fill)


def update_settings(seen):
    verbs = list(dict.fromkeys(load_lines("verbs")))
    if not verbs:
        return seen
    try:
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return seen
    picked, seen = pick(verbs, seen, VERB_PICK)
    random.shuffle(picked)
    settings["spinnerVerbs"] = {"mode": "replace", "verbs": picked}
    override = settings.get("spinnerTipsOverride")
    if isinstance(override, dict):
        override["label"] = random.choice(TIP_LABELS)
    write_json(SETTINGS, settings, SETTINGS.stat().st_mode & 0o777)
    return seen


def update_tips(seen):
    tips = {}
    for line in load_lines("tips"):
        tip_id, _, text = line.partition(" ")
        if text.strip():
            tips.setdefault(tip_id, text.strip())
    if not tips:
        return seen
    picked, seen = pick(list(tips), seen, TIP_PICK)
    random.shuffle(picked)
    write_json(TIPS_FILE, [
        {"id": tip_id, "text": tips[tip_id], "cooldownSessions": TIP_COOLDOWN_SESSIONS}
        for tip_id in picked
    ], 0o644)
    return seen


if __name__ == "__main__":
    state = load_state()
    for key, step in (("verbs", update_settings), ("tips", update_tips)):
        try:
            state[key] = sorted(step(state.get(key, [])))
        except Exception as e:  # 起動を邪魔しない
            print(f"spinner-trivia: {step.__name__}: {e}", file=sys.stderr)
    try:
        write_json(STATE_FILE, state)
    except Exception as e:
        print(f"spinner-trivia: state: {e}", file=sys.stderr)
