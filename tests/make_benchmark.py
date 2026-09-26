#!/usr/bin/env python3
"""
Build a benchmark split from the harvested corpus.

Two outputs:
  tests/benchmark.jsonl  — blind eval: clue + 谜目 only (no answer), 40 per category
  tests/answers.jsonl    — matching answer key, id -> clue/expected

Blind split lets you (or an agent) actually solve before grading.
Run `python3 tests/score.py` after writing your answers into tests/predictions.jsonl.
"""
import json, re, random
from pathlib import Path

ROOT = Path(__file__).parent
BOILER = re.compile(r"(谜语是谜语|汉辞网|在线查询|第.页|百科知识|首\s*页)")
N = 40

def clean(cat, items, maxlen):
    out = []
    for it in items:
        c, a = it["clue"].strip(), it["expected"].strip()
        if not c or not a: continue
        if not (1 <= len(a) <= maxlen): continue
        if BOILER.search(c): continue
        if "<" in c or ">" in c: continue
        if any(ch in c for ch in a): continue      # 三戒：底面不相犯
        out.append({"clue": c, "expected": a})
    return out

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--out", default="benchmark")
    ap.add_argument("--exclude", default="", help="jsonl file whose clues must be excluded")
    ap.add_argument("--kind", default="both", choices=["both","zimi","chengyu"])
    a = ap.parse_args()
    random.seed(a.seed)
    N = a.n
    data = json.load(open(ROOT / "corpus" / "dengmi_corpus.json", encoding="utf-8"))
    rules = {"zimi": (1, "打一字"), "chengyu": (8, "打一成语")}
    if a.kind != "both":
        rules = {k: v for k, v in rules.items() if k == a.kind}

    excl = set()
    for path in [x for x in a.exclude.split(",") if x]:
        for l in open(path, encoding="utf-8"):
            if not l.strip():
                continue
            r = json.loads(l)
            if "clue" in r:                 # 跳过注记行（如 holdout_b 的 INVALID 标记）
                excl.add(r["clue"])

    bench, key = [], {}
    for cat, (maxlen, mu) in rules.items():
        pool = [p for p in clean(cat, data[cat], maxlen) if p["clue"] not in excl]
        # 偏好中等长度谜面：太短难解，太长常含整句
        pool.sort(key=lambda x: (abs(len(x["clue"]) - 8), x["clue"]))
        picked = pool[: N * 3]
        sample = random.sample(picked, min(N, len(picked)))
        for i, r in enumerate(sample, 1):
            rid = f"{cat}-{i:02d}"
            bench.append({"id": rid, "clue": r["clue"], "mu": mu})
            key[rid] = r["expected"]

    with open(ROOT / f"{a.out}.jsonl", "w", encoding="utf-8") as f:
        for b in bench:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    with open(ROOT / f"{a.out}_answers.jsonl", "w", encoding="utf-8") as f:
        for k, v in key.items():
            f.write(json.dumps({"id": k, "expected": v}, ensure_ascii=False) + "\n")
    print(f"{a.out}.jsonl: {len(bench)} 题（无答案）  {a.out}_answers.jsonl: {len(key)} 条答案键  seed={a.seed}")
    for b in bench[:4]:
        print("  ", b)

if __name__ == "__main__":
    main()
