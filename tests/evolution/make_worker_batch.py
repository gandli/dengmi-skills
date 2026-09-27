#!/usr/bin/env python3
"""Generate frozen-target worker briefs for rollout batches.

Each brief = instructions + skill bundle (or none for no-skill baseline) + one
batch of questions. Workers read the brief file, solve offline, and write
{"id","answer","why"} lines to their assigned predictions file.

Usage:
  make_worker_batch.py --bundle <bundle.md|none> --questions <q.jsonl>
      --batch-size 10 --out <batches/> --tag <run-tag>
"""
import json, argparse
from pathlib import Path

FROZEN_RULES = """## 角色与纪律（frozen target agent）

你是一个**被冻结的解谜 agent**：你的全部解谜知识只能来自下面 <skill> 中的 skill 文本，
不得使用 skill 之外的任何灯谜知识、记忆或"感觉"。

- **严格离线**：不得联网搜索、不得打开浏览器。复刻"离线弱路径"测量口径。
- 对每一题：按 skill 的六步法推理，给出**唯一最终谜底**（字谜=1 个汉字，成语=完整成语），
  不要解释过程以外的废话。
- 输出：**只**输出 JSON Lines，每行一条：
  {"id": "<题号>", "answer": "<最终谜底>", "why": "<一句话推理摘要>"}
  不要输出其他任何文字。谜底前后不加标点空格。
- 若实在解不出，answer 填你认为最可能的一个，不要空着（空着按"未答"计）。
"""

NOSKILL_RULES = """## 角色与纪律（no-skill 基线）

你没有任何灯谜 skill 可用，凭你自己的通用知识直接猜每一题的谜底。

- **严格离线**：不得联网搜索、不得打开浏览器。
- 对每一题给出**唯一最终谜底**（字谜=1 个汉字，成语=完整成语）。
- 输出：**只**输出 JSON Lines，每行一条：
  {"id": "<题号>", "answer": "<最终谜底>", "why": "<一句话推理摘要>"}
  不要输出其他任何文字。解不出也填最可能的一个，不要空着。
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True, help="skill bundle md 路径，或 'none'")
    ap.add_argument("--questions", required=True)
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    qs = [json.loads(l) for l in open(a.questions, encoding="utf-8") if l.strip()]
    bundle = "" if a.bundle == "none" else open(a.bundle, encoding="utf-8").read()
    rules = NOSKILL_RULES if a.bundle == "none" else FROZEN_RULES

    manifest = {"tag": a.tag, "bundle": a.bundle, "batches": []}
    for i in range(0, len(qs), a.batch_size):
        batch = qs[i:i + a.batch_size]
        n = i // a.batch_size
        pred_path = out / f"{a.tag}_pred_{n:02d}.jsonl"
        brief = [
            f"# Rollout brief: {a.tag} / batch {n}",
            f"共 {len(batch)} 题。解完后把结果写入 `{pred_path}`（JSON Lines，每行一条）。",
            rules,
        ]
        if bundle:
            brief += ["<skill>", bundle.rstrip(), "</skill>"]
        brief += ["## 题目"]
        for q in batch:
            brief.append(f"- [{q['id']}] 谜面：{q['clue']}（{q['mu']}）")
        (out / f"{a.tag}_brief_{n:02d}.md").write_text("\n\n".join(brief), encoding="utf-8")
        manifest["batches"].append({"brief": f"{a.tag}_brief_{n:02d}.md",
                                    "pred": str(pred_path), "n": len(batch)})
    (out / f"{a.tag}_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{a.tag}: {len(qs)} 题 -> {len(manifest['batches'])} 个 batch, 输出目录 {out}")

if __name__ == "__main__":
    main()
