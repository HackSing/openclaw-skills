# 检索顺序与典型场景

## 默认检索顺序

复杂任务默认采用以下顺序：

1. 根目录核心文件
2. `shared-context/`
3. 目标目录的 `.abstract.md`
4. 目标目录的 `.overview.md`
5. 详细正文文件
6. 外部资料

命中目录后，不要一上来读完整个目录正文。

## 错误回读的触发规则

以下情况在正式执行前，优先检查相关 `.learnings/`、相关 `memory/` 和记忆文件：

- 该领域之前出过错
- 用户正在纠正你
- 这是高频重复任务
- 这是更新、发布、路由、目录结构、技能路径等易错问题
- 这是复杂排障或多步骤任务
- 这是 self-evolution、cron、pending 队列或规则晋升相关任务

优先回看：
- `.learnings/ERRORS.md`
- `.learnings/LEARNINGS.md`
- `.learnings/pending/rules.json`
- 相关 `MEMORY.md`
- 今天对应的 `memory/YYYY-MM-DD.md`
- 昨天对应的 `memory/YYYY-MM-DD.md`

如果今天或昨天的 daily memory 文件不存在，必须如实记录文件不存在，不要假装已经读取到内容。

## 典型场景

### 用户发来文章让我学习
处理方式：
1. 放进 `context/research/` 或 `context/refs/articles/`
2. 如果会长期复用，补 `.abstract.md` 和 `.overview.md`
3. 不直接写进 `MEMORY.md`

### 用户发来 GitHub 仓库让我研究
处理方式：
1. 放进 `context/research/` 或 `context/refs/repos/`
2. 提炼可采纳点
3. 只有稳定规则才考虑进入 `AGENTS.md` 或 `TOOLS.md`

### 用户纠正我说错了
处理方式：
1. 先检查是否已有相关旧错或旧经验
2. 再给出修正后的回答
3. 将新经验写到 `.learnings/LEARNINGS.md`
4. 如果涉及错误模式，也补写 `.learnings/ERRORS.md`

### 命令失败或工具异常
处理方式：
1. 先写到 `.learnings/ERRORS.md`
2. 提炼最小修复路径
3. 如果是环境级坑点，再考虑补到 `TOOLS.md`

### 无 Git 的工作区修改
处理方式：
1. 先确认当前工作区是否存在 `.git`
2. 如果有 Git，按提交纪律执行
3. 如果没有 Git，不把 commit 当阻塞
4. 以文件写入成功、路径正确、产物可用作为完成标准

### 首次接管 workspace
处理方式：
1. 先确认当前 agent 的 workspace 根路径
2. 优先执行 `python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py init <workspace-root>`
3. 如需先预览风险，先执行 `python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py init <workspace-root> --dry-run`
4. 检查 `memory/`、`.learnings/`、`.learnings/pending/`、`context/`、`shared-context/`、`reviews/` 是否已齐备
5. 检查 `.learnings/pending/rules.json` 与 `.learnings/pending/info-sources.json` 是否已初始化
6. 只创建最小可用结构，不预填虚假内容
7. 已存在文件一律跳过，不覆盖用户已有内容
8. 再开始后续的读取、记忆、学习与沉淀

### 多个智能体要共享同一批信息
处理方式：
1. 放进 `shared-context/`
2. 明确谁写谁读
3. 遵守 one-writer many-readers

### 重要事故或误操作
处理方式：
1. 写入 `memory/incidents/`
2. 如有长期影响，再提炼进 `MEMORY.md`

### 重要方案取舍
处理方式：
1. 写入 `memory/decisions/`
2. 必要时在项目目录保留项目级决策记录

### 收到 heartbeat
处理方式：
1. 先确认当前 agent 的 workspace 根路径
2. 读取该 workspace 根里的 `HEARTBEAT.md`
3. 只执行轻量运行规则，不把 heartbeat 当成反思、审核或规则晋升通道
4. 自我进化相关检查统一交给 `daily-info-update` 与 `daily-review`

### 主动外部学习
处理方式：
1. 搜索或收集可能有价值的外部资料
2. 提炼候选摘要、来源、适用场景和潜在收益
3. 先询问用户是否同意吸收或落地
4. 用户同意后，再决定写入 `context/`、`.learnings/` 或核心文件

### 维护 pending 规则队列
处理方式：
1. 先读取 `references/self-evolution.md`
2. 检查 `rules.json` 顶层结构和单条 rule schema
3. 检查 `rules.json` 是否只保留 pending
4. 检查 archive 是否按天归档
5. 修改 cron 时优先只改 message 文案，不随意改调度和机制

### 调整 daily-info-update 或 daily-review
处理方式：
1. 先核对现有任务内容，不要直接执行 run
2. 核对 OpenClaw cron 是否已经存在，并确认 `agent` 绑定到了当前智能体自己
3. 先判断是文案收口还是机制重构
4. 如果只是 schema、source、生命周期歧义，优先只改 message 文案
5. 改完后做只读复核，确认 schedule、sessionTarget、delivery、agent 未被误改

## L0 / L1 / L2

`context/` 下的重要目录采用三层结构：

- `L0`：`.abstract.md`
- `L1`：`.overview.md`
- `L2`：详细正文

默认顺序：
1. 先读 `.abstract.md`
2. 再读 `.overview.md`
3. 最后读正文

## 何时需要补检索轨迹

以下情况建议补检索轨迹：
- 复杂任务
- 多来源资料汇总
- 结构分析
- 方案对比
- 容易被追问依据的结论
- 引用了历史错误、长期记忆或外部资料的判断
- 自我进化机制、规则晋升、cron 审核链路相关判断
