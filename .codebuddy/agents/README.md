# 多 Agent 协作工作流（v2 · 2026-05-09）

> **核心架构**：主 agent 当架构师 + 协调者；writer/reviewer 只管"写"和"审"。
> subagent 不依赖自身工具调用（agentic 模式下工具受限），所有信息由主 agent **预处理后塞进 prompt**。

---

## 角色分工

| 角色 | 谁来做 | 依赖什么 |
|------|--------|----------|
| **架构师**（设计骨架卡） | 主 agent 自己 | 读 beat_sheet / state_tracker / foreshadowing / power_system 等 |
| **执笔人**（写正文） | `novel-writer` subagent | 主 agent 把骨架卡 + 前章末尾 + 风格约束摘要塞进 prompt |
| **审查官**（出审查报告） | `novel-reviewer` subagent | 主 agent 把正文 + 骨架卡 + 约束摘要塞进 prompt |
| **脚本检查**（字数/禁词/境界/修真感） | 主 agent 跑 bash | `python3 tools/check_all.py` |
| **连续性更新** | 主 agent 自己 | state_tracker / foreshadowing / beat_sheet |

---

## 标准工作流（写第 X 章）

### 阶段 1：架构（主 agent 直接做）

主 agent 读全部约束文件 → 产出 `06_output/<vol>/briefs/ch_XXX_brief.md` → 让用户审。

### 阶段 2：执笔（writer subagent）

主 agent 把以下内容**打包进 prompt**交给 writer：
- 骨架卡全文
- 前一章正文（或末尾 2000 字）
- 风格约束摘要（句式/钩子/修真感/人物语言等核心铁律）
- 本章出场角色"自己的语言"摘录

writer 纯输出正文 + Write 一个文件。

### 阶段 3：脚本检查（主 agent）

```bash
python3 tools/check_all.py 06_output/<vol>/ch_XXX.md
```

失败 → 主 agent 自己微调 / 再调 writer 二修。

### 阶段 4：审查（reviewer subagent · 可选）

主 agent 把以下内容**打包进 prompt**交给 reviewer：
- 本章正文全文
- 骨架卡全文
- 核心约束（故事优先三铁则 + 情感六铁律 + 伏笔清单）

reviewer 产出审查报告到 `06_output/<vol>/reviews/ch_XXX_review.md`。

### 阶段 5：连续性更新 + 交付（主 agent）

主 agent 更新 state_tracker / foreshadowing / beat_sheet，汇报给用户。

---

## 为什么 subagent 不自己读文件

codebuddy 的 `agentic` 模式 subagent **工具调用不稳定**（受限沙箱，无 bash，读文件偶尔 0 tool uses）。

**解法**：主 agent 预处理 → 把完整上下文塞进 prompt → subagent 只需"思考 + 写一个文件"。

好处：
- **subagent 永不幻觉**（它看到的就是真实内容，不需要猜）
- **上下文精确控制**（主 agent 决定 writer 看到什么、reviewer 看到什么）
- **保留独立视角价值**（writer 不知道远期规划 / reviewer 独立于 writer）

---

## 目录约定

```
06_output/volume_01_qingyu/
├── ch_001.md              ← 正文
├── ch_002.md
├── briefs/                ← 主 agent 产出的骨架卡
│   ├── ch_005_brief.md
│   └── ...
└── reviews/               ← reviewer 产出的审查报告
    ├── ch_005_review.md
    └── ...
```

---

## 何时不用 subagent

- 修小问题、改一两句话：主 agent 直接做
- 调整设定文件：主 agent 直接做
- 短章节（< 2000 字）：主 agent 自己写可能更快
