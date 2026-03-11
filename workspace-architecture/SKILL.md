---
name: workspace-architecture
description: Explain and apply a layered workspace architecture for AI agents. Use when an agent needs to understand how a workspace is organized, decide where files should live, determine retrieval order for complex tasks, initialize a new workspace safely, integrate new runtime rules into AGENTS.md after architecture setup, or operate the self-evolution loop built on .learnings/pending/rules.json and the cron jobs named daily-info-update and daily-review.
---

# Workspace Architecture

用这份技能来理解、建立并运行一套面向智能体协作的 workspace 分层体系。

## 安装后使用

安装后，先阅读当前 `SKILL.md`。

需要更细 guidance 时，按需读取：
- `./references/model-and-boundaries.md`
- `./references/scenarios-and-retrieval.md`
- `./references/self-evolution.md`

需要初始化 workspace 最小骨架时，使用：
- `python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py init <workspace-root>`

需要检查集成与自我进化骨架状态时，使用：
- `python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py check <workspace-root>`

需要创建规则补丁文件时，使用：
- `python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py patch <workspace-root>`

## 执行硬规则

- 先确认当前 agent 的 workspace 根路径，再在该 workspace 内执行初始化、读取与写入
- 首次接管一个 workspace 时，先检查最小目录骨架；缺失时优先使用 `bootstrap.py init` 创建最小可用结构
- `HEARTBEAT.md` 按当前 agent 自己 workspace 根路径读取，不默认全体 agent 共用同一份
- daily memory 必须先读今天对应的 `memory/YYYY-MM-DD.md`，再读昨天对应的 `memory/YYYY-MM-DD.md`
- 如果 today 或 yesterday 对应的 daily memory 文件不存在，必须明确说明不存在，不要假装已经读取
- 有 Git 就提交；无 Git 时，不要把 commit 当阻塞
- heartbeat 无异常统一回复 `HEARTBEAT_OK`
- 用户当场纠正触发的实时学习可直接写既有学习与记忆通道
- 定时任务自己发现的候选规则，必须先进入 `.learnings/pending/rules.json`，未经审核不得直接写入核心规则文件
- 初始化时只创建最小骨架，不预填虚假内容，不批量空造无用文件
- 首次建制完成后，必须检查并更新当前 workspace 的 `AGENTS.md`，让运行层接住新架构
- 更新 `AGENTS.md` 前，必须先备份原文件，再修改；不要直接裸改旧文档
- 启用自我进化机制时，必须检查名称为 `daily-info-update` 与 `daily-review` 的 cron 任务是否存在；不存在则创建，存在则核对配置是否符合约定

如果技能规则与本地旧文档表述不一致，优先按本技能中的执行型规则处理，再回看本地文档补细节。

## 核心模型

默认采用五层模型：

1. Identity
2. Operations
3. Knowledge
4. Context
5. Learning

用这个模型判断文件职责、读取顺序和写入位置，不要临时发明新的并列层级。

## 快速判断

### Identity
存放 Agent 是谁、服务谁、长期风格与边界。

典型文件：
- `SOUL.md`
- `IDENTITY.md`
- `USER.md`

### Operations
存放 Agent 怎么工作。

典型文件：
- `AGENTS.md`
- `HEARTBEAT.md`
- `TOOLS.md`
- `NOTICE.md`

注意：在多智能体场景下，`HEARTBEAT.md` 应按各自 workspace 理解。
- `main` 读取 `main` 自己 workspace 根里的 `HEARTBEAT.md`
- 其他 agent 读取各自 workspace 根里的 `HEARTBEAT.md`
- 不要默认所有 agent 共用同一个 `HEARTBEAT.md`

### Knowledge
存放长期记忆和结构化事件记录。

典型文件：
- `MEMORY.md`
- `memory/YYYY-MM-DD.md`
- `memory/tasks/`
- `memory/incidents/`
- `memory/decisions/`

读取 daily memory 时，默认按以下规则执行：
1. 先读今天对应的 `memory/YYYY-MM-DD.md`
2. 再读昨天对应的 `memory/YYYY-MM-DD.md`
3. 如果文件不存在，必须明确说明文件不存在
4. 不要把“当天.md”“今日.md”“today.md”当成真实文件名
5. 不要假装已经读取到不存在的文件

### Context
存放资料、研究、项目背景和共享上下文。

