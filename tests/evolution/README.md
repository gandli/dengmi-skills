# tests/evolution — SkillOpt 式进化闭环

用 Microsoft SkillOpt 方法论（rollout → reflect → 有界编辑 → 验证门控）
持续进化 `skills/dengmi-basics/SKILL.md` 的可实施方案与配套脚本。

- **`SKILLOPT_PLAN.md`** — 完整可实施方案（方法论、三集隔离铁律、每步操作命令、门控规则）。先读这份。
- **`make_evo_splits.py`** — 生成 train/val/test 切分（确定性：seed 固定，同 commit 下字节一致）。
- **`make_worker_batch.py`** — 生成 frozen worker 的 rollout 简报（含 skill 包或无 skill 基线）。
- **`score_evo.py`** — 隔离评分器：`reflect`（train，输出失败包）/ `aggregate`（val/test，只输出聚合分数）。
- **`splits/`** — 已生成的切分：train 100 题 / val 60 题 / test 60 题（题面与答案键分离）。

## 快速开始

```bash
# 1. 生成切分（已生成好，一般不需要重跑；重跑结果应与 splits/ 字节一致）
python3 tests/evolution/make_evo_splits.py

# 2. 生成一批 rollout 简报（示例：v1.5.0 在 val 上，每批 10 题）
python3 tests/evolution/make_worker_batch.py \
  --bundle skills/dengmi-basics/SKILL.md \
  --questions tests/evolution/splits/evo_val_q.jsonl \
  --batch-size 10 --out /tmp/batches --tag v150_val

# 3. worker 按简报离线解谜，写出 {"id","answer","why"} 的 predictions jsonl 后，评分
python3 tests/evolution/score_evo.py /tmp/batches/v150_val_pred.jsonl \
  --key tests/evolution/splits/evo_val_key.jsonl --mode aggregate
```

**铁律**：`splits/*_key.jsonl` 只给评分器，绝不进入 worker 上下文；
val/test 一律用 `aggregate` 模式，只看聚合分数，不看逐题 gold。
详见 `SKILLOPT_PLAN.md`。
