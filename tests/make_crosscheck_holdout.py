#!/usr/bin/env python3
"""
Build holdout C: cross-source, dual-verified 字谜 holdout.

Sources (independent third party, no overlap with the hydcd corpus):
  tests/corpus/zhz_crosscheck.json  - scraped zhilezhi.com items
  tests/crosscheck.json             - dual-derivation metadata (scraped == my 拆字)

Only items whose answer is corroborated by an independent character decomposition
are emitted. Emits clue-only file + isolated answer key.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent

def main():
    pool, verified = [], {}
    if (ROOT / "crosscheck.json").exists():
        for r in json.load(open(ROOT / "crosscheck.json", encoding="utf-8")):
            if r.get("kind") == "字" and r.get("expected"):
                verified[r["clue"]] = r
    if (ROOT / "corpus" / "zhz_crosscheck.json").exists():
        for r in json.load(open(ROOT / "corpus" / "zhz_crosscheck.json", encoding="utf-8")):
            if r.get("kind") == "字" and r.get("expected"):
                pool.append(r)

    seen, out = set(), []
    for r in pool:
        c = r["clue"]
        if c in seen:
            continue
        seen.add(c)
        if c in verified:                       # keep the dual-verified record
            out.append(verified[c])
        # unverified zhz items are dropped on purpose

    with open(ROOT / "holdout_c.jsonl", "w", encoding="utf-8") as f:
        for i, r in enumerate(out, 1):
            f.write(json.dumps({"id": f"c{i:02d}", "clue": r["clue"], "mu": "打一字"},
                               ensure_ascii=False) + "\n")
    with open(ROOT / "holdout_c_answers.jsonl", "w", encoding="utf-8") as f:
        for i, r in enumerate(out, 1):
            f.write(json.dumps({"id": f"c{i:02d}", "expected": r["expected"],
                                "derivation": r.get("derivation", "")}, ensure_ascii=False) + "\n")
    print(f"holdout C: {len(out)} 条异源双路验证字谜（答案隔离在 holdout_c_answers.jsonl）")
    dropped = len({r["clue"] for r in pool}) - len(out)
    print(f"丢弃未双路验证条目: {dropped}")

if __name__ == "__main__":
    main()
