#!/usr/bin/env python3
"""SkillOpt-style scorer with label isolation.

Modes:
  reflect   - for TRAIN rollouts: prints per-category accuracy AND writes a
              reflection pack (failures with clue/predicted/expected) for the
              optimizer. Golds for train are visible by design.
  aggregate - for VAL/TEST rollouts: prints ONLY per-category and total
              accuracy counts. Never prints golds or per-item details, so
              val/test labels stay out of the optimizer's context.

Usage:
  score_evo.py <predictions.jsonl> --key <key.jsonl> --mode <reflect|aggregate>
               [--questions <q.jsonl>] [--pack <reflection_pack.json>]
"""
import json, argparse, sys
from pathlib import Path

def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("predictions")
    ap.add_argument("--key", required=True)
    ap.add_argument("--mode", choices=["reflect", "aggregate"], required=True)
    ap.add_argument("--questions", default="")
    ap.add_argument("--pack", default="")
    a = ap.parse_args()

    key = {r["id"]: r["expected"] for r in load_jsonl(a.key)}
    preds = {}
    for r in load_jsonl(a.predictions):
        preds[r["id"]] = r.get("answer", "").strip()
    qmap = {r["id"]: r for r in load_jsonl(a.questions)} if a.questions else {}

    per_cat, wrong, exact, fuzzy, missed = {}, [], 0, 0, 0
    for rid, expected in key.items():
        got = preds.get(rid, "")
        cat = rid.split("-")[2]  # evo-{split}-{cat}-{nn}
        s = per_cat.setdefault(cat, {"exact": 0, "total": 0, "fuzzy": 0})
        s["total"] += 1
        if got == expected:
            exact += 1
            s["exact"] += 1
        elif got and (got in expected or expected in got):
            fuzzy += 1
            s["fuzzy"] += 1
            wrong.append(rid)
        elif got:
            wrong.append(rid)
        else:
            missed += 1
            wrong.append(rid)

    total = len(key)
    acc = exact / max(total, 1) * 100
    print(f"=== [{a.mode}] 共 {total} 题，已答 {total - missed}，精确命中 {exact} ({acc:.1f}%)，近似 {fuzzy} ===")
    for cat, s in sorted(per_cat.items()):
        print(f"[{cat}] {s['exact']}/{s['total']} ({s['exact']/max(s['total'],1)*100:.1f}%) 近似 {s['fuzzy']}")

    summary = {"mode": a.mode, "total": total, "exact": exact,
               "accuracy": round(acc, 2), "fuzzy": fuzzy, "missed": missed,
               "per_cat": {k: {"exact": v["exact"], "total": v["total"],
                               "acc": round(v["exact"]/max(v["total"],1)*100, 2)}
                           for k, v in per_cat.items()}}
    print("SUMMARY_JSON:" + json.dumps(summary, ensure_ascii=False))

    if a.mode == "reflect":
        pack = []
        for rid in wrong:
            q = qmap.get(rid, {})
            pack.append({"id": rid, "clue": q.get("clue", ""), "mu": q.get("mu", ""),
                         "predicted": preds.get(rid, ""), "expected": key[rid],
                         "worker_why": ""})
        # attach worker reasoning if present in predictions
        why = {r["id"]: r.get("why", "") for r in load_jsonl(a.predictions)}
        for p in pack:
            p["worker_why"] = why.get(p["id"], "")
        out = a.pack or "reflection_pack.json"
        Path(out).write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"reflection pack: {len(pack)} 条失败样本 -> {out}")
    else:
        print("(aggregate 模式：不输出 gold 与逐题明细，标签保持隔离)")

if __name__ == "__main__":
    sys.exit(main())