典型目录：
- `shared-context/`
- `context/`

区分规则：
- 当前共享事实、跨 Agent 共识、阶段性协作信息 → `shared-context/`
- 长期可复用资料、研究、项目背景 → `context/`

### Learning
存放错误、纠正、需求和候选晋升内容。

典型目录：
- `.learnings/`
- `reviews/`

典型文件与子目录：
- `.learnings/ERRORS.md`
- `.learnings/LEARNINGS.md`
- `.learnings/pending/rules.json`
- `.learnings/pending/info-sources.json`
- `.learnings/pending/archive/`

## 首次接管 workspace 的初始化

首次在一个 workspace 中使用本技能时，先检查最小目录骨架是否存在。

优先执行：
- `python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py init <workspace-root>`

如果需要先预览而不实际写入，可先执行：
- `python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py init <workspace-root> --dry-run`

默认应主动创建的最小目录：
- `memory/`
- `.learnings/`
- `.learnings/pending/`
- `.learnings/pending/archive/`
- `context/`
- `shared-context/`
- `reviews/`

按需创建的子目录：
- `memory/tasks/`
- `memory/incidents/`
- `memory/decisions/`
- `context/research/`
- `context/refs/`

默认应初始化的最小文件：
- `.learnings/pending/rules.json`
- `.learnings/pending/info-sources.json`

初始化规则：
1. 先确认当前 agent 的 workspace 根路径
2. 只在当前 workspace 内创建目录和文件
3. 缺目录时优先通过 `bootstrap.py init` 补齐最小骨架
4. 只创建目录和确有必要的最小文件，不预填虚假内容
5. 已存在文件一律跳过，不覆盖、不清空、不改写
6. 不要因为目录缺失就跳过记忆、学习或上下文沉淀

## 建制后接管运行层

建制完成不等于能稳定运行。首次完成以下任一动作后，必须按固定顺序完成接管：
- 初始化最小目录骨架
- 启用 `.learnings/pending/`
- 启用自我进化机制
- 把 workspace 从旧结构迁移到五层结构

### 建制完成的固定顺序

1. 检查并补齐目录与最小文件
2. 检查名称为 `daily-info-update` 和 `daily-review` 的 cron 任务是否存在；不存在则创建，存在则核对配置
3. 读取当前 `AGENTS.md`
4. 如需修改，先创建备份文件 `AGENTS.backup-YYYYMMDD-HHMM.md`
5. 更新 `AGENTS.md` 的运行层内容
6. 做建制验收，确认后续会话仅依赖 `AGENTS.md` 也能正常运行

### 建制阶段的 cron 建立规则

启用自我进化机制时，必须检查以下两个固定名称的 cron 任务：
- `daily-info-update`
- `daily-review`

检查原则：
- 先检查是否存在
- 不存在则创建
- 已存在则核对调度、时区、会话目标、delivery 与消息内容是否符合约定
- 如果只有文案不完整，优先修正文案，不轻易改动整体机制
- 不要重复创建同名任务

固定约定：

#### `daily-info-update`
- 名称：`daily-info-update`
- 调度：`0 22 * * *`
- 时区：`Asia/Shanghai`
- 会话：`isolated`
- delivery：`none`
- 作用：信息流更新，只产出 pending 规则，不直接写核心文件

#### `daily-review`
- 名称：`daily-review`
- 调度：`0 23 * * *`
- 时区：`Asia/Shanghai`
- 会话：`isolated`
- delivery：`none`
- 作用：清理、补录、审核、归档和每日进化摘要，是候选规则的唯一晋升闸门

### 运行层接管规则

重点检查当前 `AGENTS.md` 是否已经覆盖以下运行层最小规则：
- 会话启动顺序
- 最小检索顺序
- 新的写入边界
- `.learnings/pending/rules.json` 的运行规则
- `daily-review` 作为候选规则晋升闸门

如果需要修改 `AGENTS.md`：
- 必须先备份，固定命名为 `AGENTS.backup-YYYYMMDD-HHMM.md`
- 先读取原文件，确认哪些段落属于人格、协作习惯和安全边界
- 不要无备份直接覆盖旧文档
- 不要删除与新架构无冲突的已有规则
- 只接管运行层，不复制整份 skill

