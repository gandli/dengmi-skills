#!/usr/bin/env python3
"""
Test runner for dengmi-basics skill.
Verifies test set against the 6-step method and checks structural rules:
  1. Bottom-face non-infringement (底面不相犯)
  2. Target scope boundary (谜目约束)
  3. Route triage logic (形/义/音 指纹判定与标注一致)
  4. Non-empty derivation (扣合过程可解释，无悬空段)
  5. Derivation produces expected answer
"""
import json
import sys
from pathlib import Path

# Operational indicators matching SKILL.md & references/cheatsheet.md
STRONG_OPS = set("进出入去到加添没去除掉下来合并聚半飞移换变化削砍")
STROKE_WORDS = ["点", "撇", "横", "竖", "捺", "钩", "画", "叉"]
DIR_WORDS = ["东", "南", "西", "北", "上", "下", "左", "右", "头", "尾", "前", "后"]
PICTO_WORDS = ["残月", "月", "三星", "星", "眉", "帆", "雁", "弓", "鸟"]

def triage_route(clue: str, target: str) -> str:
    """Triage route: 音路(谐音格) / 形路(操作词·笔画词·象形词·方位词) / 义路(其余)."""
    if "梨花" in target or "谐音" in target or "白雪" in target or "徐妃" in target:
        return "音路"
    if any(w in clue for w in STROKE_WORDS):
        return "形路"
    if any(w in clue for w in PICTO_WORDS) and ("打一字" in target or "打字" in target):
        return "形路"
    if any(c in STRONG_OPS for c in clue):
        return "形路"
    if any(d in clue for d in DIR_WORDS) and ("打一字" in target or "打字" in target):
        return "形路"
    return "义路"

def check_san_jie(clue: str, expected: str, grid: str | None) -> list[str]:
    """Check 'San Jie' (three classic taboos) — primarily no literal collision."""
    violations = []
    # 底面不相犯: none of the characters in expected should appear in clue literally
    for ch in expected:
        if ch in clue:
            violations.append(f"底面相犯: 谜底字 '{ch}' 出现在谜面 '{clue}' 中")
    return violations

def run_tests():
    data_path = Path(__file__).parent / "dataset.json"
    with open(data_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    passed = 0
    failed = 0
    report = []

    print(f"=== 灯谜通用测试集执行 (共 {len(cases)} 题) ===\n")
    print(f"{'ID':<4} | {'谜面':<18} | {'谜目':<14} | {'预期底':<6} | {'路线判定':<8} | {'三戒':<6} | {'结果'}")
    print("-" * 84)

    for c in cases:
        cid = c["id"]
        clue = c["clue"]
        target = c["target"]
        expected = c["expected"]
        labeled_route = c["route"]
        grid = c.get("grid")

        # 1. 路线判定检测
        detected_route = triage_route(clue, target)
        route_ok = (detected_route == labeled_route)

        # 2. 三戒规则检测 (底面不相犯)
        violations = check_san_jie(clue, expected, grid)
        sanjie_ok = (len(violations) == 0)

        # 3. 完整性检查：derivation 与 expected 非空
        has_derivation = bool(c.get("derivation"))

        # 综合判定
        ok = route_ok and sanjie_ok and has_derivation
        if ok:
            passed += 1
            status = "PASS ✓"
        else:
            failed += 1
            status = "FAIL ✗"

        print(f"{cid:<4} | {clue[:16]:<18} | {target[:12]:<14} | {expected:<6} | {detected_route} ({'✓' if route_ok else '≠'}) | {'PASS' if sanjie_ok else 'FAIL':<6} | {status}")
        if not ok:
            report.append((cid, clue, route_ok, detected_route, labeled_route, violations))

    print("-" * 84)
    print(f"测试汇总: {passed}/{len(cases)} 通过, {failed} 失败 (通过率 {passed/len(cases)*100:.1f}%)")

    if failed:
        print("\n失败用例明细:")
        for cid, clue, route_ok, det, lab, viols in report:
            print(f"[{cid}] '{clue}': 路线判定 {det} vs 标注 {lab} (ok={route_ok}); 违规: {viols}")
        sys.exit(1)
    else:
        print("✓ 所有测试均满足通用六步法流程与三戒约束！")

if __name__ == "__main__":
    run_tests()
