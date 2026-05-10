#!/usr/bin/env python3
"""
一键自检 · check_all.py

按顺序跑：
1. check_style.py    风格（字数/句长/禁词/解释句/武侠对白）
2. check_continuity.py 连续性（境界/角色一致/彼岸禁令）
3. check_modal.py    修真感（≥ 2 类）

任意一项失败即整体失败。

用法：
    python3 tools/check_all.py 06_output/volume_01_qingyu/ch_004.md
    python3 tools/check_all.py 06_output/volume_01_qingyu/  # 整目录
"""

import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).parent
SCRIPTS = ["check_style.py", "check_continuity.py", "check_modal.py"]

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = sys.argv[1]
    overall_pass = True
    summary = []

    for script in SCRIPTS:
        print(f"\n{'#'*60}")
        print(f"# 运行 {script}")
        print(f"{'#'*60}")
        r = subprocess.run(
            ["python3", str(TOOLS / script), target],
            capture_output=False
        )
        passed = r.returncode == 0
        summary.append((script, passed))
        if not passed:
            overall_pass = False

    print(f"\n{'='*60}")
    print("# 综合报告")
    print(f"{'='*60}")
    for script, passed in summary:
        flag = "✅" if passed else "❌"
        print(f"  {flag}  {script}")
    print()
    print(f"  整体: {'✅ 全部通过' if overall_pass else '❌ 有问题待处理'}")
    sys.exit(0 if overall_pass else 1)

if __name__ == "__main__":
    main()