更新后的 `AGENTS.md` 应保留的运行层内容：
- 会话启动顺序
- 最小导航与检索顺序
- 写入边界
- 定时学习候选先进 `.learnings/pending/rules.json`
- `daily-review` 是候选规则晋升闸门
- 关键改动前先给方案并等用户确认
- 长任务主动汇报
- 有 Git 就提交，无 Git 不阻塞

### 建制验收标准

建制完成后，至少同时满足：
- 目录和最小文件已建立
- `daily-info-update` 已存在且配置正确
- `daily-review` 已存在且配置正确
- `AGENTS.md` 已接住运行层最小规则
- 如果下一次会话不再触发本 skill，仅依赖新的 `AGENTS.md`，当前 agent 仍然能按新架构运行

## 自我进化机制

这套技能内建一条新的自我进化闭环，用来把“实时纠正”和“定时发现”分开治理。

### 两条学习通道

#### 通道一：实时纠正
适用场景：
- 用户当场指出错误
- 可信度高
- 需要立即修正与记录

保留原有流程：
- 承认
- 说清
- 修正
- 写入

可直接写入：
- `.learnings/ERRORS.md`
- `.learnings/LEARNINGS.md`
- `memory/YYYY-MM-DD.md`
- 必要时 `MEMORY.md`
- 必要时 `AGENTS.md`

#### 通道二：定时学习
适用场景：
- 名称为 `daily-info-update` 的 cron 任务发现的新规则候选
- 名称为 `daily-review` 的 cron 任务在复盘中发现的潜在规则
- 高频错误模式提炼出的规则

硬规则：
- 不得直接写入 `MEMORY.md` 或 `AGENTS.md`
- 必须先进入 `.learnings/pending/rules.json`
- 审核通过后才能晋升到核心文件

### pending 规则队列

`pending/rules.json` 是定时学习通道的唯一入口。

顶层结构固定为：

```json
{
  "version": "YYYY-MM-DD",
  "rules": []
}
```

单条规则必须使用以下字段：

```json
{
  "id": "pending_YYYYMMDD_001",
  "source": "info_update / review / error_pattern",
  "source_detail": "具体来源描述",
  "created_at": "ISO 8601 带时区时间",
  "content": "建议的规则内容，一句话描述在什么情况下应该怎么做",
  "reason": "为什么建议新增这条规则",
  "target_files": ["AGENTS.md"],
  "status": "pending / integrated / rejected / expired",
  "reviewed_at": null,
  "review_note": null
}
```

字段含义：
- `source=info_update`：来自名称为 `daily-info-update` 的 cron 任务
- `source=review`：来自名称为 `daily-review` 的 cron 任务中的直接复盘判断
- `source=error_pattern`：来自名称为 `daily-review` 的 cron 任务中，对同类错误累计后的规则提炼

### 规则生命周期

规则状态只有四种：
- `pending`
- `integrated`
- `rejected`
- `expired`

执行硬规则：
- `rules.json` 永远只保留 `pending`
- 一旦变成 `integrated`、`rejected`、`expired`
- 必须在名称为 `daily-review` 的同次执行中立即移入 `.learnings/pending/archive/rules_YYYY-MM-DD.json`
- `pending` 超过 7 天仍未审核，自动标记为 `expired` 并归档
- archive 默认保留 30 天，超过 30 天自动删除

### 两个定时任务

以下名称是固定运行名，不要自行发明别名：
- `daily-info-update`
- `daily-review`

#### `daily-info-update`
职责：
- 读取 `.learnings/pending/info-sources.json`
- 只提炼与当前职责直接相关、能改变行为、目标文件明确的候选规则
- 每天最多新增 3 条 pending 规则
- 模糊内容直接丢弃

写入规则：
- 只写 `.learnings/pending/rules.json`
- `source` 固定为 `info_update`
- `status` 固定为 `pending`
- 完成后写当天 daily memory 摘要

#### `daily-review`
职责分四段：
1. 清理与归档
2. 回顾遗漏错误并补录
3. 审核 pending 规则并决定晋升或拒绝
4. 生成每日进化摘要

额外硬规则：
- 直接复盘发现的新候选规则，`source` 必须设为 `review`
- 同类错误累计达到 3 次以上提炼出的规则，`source` 必须设为 `error_pattern`
- `error_pattern` 规则一旦采纳，除写入目标文件外，还要在 `.learnings/LEARNINGS.md` 记录“从错误链路提炼成规则”的来源

