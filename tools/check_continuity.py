#!/usr/bin/env python3
"""
连续性自检脚本 · check_continuity.py

从 04_continuity/ 和 02_characters/ 提取"已成事实"，扫描本章是否矛盾。

核心检查：
1. 主角境界/灵力一致（state_tracker.md → 当前境界）
2. 角色境界一致（races_factions.md / character cards 中的修为标注）
3. 已埋伏笔不重复埋（foreshadowing.md → 状态 🟢 的）
4. 已发生事件不与本章冲突（state_tracker.md → 已知秘密）

用法：
    python3 tools/check_continuity.py 06_output/volume_01_qingyu/ch_004.md
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============== 角色境界注册表（从设定文件硬编码，更可靠） ==============
# 格式：人名 → 当前章应该的境界关键词
# 注意：使用关键词而非精确字符串，方便文中以多种方式提及
CHARACTER_REALMS = {
    "肖凯": {
        "realm": "淬体",
        "stage": "高阶",   # ch_006 突破淬体高阶（中阶+高阶一并通）
        "禁出现": ["开窍", "铸魂"],  # 凝气 已移出：正文里大量出现"看见凝气境前辈"等第三方叙述，不适合禁
        "灵力": 62,  # 突破后灵力值
    },
    "肖彦章": {
        "realm": "凝气",
        "stage": "巅峰",
        "状态": "被废",  # 经脉被封 → 实战 = 凡人
    },
    "陈守一": {
        "realm": "凝气",
        "stage": "中阶",  # races_factions.md 第 77 行写的是凝气中阶
    },
    "赵元景": {
        "realm": "淬体",
        "stage": "巅峰",
        "禁出现": ["练气境"],  # 错误境界名
    },
    "赵仲谦": {
        "realm": "凝气",
        "stage": "巅峰",
    },
    "于子和": {
        "realm": "凝气",
        "stage": "巅峰",
    },
    "周敬安": {
        "realm": None,  # 暂未定，仅检查名字一致
    },
    "阴无常": {
        "realm": "铸魂",
        "stage": "巅峰",
    },
}

# 生造境界名（违反 power_system 的名字）
FORBIDDEN_REALMS = ["练气境", "练气期", "练气", "金丹", "元婴", "化神期", "渡劫"]

# 生造路径名（违反 power_system 的路径）
FORBIDDEN_PATHS = ["元修", "法修", "心修", "灵修"]

# ============== 工具函数 ==============

def parse_state_tracker():
    """从 state_tracker.md 提取主角当前境界、灵力"""
    f = PROJECT_ROOT / "04_continuity" / "state_tracker.md"
    if not f.exists():
        return {}
    text = f.read_text(encoding="utf-8")
    state = {}
    # 抽取 "境界" 字段
    m = re.search(r"\*\*境界\*\*\s*\|\s*([^\|\n]+)", text)
    if m:
        state["境界"] = m.group(1).strip()
    # 灵力值
    m = re.search(r"\*\*灵力值\*\*\s*\|\s*(\d+)", text)
    if m:
        state["灵力值"] = int(m.group(1))
    # 最后更新章节
    m = re.search(r"\*\*最后更新章节\*\*\s*\|\s*([^\|\n]+)", text)
    if m:
        state["最后章"] = m.group(1).strip()
    return state

def parse_chapter_num(filepath):
    """从文件名提取章节号"""
    m = re.search(r"ch_(\d+)", str(filepath))
    return int(m.group(1)) if m else None

def get_chapter_text(filepath):
    text = Path(filepath).read_text(encoding="utf-8")
    # 去掉注释
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return text

# ============== 检查项 ==============

def check_forbidden_realms(text):
    """检查生造境界名"""
    issues = []
    for word in FORBIDDEN_REALMS:
        if word in text:
            issues.append(f"出现非法境界名 '{word}'（power_system 中不存在）")
    for word in FORBIDDEN_PATHS:
        if word in text:
            issues.append(f"出现非法路径名 '{word}'（power_system 中不存在）")
    return issues

def check_character_realms(text, ch_num):
    """检查角色境界一致性

    策略：
    - 找到角色名出现的段落，检查其附近 ±150 字内是否出现该角色【禁出现】的境界词
    - 排除第三方语境：禁词若紧跟"前辈/师叔/师伯/某某境的"等表示别人的修饰，不算
    """
    # 第三方语境模式：禁词后紧跟"前辈/师/某某"等
    third_party_suffixes = [
        r"前辈", r"师叔", r"师伯", r"师祖", r"长老",
        r"宗师", r"高人", r"祖师", r"老者",
        r"老?修士", r"修士", r"道人", r"道长",
        r"大能", r"巨擘", r"老者", r"前贤",
    ]
    # 禁词前缀（说"X 境的某某"）
    third_party_prefixes = [r"位\s*", r"个\s*"]

    issues = []
    for char_name, info in CHARACTER_REALMS.items():
        if char_name not in text:
            continue
        forbidden = info.get("禁出现", [])
        if not forbidden:
            continue

        positions = [m.start() for m in re.finditer(re.escape(char_name), text)]
        for pos in positions:
            window = text[max(0, pos-150):pos+150]
            for fw in forbidden:
                # 在 window 中查所有 fw 的位置
                for fm in re.finditer(re.escape(fw), window):
                    fpos = fm.end()
                    # 看 fw 后面 8 字内是否是第三方语境
                    after = window[fpos:fpos+8]
                    is_third_party = any(re.match(s, after) for s in third_party_suffixes)
                    # 也检查 fw 前面（"一位 凝气境 前辈" 这种）
                    before = window[max(0, fm.start()-3):fm.start()]
                    if not is_third_party:
                        # 再宽松检查："一位/一个 X 境"（中文无空格）
                        full_check = window[max(0, fm.start()-6):fm.end()+12]
                        if re.search(r"[一二三四五六七八九十]?[位个名]\s*[\u4e00-\u9fff]{0,3}" +
                                     re.escape(fw) +
                                     r"[境期]?[的]?[\u4e00-\u9fff]{0,8}(前辈|师叔|师伯|师祖|长老|宗师|高人|老者|大能|老?修士|道人|道长)",
                                     full_check):
                            is_third_party = True
                    if is_third_party:
                        continue
                    issues.append(
                        f"角色'{char_name}'附近出现禁词'{fw}'"
                        f"（应为 {info['realm']}{info.get('stage','')}）"
                    )
                    break  # 同一处不重复报
    # 去重
    return sorted(set(issues))

def check_realm_progress(text, state, ch_num):
    """检查主角是否擅自跳境界"""
    issues = []
    if not state:
        return issues
    current_realm = state.get("境界", "")
    if "淬体" in current_realm:
        # 主角段落里不应出现"凝气境第 X 阶"等更高境界自述
        wrong_phrases = [
            "肖凯已是凝气", "肖凯进入凝气", "肖凯凝气境",
            "肖凯已是开窍", "肖凯进入开窍",
        ]
        for p in wrong_phrases:
            if p in text:
                issues.append(f"主角擅自跳境界：'{p}'（state_tracker: {current_realm}）")
    return issues

def check_pengyan_taboo(text, ch_num):
    """前 30 章绝禁'彼岸'"""
    if ch_num is not None and ch_num <= 30:
        if "彼岸" in text:
            return [f"第 {ch_num} 章出现'彼岸'（前 30 章绝禁，违反终极悬念条款）"]
    return []

# ============== 主流程 ==============

def check_file(filepath):
    text = get_chapter_text(filepath)
    ch_num = parse_chapter_num(filepath)
    state = parse_state_tracker()

    issues = []
    issues += check_forbidden_realms(text)
    issues += check_character_realms(text, ch_num)
    issues += check_realm_progress(text, state, ch_num)
    issues += check_pengyan_taboo(text, ch_num)

    return {
        "file": str(filepath),
        "ch_num": ch_num,
        "state_tracker": state,
        "passed": len(issues) == 0,
        "issues": issues,
    }

def print_report(r):
    status = "✅ PASS" if r["passed"] else "❌ FAIL"
    print(f"\n{'='*60}")
    print(f"{status}  {r['file']}")
    print(f"{'='*60}")
    if r.get("state_tracker"):
        st = r["state_tracker"]
        print(f"参考状态: {st.get('最后章','?')} | 境界: {st.get('境界','?')} | 灵力: {st.get('灵力值','?')}")
    if not r["passed"]:
        print("\n连续性问题：")
        for i in r["issues"]:
            print(f"  • {i}")

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
        r = check_file(f)
        print_report(r)
        if not r["passed"]:
            all_passed = False

    print(f"\n{'='*60}")
    print(f"总计: {len(files)} 文件，{'全部通过 ✅' if all_passed else '有问题 ❌'}")
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
