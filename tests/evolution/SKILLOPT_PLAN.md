# 灯谜 Skill 的 SkillOpt 式进化：可实施方案

> 状态：方案已定稿并在本 PR 落地为可运行脚本；基线测量（no-skill / v1.5.0）
> 正在进行中，进化循环待基线完成后启动。
> 本文档是执行手册，不是结果报告——结果（`best_skill.md`、v1.6.0）走后续 PR。

## 一、背景与目标

仓库历史测量（见 `tests/TESTREPORT.md`）：v1.2.0 离线基线 16.2%，
后续"规则写得更多"反而掉到 12.5%，v1.5.0 在多段成语专项上到 25%。
教训：**凭感觉加规则不可靠，必须用"轨迹驱动、有门控"的进化代替拍脑袋改 Skill**。

本方案借鉴 [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) 的核心思想：

- **Skill 文档即模型可训练状态**：优化对象是 `SKILL.md` 文本本身，不是权重。
- **闭环**：rollout（用当前 skill 解一批题，记录轨迹）→ reflect（在 train
  失败上反思，聚类失败模式）→ 有界编辑（每轮 ≤4 个 add/delete/replace 编辑）
  → validation gate（候选 skill 在 held-out val 上重跑，**严格涨分才接受**，
  否则进 rejected-edit buffer）。
- **产物**：通过门控的最终 `best_skill.md`（通常 300–2000 tokens），只收录
  被验证过的编辑。

**成功标准**：在 held-out test 上相对 v1.5.0 严格涨分（目标约 +10pp）；
任何未过门控的编辑不得进入最终 Skill。

## 二、三集定位与隔离铁律（勿混用）

| 切分 | 规模 | 用途 | 标签可见性 |
|---|---|---|---|
| train | 100（字谜/成语各 50） | rollout + reflect：生成失败反思包，指导编辑 | 可见（by design） |
| val | 60（各 30） | 验证门控：候选 skill 重跑，只有严格涨分才接受 | 不可见，只看聚合分数 |
| test | 60（各 30） | 最终一次性评测：best vs v1.5.0 | 不可见，只看聚合分数 |

生成规则（`make_evo_splits.py`，seed=`20260928`，确定性）：

1. 来源 `tests/corpus/dengmi_corpus.json`，清洗规则与 `tests/make_benchmark.py` 一致
   （三戒底面不相犯、去样板污染、谜底长度约束：字谜 1 字、成语 ≤8 字）。
2. **排除 tests/ 下所有历史测试用过的 299 条谜面**（benchmark、offline、holdout、
   crosscheck 等），跨 split 再去重。
3. 题面 `*_q.jsonl`（id/clue/谜目）与答案键 `*_key.jsonl`（id/expected）分离存放；
   `manifest.json` 记录 seed 与生成时的仓库 commit。

**铁律**：

- worker 只见题面 + skill 文本，**永远见不到答案键**。
- val/test 评分一律 `--mode aggregate`：只输出"精确命中 X/Y (Z%)"聚合数字，
  不输出 gold、不输出逐题明细。
- train 评分用 `--mode reflect`：输出失败包（含谜面/预测/答案/worker 推理摘要），
  供优化器聚类。
- 不用 test 的任何信息指导编辑；test 的聚合基线只跑一次、只用于最终对照。

## 三、执行步骤（按顺序跑）

### 步骤 0：生成切分（已做完，一般不重跑）

```bash
python3 tests/evolution/make_evo_splits.py
# 输出 tests/evolution/splits/；重跑应与已提交文件字节一致（确定性校验）
```

### 步骤 1：基线 rollout（frozen worker，严格离线）

```bash
# no-skill 基线（val）：测"裸模型"水平
python3 tests/evolution/make_worker_batch.py --bundle none \
  --questions tests/evolution/splits/evo_val_q.jsonl \
  --batch-size 10 --out batches/noskill_val --tag noskill_val

# v1.5.0 基线（train/val/test）：worker 被"冻结"，只能用 skill 文本内的知识解谜
python3 tests/evolution/make_worker_batch.py --bundle skills/dengmi-basics/SKILL.md \
  --questions tests/evolution/splits/evo_train_q.jsonl \
  --batch-size 10 --out batches/v150_train --tag v150_train
# val / test 同理（tag 换成 v150_val / v150_test）
```