### 写入边界

#### 写入 `MEMORY.md`
只写长期、稳定、会持续影响后续判断的内容：
- 稳定偏好
- 长期有效规则
- 反复验证过的经验
- 会持续影响行为的背景

#### 写入 `memory/`
写日常过程和结构化事件：
- 当日记录
- 临时上下文
- 阶段性问题
- 一次性排障过程
- 决策与事故记录
- 每日进化摘要

#### 写入 `context/`
写资料型内容：
- 仓库分析
- 外部文章总结
- 技术研究
- 项目背景
- 方案文档
- 长期参考资料

#### 写入 `.learnings/`
写候选学习：
- 用户纠正
- 工具失败
- 环境坑点
- 能力缺口
- 待晋升规则草案

## 默认检索顺序

复杂任务默认按以下顺序取材：

1. 根目录核心文件
2. `shared-context/`
3. 目标目录的 `.abstract.md`
4. 目标目录的 `.overview.md`
5. 详细正文文件
6. 外部资料

## 先读旧错和旧经验

当任务属于高重复、易出错或曾被用户纠正过的领域时，在正式执行前先检查相关学习记录。

优先回看：
- `.learnings/ERRORS.md`
- `.learnings/LEARNINGS.md`
- `.learnings/pending/rules.json`
- 相关 `MEMORY.md`
- 相关 `memory/` 记录
- 相关 `context/` 资料

尤其是这些任务：
- 更新与发布
- 路由与日志判断
- 技能路径与目录归属判断
- 文档结构调整
- 高频被纠正的问题域
- 自我进化架构维护
- `daily-info-update` 与 `daily-review` 的配置维护

如果用户正在纠正你，不要只当场修一句。先判断是否存在相关旧错，必要时立即回看再回答。

## 执行后的回写闭环

任务结束后，不要只给结果。额外判断以下内容是否需要写回文件系统：

- 这次有没有新的错误模式 → `.learnings/ERRORS.md`
- 这次有没有新的纠正经验 → `.learnings/LEARNINGS.md`
- 这次有没有值得长期保留的稳定经验 → `MEMORY.md`
- 这次有没有值得复用的资料沉淀 → `context/`
- 这次有没有应该进入 pending 规则队列的候选 → `.learnings/pending/rules.json`

目标不是“有文件就行”，而是形成：
读取旧经验 → 执行任务 → 写回新经验 → `daily-review` 审核 → 下次再先读 的闭环。

## heartbeat 反思机制

将 heartbeat 视为周期性自我维护入口，而不只是状态检查。

在多智能体场景下，heartbeat 读取的是当前 agent 自己 workspace 根里的 `HEARTBEAT.md`。不要把某个 agent 的 heartbeat 文件误当成其他 agent 的主文件。

heartbeat 反思的最小可跑通闭环只保留四项核心检查：
1. 今天是否有新的错误或被纠正
2. 是否需要写入 `.learnings/`
3. 是否需要提炼进 `MEMORY.md`
4. 是否存在需要用户确认的外部学习候选

如果当前 workspace 已启用自我进化机制，还应额外检查：
- `pending/rules.json` 是否结构合法
- 是否存在积压过久的 pending 规则
- 当天 daily memory 是否已记录进化摘要

## 外部主动学习

可以主动搜索外部资料来改进工作方式，但不要直接把外部信息升级为核心规则。

正确流程：
1. 发现可疑似有价值的新资料
2. 做摘要和候选判断
3. 标明来源、适用场景和潜在收益
4. 先询问用户是否同意吸收或落地
5. 用户同意后，再写入 `context/`、`.learnings/` 或其他合适位置

默认不要擅自把网上看到的新做法直接写进：
- `SOUL.md`
- `AGENTS.md`
- `MEMORY.md`
- 其他核心规则文件

## Git 与非阻塞提交规则

- 有 Git 就提交
- 没有 Git 时，不要把 commit 当作任务阻塞
- 无 Git 环境下，应以文件实际写入成功、路径正确、产物可用作为完成标准
- 不要因为没有 `.git` 就把本可完成的任务误报成未完成

## 不要这样做

