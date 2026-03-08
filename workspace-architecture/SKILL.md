---
name: workspace-architecture
description: Explain and apply a layered workspace architecture for AI agents. Use when an agent needs to understand how a workspace is organized, decide where files should live, determine retrieval order for complex tasks, actively reuse past errors and learnings, avoid mixing rules/memory/research, or design shared conventions for multi-agent collaboration and long-term self-improvement through the file system.
---

# Workspace Architecture

用这份技能来理解和执行一套面向智能体协作的 workspace 分层体系。

## 安装后使用

安装后，先阅读当前 `SKILL.md`。

需要更细 guidance 时，按需读取：
- `./references/model-and-boundaries.md`
- `./references/scenarios-and-retrieval.md`

需要初始化 workspace 最小骨架时，优先使用：
- `./scripts/init_workspace.py`

执行时默认遵守以下硬规则：
- 先确认当前 agent 的 workspace 根路径，再在该 workspace 内执行初始化、读取与写入
- 首次接管一个 workspace 时，先检查最小目录骨架；缺失时优先使用 `./scripts/init_workspace.py` 创建最小可用结构
- `HEARTBEAT.md` 按当前 agent 自己 workspace 根路径读取，不默认全体 agent 共用同一份
- daily memory 必须先读今天对应的 `memory/YYYY-MM-DD.md`，再读昨天对应的 `memory/YYYY-MM-DD.md`
- 如果 today 或 yesterday 对应的 daily memory 文件不存在，必须明确说明不存在，不要假装已经读取
- 有 Git 就提交；无 Git 时，不要把 commit 当阻塞
- heartbeat 无异常统一回复 `HEARTBEAT_OK`
- 外部主动学习只能先做候选摘要，未经用户同意不得写入核心规则
- 初始化时只创建最小骨架，不预填虚假内容，不批量空造无用文件

如果技能规则与本地旧文档表述不一致，优先按本技能中的执行型规则处理，再回看本地文档补细节。

这份技能不只负责“把内容放对地方”，还负责让 Agent 通过文件系统形成闭环：
- 先回看旧错与旧经验
- 再执行任务
- 执行后写回学习池与记忆层
- 通过 heartbeat 定期反思
- 在用户同意前，不把外部新知识直接升级为规则

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

## 首次接管 workspace 的初始化

首次在一个 workspace 中使用本技能时，先检查最小目录骨架是否存在。

优先执行：
- `python3 ./scripts/init_workspace.py <workspace-root>`

如果需要先预览而不实际写入，可先执行：
- `python3 ./scripts/init_workspace.py <workspace-root> --dry-run`

如果需要同时补最小模板文件，并且确认目标文件不存在，可显式使用：
- `python3 ./scripts/init_workspace.py <workspace-root> --with-templates --date YYYY-MM-DD`

默认应主动创建的最小目录：
- `memory/`
- `.learnings/`
- `context/`
- `shared-context/`
- `reviews/`

按需创建的子目录：
- `memory/tasks/`
- `memory/incidents/`
- `memory/decisions/`
- `context/research/`
- `context/refs/`

初始化规则：
1. 先确认当前 agent 的 workspace 根路径
2. 只在当前 workspace 内创建目录和文件
3. 缺目录时优先通过 `./scripts/init_workspace.py` 补齐最小骨架
4. 只创建目录和确有必要的最小文件，不预填虚假内容
5. 已存在文件一律跳过，不覆盖、不清空、不改写
6. 不要因为目录缺失就跳过记忆、学习或上下文沉淀

## 默认检索顺序

复杂任务默认按以下顺序取材：

1. 根目录核心文件
2. `shared-context/`
3. 目标目录的 `.abstract.md`
4. 目标目录的 `.overview.md`
5. 详细正文文件
6. 外部资料

如果要理解资料区布局，优先读 `reviews/CONTEXT-INDEX.md`。

## 先读旧错和旧经验

当任务属于高重复、易出错或曾被用户纠正过的领域时，在正式执行前先检查相关学习记录。

优先回看：
- `.learnings/ERRORS.md`
- `.learnings/LEARNINGS.md`
- `.learnings/PROMOTION_QUEUE.md`
- 相关 `MEMORY.md`
- 相关 `memory/` 记录
- 相关 `context/` 资料

尤其是这些任务：
- 更新与发布
- 路由与日志判断
- 技能路径与目录归属判断
- 文档结构调整
- 高频被纠正的问题域

如果用户正在纠正你，不要只当场修一句。先判断是否存在相关旧错，必要时立即回看再回答。

## 写入边界

### 写入 `MEMORY.md`
只写长期、稳定、会持续影响后续判断的内容：
- 稳定偏好
- 长期有效规则
- 反复验证过的经验
- 会持续影响行为的背景

### 写入 `memory/`
写日常过程和结构化事件：
- 当日记录
- 临时上下文
- 阶段性问题
- 一次性排障过程
- 决策与事故记录

