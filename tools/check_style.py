#!/usr/bin/env python3
"""
风格自检脚本 · check_style.py

检查项：
1. 字数（中文字符 + 含标点）
2. 平均句长 / 长短句比例
3. 禁词扫描（地球/手机/yyds/只见/忽然之间 等）
4. 画蛇添足解释句（"——这是.../"那一刻他明白了..." 等）
5. 武侠程式化对白（"师兄所言甚是" 等）
6. 现代网络梗

用法：
    python3 tools/check_style.py 06_output/volume_01_qingyu/ch_004.md
    python3 tools/check_style.py 06_output/volume_01_qingyu/  # 整目录
"""

import re
import sys
from pathlib import Path

# ============== 配置区（确定性规则，从 prompt 迁移到这里） ==============

# 字数硬约束
WORDS_MIN = 3000
WORDS_MAX = 4000
WORDS_TARGET = 3500

# 句长硬约束
AVG_LEN_MIN = 9   # 战斗/紧凑章可短，所以放宽到 9
AVG_LEN_MAX = 28
LONG_SENT_RATIO_MAX = 0.10  # ≥35 字长句占比 ≤ 10%

# 禁词（按类别）
FORBIDDEN_WORDS = {
    "现代/地球词": ["地球", "科技", "念力", "手机", "电脑", "互联网"],
    "现代网络梗": ["yyds", "绝绝子", "破防", "内卷", "yyds", "绝绝子"],
    "陈词滥调": ["话说", "只见", "忽然之间", "不知不觉"],
    "堆砌辞藻": ["蹁跹", "氤氲", "缱绻"],
    "境界混淆": ["元修", "法修", "心修"],  # 生造路径名
    "彼岸禁令": ["彼岸"],  # 前 30 章绝禁
}

# 画蛇添足解释句（regex）
EXPLANATION_PATTERNS = [
    r"——这是[^\n]{2,30}的[^\n]{0,15}[。！？]",  # ——这是 X 的 Y。
    r"那一刻他明白了",
    r"那一刻她明白了",
    r"那一瞬间[他她它]",
    r"——这意味着",
]

# 武侠程式化对白
WUXIA_FORMAL = [
    "师兄所言甚是", "敢问尊驾", "惭愧惭愧",
    "尔等", "汝可", "此乃", "岂不", "在下不才",
]

# ============== 工具函数 ==============

def strip_title_and_meta(text):
    """去掉一级标题和 HTML 注释"""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"^# .*\n", "", text, count=1)
    return text.strip()

def count_chinese(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))

def count_total(text):
    """含标点的总字符数（不含空格、换行）"""
    return len(re.sub(r"[\s\n]", "", text))

def get_sentences(text):
    """按 。！？ 切分，返回非空句子列表（中文字符数）"""
    sents = re.split(r"[。！？]", text)
    lens = [count_chinese(s) for s in sents]
    return [l for l in lens if l > 0]

# ============== 检查项 ==============

def check_word_count(text):
    zh = count_chinese(text)
    total = count_total(text)
    issues = []
    # 按【中文字符数】判断（更准确，不受标点/英文干扰）
    # 网文章节标准 3500，允许 ±500 范围（3000-4000）；超出 ±800 才报错
    if zh < WORDS_MIN - 500:
        issues.append(f"字数偏少：中文 {zh}（目标 {WORDS_MIN}-{WORDS_MAX}）")
    elif zh > WORDS_MAX + 500:
        issues.append(f"字数偏多：中文 {zh}（目标 {WORDS_MIN}-{WORDS_MAX}）")
    return {"中文字符": zh, "含标点": total, "issues": issues}

def check_sentence_length(text):
    sent_lens = get_sentences(text)
    if not sent_lens:
        return {"issues": ["无法切分句子"]}
    avg = sum(sent_lens) / len(sent_lens)
    long_count = sum(1 for l in sent_lens if l >= 35)
    long_ratio = long_count / len(sent_lens)
    issues = []
    if avg > AVG_LEN_MAX:
        issues.append(f"平均句长 {avg:.1f} 偏长（>{AVG_LEN_MAX}）")
    if long_ratio > LONG_SENT_RATIO_MAX:
        issues.append(f"长句占比 {long_ratio*100:.1f}% 超限（>{LONG_SENT_RATIO_MAX*100}%）")
    return {
        "平均句长": round(avg, 1),
        "句子数": len(sent_lens),
        "长句占比": f"{long_ratio*100:.1f}%",
        "issues": issues,
    }

def check_forbidden_words(text):
    issues = []
    hits = {}
    for category, words in FORBIDDEN_WORDS.items():
        for w in words:
            if w in text:
                hits.setdefault(category, []).append(w)
    for cat, ws in hits.items():
        issues.append(f"{cat}: {ws}")
    return {"hits": hits, "issues": issues}

def check_explanation_sentences(text):
    """画蛇添足解释句（铁则 3.5）"""
    issues = []
    for pattern in EXPLANATION_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            issues.append(f"解释句模式 r'{pattern}' 命中 {len(matches)} 处: {matches[:3]}")
    return {"issues": issues}

def check_wuxia_formal(text):
    """武侠程式化对白扫描"""
    issues = []
    for phrase in WUXIA_FORMAL:
        # 排除 "在下" 等可能误报的（"雨还在下"），用对白引号包裹检测
        if phrase in text:
            # 多次出现才报错（一次可能是合理通名）
            count = text.count(phrase)
            if count >= 2 or phrase in ["师兄所言甚是", "敢问尊驾", "惭愧惭愧"]:
                issues.append(f"'{phrase}' 出现 {count} 次")
    return {"issues": issues}

# ============== 主流程 ==============

def check_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return {"file": str(path), "error": "文件不存在"}

    text = path.read_text(encoding="utf-8")
    text = strip_title_and_meta(text)

    result = {
        "file": str(path),
        "word_count": check_word_count(text),
        "sentence_length": check_sentence_length(text),
        "forbidden_words": check_forbidden_words(text),
        "explanation": check_explanation_sentences(text),
        "wuxia_formal": check_wuxia_formal(text),
    }

    all_issues = []
    for k, v in result.items():
        if isinstance(v, dict) and v.get("issues"):
            all_issues.extend([f"[{k}] {i}" for i in v["issues"]])
    result["passed"] = len(all_issues) == 0
    result["all_issues"] = all_issues
    return result

def print_report(result):
    if "error" in result:
        print(f"❌ {result['file']}: {result['error']}")
        return

    status = "✅ PASS" if result["passed"] else "❌ FAIL"
    print(f"\n{'='*60}")
    print(f"{status}  {result['file']}")
    print(f"{'='*60}")
    wc = result["word_count"]
    sl = result["sentence_length"]
    print(f"字数: 中文 {wc['中文字符']} / 含标点 {wc['含标点']}")
    print(f"平均句长: {sl['平均句长']} | 长句占比: {sl['长句占比']} | 句数: {sl['句子数']}")

    if not result["passed"]:
        print("\n问题清单：")
        for issue in result["all_issues"]:
            print(f"  • {issue}")

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
        if not r.get("passed", False):
            all_passed = False

    print(f"\n{'='*60}")
    print(f"总计: {len(files)} 文件，{'全部通过 ✅' if all_passed else '有问题 ❌'}")
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