worker 纪律（已写入每份简报）：不得联网；每题输出唯一谜底；
只写 JSON Lines：`{"id":"...","answer":"...","why":"一句话推理摘要"}`；
解不出也填最可能的一个（空着按"未答"计）。

### 步骤 2：评分

```bash
# 合并各 batch 的 pred 文件后：
python3 tests/evolution/score_evo.py batches/v150_train_pred.jsonl \
  --key tests/evolution/splits/evo_train_key.jsonl \
  --questions tests/evolution/splits/evo_train_q.jsonl \
  --mode reflect --pack reflection_pack.json   # train：拿失败包

python3 tests/evolution/score_evo.py batches/v150_val_pred.jsonl \
  --key tests/evolution/splits/evo_val_key.jsonl \
  --mode aggregate                            # val/test：只看聚合
```

### 步骤 3：进化循环（最多 4 个 epoch，每轮如下）

1. **reflect**：读 `reflection_pack.json`，把失败按原因聚类
   （如：部件字典缺字、操作词误判、多段结构切分错、义路典故缺失……）。
2. **propose**：针对最大的一两个失败簇，提 **≤4 个**有界编辑
   （add / delete / replace，注明改哪一段、为什么）。
3. **candidate**：把编辑应用到当前 skill，生成候选 skill 文本。
4. **gate**：用候选 skill 在 **val** 上完整重跑（步骤 1+2，`aggregate` 模式）。
   - val 准确率**严格高于**当前 skill → 接受，进入下一轮；
   - 否则 → 拒绝，编辑记入 rejected-edit buffer（注明 val 分数与失败原因），
     skill 回滚。
5. 每轮记录：编辑内容、val 前后分数、接受/拒绝。

### 步骤 4：最终评测与产物

1. 取最后一轮通过门控的 skill，整理为 `best_skill.md`。
2. 在 **test** 上跑一次最终对照：no-skill / v1.5.0 / best（`aggregate` 模式，
   只记录聚合分数，不看明细，不再调参）。
3. 产出：`best_skill.md`、每轮编辑与门控记录、三者对照表、
   局限与置信度说明。
4. 回写仓库：只有被验证过的编辑并入 `skills/dengmi-basics/SKILL.md`
  （升版 v1.6.0），`tests/TESTREPORT.md` 追加第五轮记录；走独立 PR。

## 四、局限与诚实声明

1. **同源切分，非异源泛化**：train/val/test 仍来自同一语料库
   （`dengmi_corpus.json`，汉辞网），只是做了历史去重与标签隔离。
   按 `tests/TESTREPORT.md` 的铁律，这不能证明跨源泛化——报告中必须称为
   "同源隔离切分"，不得夸大。条件允许时应另建异源 final test。
2. **test 复用**：v1.5.0 的 test 基线在方案执行中已被评分一次，最终对照会再评一次。
   缓解：只保留聚合基线、从不看 test 明细、不用 test 指导编辑。
3. **worker 即评测者**：rollout 用 LLM worker 模拟"读 skill 解谜的人"，
   测的是 skill 文本的指导效力，不是某个固定模型的绝对能力。
   跨轮比较时保持 worker 配置一致，结论只在"相对涨分"上成立。

## 五、当前进度（2026-09-28）

- [x] 基础设施：切分脚本、隔离评分器、worker 简报模板（本 PR）
- [x] 切分生成：train 100 / val 60 / test 60，确定性校验通过
- [ ] 基线 rollout：28 个 batch 已派出（no-skill val / v1.5.0 train,val,test），收集中
- [ ] 进化循环（≤4 epochs）
- [ ] 最终 test 评测与 `best_skill.md`
- [ ] v1.6.0 回写（独立 PR）