- 不要把外部研究直接塞进 `MEMORY.md`
- 不要把一次性 workaround 直接写成长期规则
- 不要把 `shared-context/` 单独解释成五层模型之外的新大层
- 不要把 `reviews/` 从 Learning 中拆出来另立一层
- 不要让多个智能体同时写同一个共享文件
- 不要在没有审核前把定时任务发现的候选学习直接写进核心文件
- 不要只记录错误而不在下次任务前回看
- 不要未经用户同意就吸收外部新规则
- 不要把无 Git 环境误判成任务阻塞
- 不要把某个 agent 的 `HEARTBEAT.md` 误当成所有 agent 共用的主文件
- 不要在未确认 workspace 根路径前就乱建目录或文件
- 不要在未备份旧文档前直接覆盖 `AGENTS.md`
- 不要重复创建同名 cron 任务
- 不要用批量空文件伪装成“已经完成初始化”

## 典型场景

### 场景一：研究一篇文章或一个仓库
放进 `context/research/` 或 `context/refs/`，不要直接写进 `MEMORY.md`。

### 场景二：记录用户纠正
先写进 `.learnings/LEARNINGS.md` 或 `.learnings/ERRORS.md`，再决定是否进入晋升流程。

### 场景三：多个智能体共享当前进展
放进 `shared-context/`，并遵守 one-writer many-readers。

### 场景四：沉淀长期稳定偏好或长期规则
提炼后写进 `MEMORY.md`，不要把原始对话整段落盘。

### 场景五：执行一个高频易错任务
先检查相关 `.learnings/`、今天与昨天对应的 `memory/YYYY-MM-DD.md`、以及相关上下文资料，再开始执行。如果 daily memory 文件不存在，必须如实说明不存在。

### 场景六：首次接管一个新的 workspace
处理方式：
1. 先确认当前 agent 的 workspace 根路径
2. 检查 `memory/`、`.learnings/`、`.learnings/pending/`、`context/`、`shared-context/`、`reviews/` 是否存在
3. 缺失时主动创建最小可用目录骨架
4. 初始化 `rules.json` 与 `info-sources.json`
5. 检查并建立或修正 `daily-info-update` 与 `daily-review`
6. 检查并更新 `AGENTS.md`
7. 更新前先创建 `AGENTS.backup-YYYYMMDD-HHMM.md`
8. 做建制验收

### 场景七：heartbeat 期间的自我反思
检查今天的错误、纠正、可晋升经验和需要归档的资料，而不是只做表面心跳响应。

### 场景八：想从外部学习新方法
先做候选摘要并向用户确认，同意后再吸收落盘。

### 场景九：维护自我进化规则队列
优先读取 `./references/self-evolution.md`，检查 schema、状态机、清理规则和 `daily-info-update`、`daily-review` 的职责边界；修改定时任务时，优先只改文案，不轻易改整体机制与调度。

## 工作方法

1. 先判断内容属于五层中的哪一层
2. 再判断应该写核心文件、资料目录还是候选学习区
3. 复杂任务先按默认检索顺序读取
4. 遇到高频问题域时，先回看相关 `.learnings/`、pending 队列和历史记录
5. 命中文件夹后，优先读 `.abstract.md` 和 `.overview.md`
6. 执行后补写错误、经验、资料或长期记忆
7. 借助 heartbeat 和 `daily-review` 定期做自我反思与提炼
8. 如果要引入外部新知识，先征得用户同意
9. 如果要修改体系说明，优先保持与既有五层模型一致

## 当前最小闭环状态

当前这套体系已经跑通的最小闭环包括：
1. 记录错误
2. 记录经验
3. 在相关任务前回读旧错与旧经验
4. 在 heartbeat 中做最小反思检查
5. 对外部主动学习设置用户确认阀门
6. 用 pending 队列隔离定时任务发现的规则候选
7. 用 `daily-review` 审核候选规则并决定是否晋升
8. 建制后把运行层规则写回 `AGENTS.md`
9. 建制时检查并建立 `daily-info-update` 与 `daily-review`

## 需要更细 guidance 时

按需读取：
- `./references/model-and-boundaries.md`：五层模型、边界和常见误区
- `./references/scenarios-and-retrieval.md`：检索顺序、错误回读、heartbeat 反思、落盘场景和外部学习规则
- `./references/self-evolution.md`：pending 规则 schema、状态机、`daily-info-update`、`daily-review`、运行层接管与建制验收规则
