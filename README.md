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

测试集与自检脚本在 `tests/`，零依赖：

```bash
python3 tests/run_tests.py
```

`tests/dataset.json` 收录 14 道有公开出处的经典谜（形路/义路/音路·谜格各覆盖，含多字地名与六平山实战题）；脚本按路线判定、三戒（底面不相犯）、推导完整性逐题自检。
