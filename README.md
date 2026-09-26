# 灯谜 Agent Skills (Dengmi Skills)

Chinese lantern riddle (灯谜/文虎) agent skills collection.

## Skills

- **dengmi-basics** — 灯谜通解：三要素（谜面/谜目/谜底）、三戒（底面相犯/闲字/无别解）、六步解谜法（缩圈→判路→分段→拆解→回查→验证）、形路/义路/音路判定信号、15种制谜方法、7大经典谜格；附：笔画部件表、借代词库、操作词表、多类典型实战复盘案例。
  - SKILL.md：通用方法论主文件
  - `references/cheatsheet.md`：笔画象形、方位五行、天干地支、借代词库、操作词全表
  - `examples/solved-cases.md`：形路单字、形路地名、义路地名四类完整复盘 + 可复用模板

## Install

```bash
npx skills add gandli/dengmi-skills
```

## Usage

猜谜时直接调取本 skill；解题流程严格走六步，每步都有校验点。  
遇到形路疑点：先查 `references/cheatsheet.md` 的操作词与象形表。  
遇到验证困难：查 `examples/solved-cases.md` 里对应类型的复盘模板。

## Tests

零依赖，四层测试：

```bash
python3 tests/lint_corpus.py    # ① 语料质检：7980 条 harvested 语料硬伤扫描
python3 tests/run_tests.py      # ② 金标 lint：14 道经典谜，路线/三戒/推导完整性
python3 tests/make_benchmark.py # ③ 生成 80 题盲测集（无答案）+ 答案键
python3 tests/score.py          # ④ 盲测评分：读 predictions.jsonl 出命中率
```

- `tests/corpus/dengmi_corpus.json` — 字谜 3863 + 成语谜 4117（来源：汉辞网）
- `tests/dataset.json` — 14 道金标（形/义/音路 + 梨花/卷帘格 + 多字地名）
- `tests/benchmark.jsonl` / `tests/answers.jsonl` — 盲测题面 / 答案键
- `tests/TESTREPORT.md` — 质检结果 + 盲测基线（16.2%）+ 4 个能力缺口 + 留出集设计铁律
- `tests/crosscheck.json` — 7 条异源双路验证谜（抓取答案 = 独立拆字推导）
- `tests/holdout_b.jsonl` — ⚠️ 同源留出，仅供"检索先行"回归，非泛化评测

当前盲测基线：字谜 20.0% / 成语谜 12.5% / 合计 16.2%（详见 TESTREPORT）。
