#!/usr/bin/env python3
"""Build SkillOpt-style train/val/test splits for dengmi skill evolution.

- Source: tests/corpus/dengmi_corpus.json (zimi 3863 + chengyu 4117)
- Cleaning: same rules as tests/make_benchmark.py (三戒底面不相犯, 去样板污染)
- Exclusion: every clue already used in any existing test file under tests/
  (the tests/evolution/ output dir itself is skipped, so re-runs are idempotent)
- Stratified: train 100 (50+50), val 60 (30+30), test 60 (30+30), seed=20260928
- Outputs: tests/evolution/splits/evo_{train,val,test}_q.jsonl (id/clue/mu, NO answers)
            tests/evolution/splits/evo_{train,val,test}_key.jsonl (id/expected, scorer only)

Deterministic: same seed + same repo commit => byte-identical splits.
"""
import json, re, random, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TESTS = REPO / "tests"
OUT = REPO / "tests" / "evolution" / "splits"
SEED = 20260928
PLAN = {"train": 50, "val": 30, "test": 30}  # per category
BOILER = re.compile(r"(谜语是谜语|汉辞网|在线查询|第.页|百科知识|首\s*页)")

def collect_used_clues() -> set:
    used = set()
    for p in TESTS.rglob("*"):
        if "evolution" in p.parts:  # skip our own output dir (idempotent re-runs)
            continue
        if p.suffix not in (".json", ".jsonl") or "corpus" in str(p):
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if p.suffix == ".jsonl":
            for line in txt.splitlines():
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict) and r.get("clue"):
                    used.add(r["clue"].strip())
        else:
            try:
                d = json.loads(txt)
            except Exception:
                continue
            items = d if isinstance(d, list) else [d]
            stack = list(items)
            while stack:
                r = stack.pop()
                if isinstance(r, dict):
                    if r.get("clue"):
                        used.add(str(r["clue"]).strip())
                    stack.extend(r.values())
                elif isinstance(r, list):
                    stack.extend(r)
    return used

def clean(cat, items, maxlen):
    out, seen = [], set()
    for it in items:
        c, a = it["clue"].strip(), it["expected"].strip()
        if not c or not a or c in seen:
            continue
        if not (1 <= len(a) <= maxlen):
            continue
        if BOILER.search(c):
            continue
        if "<" in c or ">" in c:
            continue
        if any(ch in c for ch in a):  # 三戒：底面不相犯
            continue
        seen.add(c)
        out.append({"clue": c, "expected": a})
    return out

def main():
    random.seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    used = collect_used_clues()
    print(f"已用谜面(排除): {len(used)} 条")
    data = json.load(open(TESTS / "corpus" / "dengmi_corpus.json", encoding="utf-8"))
    rules = {"zimi": (1, "打一字"), "chengyu": (8, "打一成语")}
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            cwd=REPO, capture_output=True, text=True).stdout.strip()
    manifest = {"seed": SEED, "repo_commit": commit, "splits": {}}
    for split, n in PLAN.items():
        qs, keys = [], []
        for cat, (maxlen, mu) in rules.items():
            pool = [p for p in clean(cat, data[cat], maxlen) if p["clue"] not in used]
            pool.sort(key=lambda x: (abs(len(x["clue"]) - 8), x["clue"]))
            cands = pool[: n * 6]
            if len(cands) < n:
                raise SystemExit(f"候选不足: {split}/{cat} 仅 {len(cands)}")
            sample = random.sample(cands, n)
            for i, r in enumerate(sample, 1):
                rid = f"evo-{split}-{cat}-{i:02d}"
                qs.append({"id": rid, "clue": r["clue"], "mu": mu})
                keys.append({"id": rid, "expected": r["expected"]})
                used.add(r["clue"])  # 跨 split 去重
        random.shuffle(qs)
        (OUT / f"evo_{split}_q.jsonl").write_text(
            "\n".join(json.dumps(q, ensure_ascii=False) for q in qs) + "\n", encoding="utf-8")
        (OUT / f"evo_{split}_key.jsonl").write_text(
            "\n".join(json.dumps(k, ensure_ascii=False) for k in keys) + "\n", encoding="utf-8")
        manifest["splits"][split] = len(qs)
        print(f"{split}: {len(qs)} 题 -> evo_{split}_q.jsonl / evo_{split}_key.jsonl")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    print("manifest:", json.dumps(manifest, ensure_ascii=False))

if __name__ == "__main__":
    main()
