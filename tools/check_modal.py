#!/usr/bin/env python3
"""
修真感打卡 · check_modal.py

根据 CLAUDE.md 第 1.0 节"调性铁律"：每章至少出现 2 项修真元素。

修真感分 5 类，每类匹配关键词正则。
本章命中类目数 ≥ 2 即通过。

用法：
    python3 tools/check_modal.py 06_output/volume_01_qingyu/ch_004.md
"""

import re
import sys
from pathlib import Path

# 5 大修真感类别（命中任一关键词即记该类别为 1）
MODAL_CATEGORIES = {
    "修士御物/差距": [
        r"御剑", r"御物", r"跨步\S{0,5}丈", r"袖[里中口]\S{0,5}光",
        r"灵纹", r"压息", r"灵压", r"灵气波动", r"无一滴水",
        r"瞬息\S{0,3}[出离]", r"踏[空虚云]",
    ],
    "灵气/灵力具象": [
        r"灵力", r"灵气", r"丹田", r"经脉", r"内息", r"真气",
        r"剑[身光][\u4e00-\u9fff]?[嗡鸣]", r"青色?气", r"淡青\S{0,3}[气芒光]",
        r"灵光", r"剑意", r"剑势", r"运功",
    ],
    "法器/灵物": [
        r"法器", r"灵器", r"灵砚", r"灵剑", r"储物袋", r"储物戒",
        r"灵石", r"上品灵石", r"中品灵石", r"下品灵石",
        r"凡品", r"灵品", r"玄品", r"天品",
        r"丹药", r"淬体丹", r"凝气丹",
    ],
    "妖兽/异象": [
        r"妖兽", r"灵兽", r"剑光", r"剑光\S{0,5}掠", r"飞遁",
        r"妖气", r"异象", r"灵雾峰", r"灵峰",
    ],
    "境界/修炼": [
        r"淬体", r"凝气", r"开窍", r"铸魂", r"踏虚", r"法相", r"化神",
        r"境界", r"突破", r"修为", r"修士", r"修炼",
        r"心法", r"功法", r"剑诀", r"剑典",
    ],
}

THRESHOLD = 2  # 至少命中 2 个类别

def check_chapter(text):
    """返回 {类别: [命中词]}"""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    hits = {}
    for category, patterns in MODAL_CATEGORIES.items():
        category_hits = set()
        for p in patterns:
            matches = re.findall(p, text)
            for m in matches:
                category_hits.add(m if isinstance(m, str) else m[0])
        if category_hits:
            hits[category] = sorted(category_hits)[:5]  # 最多展示 5 个
    return hits

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    target = Path(sys.argv[1])
    files = []
    if target.is_dir():
        files = sorted(target.glob("ch_*.md"))
    elif target.is_file():
        files = [target]
    else:
        print(f"路径不存在: {target}")
        sys.exit(1)

    all_passed = True
    for f in files:
        text = f.read_text(encoding="utf-8")
        hits = check_chapter(text)
        cat_count = len(hits)
        passed = cat_count >= THRESHOLD
        status = "✅ PASS" if passed else "❌ FAIL"

        print(f"\n{'='*60}")
        print(f"{status}  {f}")
        print(f"{'='*60}")
        print(f"修真感类别命中: {cat_count}/{len(MODAL_CATEGORIES)}（阈值 ≥ {THRESHOLD}）")
        for cat, ws in hits.items():
            print(f"  ✓ {cat}: {ws}")
        missed = set(MODAL_CATEGORIES.keys()) - set(hits.keys())
        if missed:
            print(f"  未命中: {sorted(missed)}")
        if not passed:
            all_passed = False
            print(f"\n  ⚠️ 调性铁律失败：本章像历史/市井小说，缺修真元素")

    print(f"\n{'='*60}")
    print(f"总计: {len(files)} 文件，{'全部通过 ✅' if all_passed else '有问题 ❌'}")
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
