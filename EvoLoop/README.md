# EvoLoop

EvoLoop（Evolution Loop）是 OpenClaw 的核心基础设施技能。它为智能体（Agent）提供了一套**五层标准化工作空间模型**和**自我进化闭环机制**。

当 Agent 在长期运行、多项目穿梭中积累了大量的对话、上下文和经验时，容易因为信息过载或遗忘发生“能力退化”。EvoLoop 解决了智能体“记忆如何存放、规则如何晋升、工作流如何沉淀”的核心痛点，确保 Agent 能**越用越聪明**。

## 🎯 核心解决的问题

1. **工作空间混沌**：提供五层结构（Identity, Operations, Knowledge, Context, Learning），告别杂乱的文件堆砌。
2. **规则无限膨胀**：将“用户随口一次纠正”与“正式长期规则”隔离。只有沉淀成稳定经验的规则，才会晋升为核心指令（`AGENTS.md` / `MEMORY.md`）。
3. **闭门造车**：通过定时的信息流摄入（`daily-info-update`），让智能体不仅能从过去的错误中学习，还能主动摄取外部最佳实践。

## 🏗️ 架构理念

### 五层目录模型

- **Identity 层**: Agent 是谁？边界在哪里？（例：`SOUL.md`）
- **Operations 层**: Agent 如何工作？运行时规则是什么？（例：`AGENTS.md`, `TOOLS.md`）
- **Knowledge 层**: 长期稳定的结构化记忆、事件记录。（例：`MEMORY.md`, `memory/` 目录）
- **Context 层**: 面向项目的资料、共享的事实和深度研究。（例：`context/`, `shared-context/` 目录）
- **Learning 层**: 进化候车室。存放实时错误、待晋升的候选规则。（例：`.learnings/ERRORS.md`, `pending/rules.json`）

### 双通道进化机制

1. **实时纠正记录**：当人类用户当场指出错误时，Agent 会立即将经验写入 `.learnings/ERRORS.md`。
2. **异步审核晋升 (Cron 驱动)**：所有潜在的新经验和规则，必须先进入 `pending/rules.json` 队列，每天深夜由 Agent 自己进行复盘和审核（`daily-review`），符合标准的才正式编入核心架构。

## 🚀 安装部署

### 1. 挂载技能

将本地的 EvoLoop 技能链接到你的 OpenClaw 环境（或者以远程方式安装）：

```bash
openclaw skill install local:/path/to/openclaw-skills/EvoLoop
```

### 2. 触发 Agent 建制

在一个新的智能体会话中，输入以下自然语言指令：

> "请使用 EvoLoop 技能，对当前工作空间进行初始化建制。"

此时，Agent 会：
1. 调用 `bootstrap.py init` 脚本为你创建标准的五层目录结构和最小文件骨架。
2. **自动接管原有的 `AGENTS.md`**：在保留你原本人设的基础上，注入 EvoLoop 的底层运行规则（比如检索顺序、写入边界、候选规则等）。确保即使后续卸载本技能，已经注入在 AGENTS.md 里的习惯也能维持运转。

---

## ⚙️ 自动化配置 (Cron)

要启用完整的“闭环进化”，必须创建两个定时的 Cron 任务。**极其建议**通过 Agent 在会话中自动配置，你也可以使用命令手动下发：

### 任务一：`daily-info-update`（每日信息更新）

每晚 22:00（按需调整）调度。它会阅读你配置在 `.learnings/pending/info-sources.json` 里的自然语言指令（如：“阅读 GitHub 某最新 Release”），总结后变为候选规则写入 `pending/rules.json`。每日新规则产生不超过 3 条。

### 任务二：`daily-review`（每日复盘审核）

每晚 23:00（一定要晚于 Update）调度。它是候选规则的**唯一晋升闸门**。
它会：清理过期规则 -> 回溯今天对话的遗漏错误 -> 审核 Pending 队列 -> 将优秀的规则真正写入 `AGENTS.md` 或 `MEMORY.md` -> 最后写下一份当日进化摘要。

## 📂 进阶阅读（面向人类和 Agent）
深入了解各机制的强制约束，可阅读 `references/` 目录：
1. [`model-and-boundaries.md`](references/model-and-boundaries.md)：五层模型的严格定义和反模式。
2. [`self-evolution.md`](references/self-evolution.md)：详细阐明 Cron 闭环、Pending 审阅机制以及信息源 (info-sources) 的配置。
3. [`scenarios-and-retrieval.md`](references/scenarios-and-retrieval.md)：典型场景下的检索及存放指南。
