---
name: EvoLoop
description: Initialize, organize, and operate a five-layer workspace with a self-evolution loop for AI agents. Covers workspace setup, file placement, retrieval order, AGENTS.md takeover, and the pending-rules lifecycle via daily-info-update and daily-review cron jobs.
---

# EvoLoop

用这份技能来理解、建立并运行一套面向智能体自我反思和学习的 workspace 分层体系。

## 安装后使用

首次使用时，先执行初始化命令创建最小目录骨架：

```
python3 ~/.openclaw/skills/EvoLoop/scripts/bootstrap.py init <workspace-root>
```

如需先预览而不实际写入：

```
python3 ~/.openclaw/skills/EvoLoop/scripts/bootstrap.py init <workspace-root> --dry-run
```

检查接管状态与自我进化骨架：

```
python3 ~/.openclaw/skills/EvoLoop/scripts/bootstrap.py check <workspace-root>
```

需要更细 guidance 时，按需读取 references（见底部导航索引）。

## 执行硬规则

- 先确认当前 agent 的 workspace 根路径，再在该 workspace 内执行初始化、读取与写入
- 首次接管 workspace 时，先检查最小目录骨架；缺失时优先使用 `bootstrap.py init` 创建最小可用结构
- daily memory 必须先读今天对应的 `memory/YYYY-MM-DD.md`，再读昨天的；文件不存在必须明确说明，不要假装已读取，不要用 `当天.md`、`today.md` 等虚假文件名
- 有 Git 就提交；无 Git 时，不要把 commit 当阻塞
- 用户当场纠正触发的实时学习可直接写既有学习与记忆通道
- 定时任务发现的候选规则，必须先进入 `.learnings/pending/rules.json`，未经审核不得直接写入核心规则文件
- 初始化时只创建最小骨架，不预填虚假内容，不批量空造无用文件
- 首次建制完成后，必须检查并更新当前 workspace 的 `AGENTS.md`，让运行层接住新架构
- 更新 `AGENTS.md` 前，必须先备份原文件，再修改
- 启用自我进化机制时，必须检查 `daily-info-update` 与 `daily-review` 两个 cron 任务是否存在并绑定到当前智能体自己；不存在则创建，存在则核对配置
- 执行建制、维护 cron、处理 pending 规则时，必须先读取对应的 reference 文件再操作
- 写入目标子目录不存在时，先创建再写入，不要因为目录缺失而跳过写入

如果技能规则与本地旧文档表述不一致，优先按本技能中的执行型规则处理，再回看本地文档补细节。

## 核心模型

默认采用五层模型，用来判断文件职责、读取顺序和写入位置：

1. **Identity** — Agent 是谁、服务谁、长期风格与边界
2. **Operations** — Agent 怎么工作、流程规则、工具说明
3. **Knowledge** — 长期记忆与结构化事件记录
4. **Context** — 资料、研究、项目背景和共享上下文
5. **Learning** — 错误、纠正、候选晋升内容

不要临时发明新的并列层级。详细定义和常见误区见 `references/model-and-boundaries.md`。

## 快速判断

### Identity
典型文件：`SOUL.md`、`IDENTITY.md`、`USER.md`

### Operations
典型文件：`AGENTS.md`、`TOOLS.md`、`NOTICE.md`

### Knowledge
典型文件：`MEMORY.md`、`memory/YYYY-MM-DD.md`
典型子目录：`memory/tasks/`、`memory/incidents/`、`memory/decisions/`

### Context
典型目录：`shared-context/`（当前共享事实、跨 Agent 共识）、`context/`（长期可复用资料、研究）

### Learning
典型目录：`.learnings/`、`reviews/`
典型文件：`.learnings/ERRORS.md`、`.learnings/LEARNINGS.md`、`.learnings/pending/rules.json`

## 首次接管 workspace 的初始化

优先执行 `bootstrap.py init` 创建最小目录骨架。

默认创建的最小目录：`memory/`、`.learnings/`、`.learnings/pending/`、`.learnings/pending/archive/`、`context/`、`shared-context/`、`reviews/`

默认初始化的最小文件：`.learnings/pending/rules.json`、`.learnings/pending/info-sources.json`

初始化规则：
1. 先确认 workspace 根路径
2. 只在当前 workspace 内创建
3. 只创建最小结构，不预填虚假内容
4. 已存在文件一律跳过，不覆盖

## 建制后接管运行层

首次完成初始化、启用 pending 队列或自我进化机制后，必须按以下固定顺序完成接管：

1. 检查并补齐目录与最小文件
2. 检查 `daily-info-update` 和 `daily-review` 的 cron 任务（详见 `references/self-evolution.md`）
3. 读取当前 `AGENTS.md`
4. 如需修改，先创建备份 `AGENTS.backup-YYYYMMDD-HHMM.md`
5. 更新 `AGENTS.md` 的运行层内容
6. 做建制验收

cron 约定、运行层接管细则和建制验收标准，详见 `references/self-evolution.md`。

> 当前智能体的 agent id 可通过 `openclaw agent list` 查看，或在 OpenClaw 会话中通过系统上下文获取。

## 自我进化机制

内建一条自我进化闭环，把"实时纠正"和"定时发现"分开治理。

