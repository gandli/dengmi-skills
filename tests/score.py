#!/usr/bin/env python3
"""
Score predictions against an answer key.

Usage:
  python3 tests/score.py [predictions.jsonl] [answers.jsonl]
    defaults: tests/predictions.jsonl  tests/answers.jsonl

predictions.jsonl format (one per line):  {"id": "zimi-01", "answer": "..."}
answers.jsonl   format (one per line):  {"id": "zimi-01", "expected": "..."}
Scores exact match; also reports fuzzy (answer substring of expected or reverse).
Note: unknown ids in predictions are ignored — only ids in the key are scored.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent

def main():
    pred_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "predictions.jsonl"
    key_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "answers.jsonl"
    if not pred_path.exists():
        print("尚未提交预测。请先编辑 tests/predictions.jsonl 或传入预测文件：")
        print("  python3 tests/score.py tests/predictions.jsonl")
        print("预测格式（每行一条）： {\"id\": \"zimi-01\", \"answer\": \"亲\"}")
        sys.exit(2)

    key = {}
    with open(key_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                key[r["id"]] = r["expected"]

    preds = {}
    with open(pred_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                preds[r["id"]] = r.get("answer", "").strip()

    exact = fuzzy = missed = 0
    per_cat = {}
    wrong = []
    for rid, expected in key.items():
        got = preds.get(rid, "")
        cat = rid.split("-")[0]
        per_cat.setdefault(cat, {"exact": 0, "total": 0, "fuzzy": 0})
        per_cat[cat]["total"] += 1
        if got == expected:
            exact += 1
            per_cat[cat]["exact"] += 1
        elif (got and got in expected) or (got and expected in got):
            fuzzy += 1
            per_cat[cat]["fuzzy"] += 1
            wrong.append((rid, expected, got, "近似"))
        elif got:
            wrong.append((rid, expected, got, "错误"))
        else:
            missed += 1
            wrong.append((rid, expected, got, "未答"))

    total = len(key)
    print(f"=== 盲测评分 [{key_path.name}] 共 {total} 题，已答 {total - missed} ===")
    for cat, s in sorted(per_cat.items()):
        acc = s["exact"] / max(s["total"], 1) * 100
        print(f"[{cat}] 精确命中 {s['exact']}/{s['total']} ({acc:.1f}%)  近似 {s['fuzzy']}")
    print(f"\n总计精确命中率: {exact}/{total} ({exact / max(total, 1) * 100:.1f}%)")
    print(f"近似（含子串重叠）: {fuzzy}   未答: {missed}")

    if wrong:
        print("\n未精确命中明细（最多列 20 条）:")
        for rid, expected, got, why in wrong[:20]:
            print(f"  [{rid}] 谜底={expected!r} 预测={got!r} ({why})")
        if len(wrong) > 20:
            print(f"  ...共 {len(wrong)} 条")

if __name__ == "__main__":
    main()