### 写入 `context/`
写资料型内容：
- 仓库分析
- 外部文章总结
- 技术研究
- 项目背景
- 方案文档
- 长期参考资料

### 写入 `.learnings/`
写候选学习：
- 用户纠正
- 工具失败
- 环境坑点
- 能力缺口
- 待晋升规则草案

## 执行后的回写闭环

任务结束后，不要只给结果。额外判断以下内容是否需要写回文件系统：

- 这次有没有新的错误模式 → `.learnings/ERRORS.md`
- 这次有没有新的纠正经验 → `.learnings/LEARNINGS.md`
- 这次有没有值得长期保留的稳定经验 → `MEMORY.md`
- 这次有没有值得复用的资料沉淀 → `context/`
- 这次有没有应该进入晋升队列的规则候选 → `.learnings/PROMOTION_QUEUE.md`

目标不是“有文件就行”，而是形成：
读取旧经验 → 执行任务 → 写回新经验 → 下次再先读 的闭环。

## heartbeat 反思机制

将 heartbeat 视为周期性自我维护入口，而不只是状态检查。

在多智能体场景下，heartbeat 读取的是当前 agent 自己 workspace 根里的 `HEARTBEAT.md`。不要把某个 agent 的 heartbeat 文件误当成其他 agent 的主文件。

heartbeat 反思的最小可跑通闭环只保留四项核心检查：

1. 今天是否有新的错误或被纠正
2. 是否需要写入 `.learnings/`
3. 是否需要提炼进 `MEMORY.md`
4. 是否存在需要用户确认的外部学习候选

设计 heartbeat 时，必须遵守以下原则：
- 最小可跑通
- 不要写复杂
- 结构化
- 清晰可执行
- 给后续扩展留空间

如果没有值得提醒的新情况，可以保持安静。
如果发现重复错误或高价值经验，优先补学习池，而不是只留在对话里。

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
- 不要在没有审核前把候选学习直接写进核心文件
- 不要只记录错误而不在下次任务前回看
- 不要未经用户同意就吸收外部新规则
- 不要把无 Git 环境误判成任务阻塞
- 不要把某个 agent 的 `HEARTBEAT.md` 误当成所有 agent 共用的主文件
- 不要在未确认 workspace 根路径前就乱建目录或文件
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
2. 检查 `memory/`、`.learnings/`、`context/`、`shared-context/`、`reviews/` 是否存在
3. 缺失时主动创建最小可用目录骨架
4. 不要预填虚假内容，不要批量创建无意义空文件
5. 再开始后续的记忆、学习、上下文落盘工作

### 场景七：heartbeat 期间的自我反思
检查今天的错误、纠正、可晋升经验和需要归档的资料，而不是只做表面心跳响应。

### 场景八：想从外部学习新方法
先做候选摘要并向用户确认，同意后再吸收落盘。


## 工作方法

1. 先判断内容属于五层中的哪一层
2. 再判断应该写核心文件、资料目录还是候选学习区
3. 复杂任务先按默认检索顺序读取
4. 遇到高频问题域时，先回看相关 `.learnings/` 和历史记录
5. 命中文件夹后，优先读 `.abstract.md` 和 `.overview.md`
6. 执行后补写错误、经验、资料或长期记忆
7. 借助 heartbeat 定期做自我反思与提炼
8. 如果要引入外部新知识，先征得用户同意
9. 如果要修改体系说明，优先保持与既有五层模型一致

## 当前最小闭环状态

当前这套体系已经跑通的最小闭环包括：

1. 记录错误
2. 记录经验
3. 在相关任务前回读旧错与旧经验
4. 在 heartbeat 中做最小反思检查
5. 对外部主动学习设置用户确认阀门

这意味着系统已经从“有文件可存”进入到“能形成基本反馈回路”的状态。

## 当前不包含的内容

以下内容不属于当前最小闭环范围，应作为后续扩展，而不是现在写进 heartbeat 主干：

- 午饭提醒
- 天气提醒
- 通知提醒
- 待办提醒
- 复杂时间调度规则
- 更细的 heartbeat 分支控制
- 自动化外部学习队列
- 针对专项问题域的独立反思技能

## 本轮实战修订要点

这份技能已根据一次真实多智能体运行中的问题进行修订，当前特别强调：
- heartbeat 读取的是当前 agent 自己 workspace 根里的 `HEARTBEAT.md`
- daily memory 必须使用显式日期文件规则
- 无 Git 时不应把 commit 当阻塞
- 首次接管 workspace 时应主动创建最小目录骨架
- heartbeat 无异常回复统一为 `HEARTBEAT_OK`

## 需要更细 guidance 时

按需读取：
- `./references/model-and-boundaries.md`：五层模型、边界和常见误区
- `./references/scenarios-and-retrieval.md`：检索顺序、错误回读、heartbeat 反思、落盘场景和外部学习规则
