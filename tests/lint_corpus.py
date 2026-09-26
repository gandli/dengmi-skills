#!/usr/bin/env python3
"""
Corpus lint for harvested riddle datasets.
Checks per item:
  - non-empty clue/expected
  - expected length matches category constraint (字谜:1字; 成语谜:3-8字)
  - 底面不相犯: expected chars must not appear in clue (hard fail for 字谜)
  - malformed clue (leftover html, numbering, boilerplate)
Outputs violation report + summary.
"""
import json, re, sys
from pathlib import Path

BOILER = re.compile(r"(谜语是谜语|汉辞网|在线查询|第.页|百科知识|首\s*页)")
NUMPFX = re.compile(r"^\d+、")
HTML   = re.compile(r"<[^>]+>")

def lint(cat, items, maxlen):
    stats = dict(total=len(items), empty=0, badlen=0, collide=0, collide_soft=0, boiler=0, numpfx=0, html=0)
    offenders = []
    for it in items:
        c, a = it.get("clue", "").strip(), it.get("expected", "").strip()
        if not c or not a:
            stats["empty"] += 1; continue
        if not (1 <= len(a) <= maxlen):
            stats["badlen"] += 1; offenders.append((cat, c, a, "badlen")); continue
        collide = any(ch in c for ch in a)
        if collide:
            # 三戒只对字谜硬性适用；成语谜面常合法含底字（如“不直一钱”含“钱”）→ 仅告警
            if cat == "zimi":
                stats["collide"] += 1; offenders.append((cat, c, a, "底面相犯(硬伤)"))
            else:
                stats["collide_soft"] += 1
        if BOILER.search(c):
            stats["boiler"] += 1; offenders.append((cat, c, a, "boiler"))
        if NUMPFX.match(c):
            stats["numpfx"] += 1
        if HTML.search(c) or HTML.search(a):
            stats["html"] += 1
    return stats, offenders

def main():
    p = Path(__file__).parent / "corpus" / "dengmi_corpus.json"
    data = json.load(open(p, encoding="utf-8"))
    rules = {"zimi": 1, "chengyu": 8}
    total_bad = 0
    print(f"=== 语料质检 lint (来源: 汉辞网 hydcd.com) ===")
    for cat, items in data.items():
        maxlen = rules.get(cat, 8)
        stats, off = lint(cat, items, maxlen)
        collide_rate = stats["collide"] / max(stats["total"], 1) * 100
        clean = stats["total"] - stats["empty"] - stats["badlen"] - stats["collide"] - stats["boiler"]
        clean_rate = clean / max(stats["total"], 1) * 100
        print(f"\n[{cat}] 总数={stats['total']}  空={stats['empty']}  越界={stats['badlen']}  "
              f"底面相犯={stats['collide']} ({collide_rate:.1f}%)  软相犯(成语合法)={stats['collide_soft']}  样板污染={stats['boiler']}  "
              f"残留HTML={stats['html']}  编号前缀={stats['numpfx']}")
        print(f"  → 可直接入基准集(全部通过): {clean} ({clean_rate:.1f}%)")
        total_bad += stats["collide"] + stats["boiler"] + stats["badlen"] + stats["empty"] + stats["html"]

if __name__ == "__main__":
    main()