### 通道一：实时纠正
用户当场纠正时，可直接写入 `.learnings/ERRORS.md`、`.learnings/LEARNINGS.md`、`memory/YYYY-MM-DD.md`，必要时写 `MEMORY.md` 和 `AGENTS.md`。

### 通道二：定时学习
`daily-info-update` 和 `daily-review` 发现的候选规则必须先进 `.learnings/pending/rules.json`，由 `daily-review` 审核后才能晋升到核心文件。

pending 规则 schema、生命周期、cron 职责和审核流程，详见 `references/self-evolution.md`。

## 默认检索顺序

复杂任务默认按以下顺序取材：

1. 根目录核心文件
2. `shared-context/`
3. 目标目录的 `.abstract.md`
4. 目标目录的 `.overview.md`
5. 详细正文文件
6. 外部资料

## 先读旧错和旧经验

当任务属于高重复、易出错或曾被纠正过的领域时，正式执行前先检查：
- `.learnings/ERRORS.md`、`.learnings/LEARNINGS.md`、`.learnings/pending/rules.json`
- 相关 `MEMORY.md` 和 `memory/` 记录
- 相关 `context/` 资料

如果用户正在纠正你，先判断是否存在相关旧错，必要时回看再回答。

## 写入边界

- `MEMORY.md` — 只写长期稳定、会持续影响判断的内容
- `memory/` — 日常过程、临时上下文、事件记录、每日进化摘要
- `context/` — 资料型内容（仓库分析、研究、方案文档）
- `.learnings/` — 候选学习（纠正、工具失败、环境坑点、待晋升规则）

## 执行后的回写闭环

任务结束后，额外判断是否需要写回：
- 新的错误模式 → `.learnings/ERRORS.md`
- 新的纠正经验 → `.learnings/LEARNINGS.md`
- 稳定经验 → `MEMORY.md`
- 可复用资料 → `context/`
- 候选规则 → `.learnings/pending/rules.json`

## 外部主动学习

可以主动搜索外部资料，但不要直接升级为核心规则。正确流程：发现候选 → 做摘要 → 问用户是否同意 → 同意后再写入。

## 工作方法

1. 先判断内容属于五层中的哪一层
2. 再判断应写核心文件、资料目录还是候选学习区
3. 复杂任务先按默认检索顺序读取
4. 高频问题域先回看 `.learnings/`、pending 队列和历史记录
5. 命中文件夹后，优先读 `.abstract.md` 和 `.overview.md`
6. 执行后补写错误、经验、资料或长期记忆
7. 借助 `daily-info-update` 与 `daily-review` 定期自我反思
8. 引入外部知识先征得用户同意
9. 修改体系说明优先保持与既有五层模型一致

## 不要这样做

- 不要把外部研究直接塞进 `MEMORY.md`
- 不要把一次性 workaround 直接写成长期规则
- 不要把 `shared-context/` 或 `reviews/` 解释成五层模型之外的新大层
- 不要让多个智能体同时写同一个共享文件
- 不要在没有审核前把定时任务发现的候选学习直接写进核心文件
- 不要未经用户同意就吸收外部新规则
- 不要把无 Git 环境误判成任务阻塞
- 不要在未确认 workspace 根路径前乱建目录
- 不要在未备份旧文档前直接覆盖 `AGENTS.md`
- 不要重复创建属于当前智能体自己的同名 cron 任务
- 不要用批量空文件伪装成已完成初始化

## 典型场景

| 场景 | 要点 | 详细参考 |
|---|---|---|
| 研究文章或仓库 | 放 `context/research/` 或 `context/refs/`，不写 `MEMORY.md` | `references/scenarios-and-retrieval.md` |
| 记录用户纠正 | 先写 `.learnings/`，再决定是否进晋升流程 | `references/scenarios-and-retrieval.md` |
| 多智能体共享进展 | 放 `shared-context/`，遵守 one-writer many-readers | `references/scenarios-and-retrieval.md` |
| 沉淀长期偏好 | 提炼后写 `MEMORY.md`，不要整段落盘 | `references/model-and-boundaries.md` |
| 执行高频易错任务 | 先检查 `.learnings/`、daily memory 和相关上下文 | `references/scenarios-and-retrieval.md` |
| 首次接管新 workspace | init → cron → AGENTS.md → 验收 | `references/self-evolution.md` |
| 外部学习新方法 | 先做候选摘要并问用户 | `references/scenarios-and-retrieval.md` |
| 维护自我进化规则队列 | 检查 schema、状态机、清理规则 | `references/self-evolution.md` |

## Git 与非阻塞提交

有 Git 就提交，没有 Git 时以文件写入成功和产物可用作为完成标准。

## References 导航索引

| 文件 | 职责范围 |
|---|---|
| `references/model-and-boundaries.md` | 五层模型详细定义、每层的边界规则、初始化边界和常见误区（共 9 项） |
| `references/scenarios-and-retrieval.md` | 默认检索顺序、错误回读触发规则、典型场景处理步骤、L0/L1/L2 结构、检索轨迹 |
| `references/self-evolution.md` | pending 规则 schema 与生命周期、`daily-info-update` 与 `daily-review` 的职责与约定、cron 建立规则、AGENTS.md 运行层接管细则、建制验收标准、info-sources.json schema、常见错误（共 7 项） |
