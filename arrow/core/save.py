# -*- coding: utf-8 -*-
"""存档：解锁进度与每关最好成绩（JSON 文件）。不依赖 pygame。

数据结构：
    {
      "unlocked": 3,                 # 已解锁的关卡数（1 起）
      "best": {"1": {"stars": 3, "score": 2450, "time": 18.4}, ...}
    }
文件损坏 / 缺失 / 字段异常时回退到默认值，绝不抛异常打断游戏。
"""

import json
import os
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "save.json"


def default_data():
    return {"unlocked": 1, "best": {}}


def load(path=None):
    """读取存档；任何异常都返回默认数据。"""
    path = Path(path) if path else DEFAULT_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        data = default_data()
        unlocked = raw.get("unlocked", 1)
        if isinstance(unlocked, int) and unlocked >= 1:
            data["unlocked"] = unlocked
        best = raw.get("best", {})
        if isinstance(best, dict):
            for key, value in best.items():
                if not isinstance(value, dict):
                    continue
                stars = value.get("stars")
                score = value.get("score")
                secs = value.get("time")
                if (isinstance(stars, int) and isinstance(score, int)
                        and isinstance(secs, (int, float))):
                    data["best"][str(key)] = {
                        "stars": stars, "score": score, "time": float(secs),
                    }
        return data
    except Exception:
        return default_data()


def store(data, path=None):
    """写入存档；写失败（如目录不可写）时静默忽略。"""
    path = Path(path) if path else DEFAULT_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except Exception:
        return False
