# 五层模型与边界

## 五层模型

### Identity
用于定义 Agent 是谁、服务谁、采用什么风格。

典型文件：
- `SOUL.md`
- `IDENTITY.md`
- `USER.md`

只保留长期稳定内容，不写一次性任务资料。

### Operations
用于定义 Agent 怎么工作。

典型文件：
- `AGENTS.md`
- `HEARTBEAT.md`
- `TOOLS.md`
- `NOTICE.md`

写工作方式、流程规则、本地工具说明和协作通知，不承载项目资料。

在多智能体场景下，`HEARTBEAT.md` 也是按各自 workspace 生效，不是默认全体 agent 共用同一份文件。

### Knowledge
用于保存长期记忆与结构化事件记录。

典型文件与目录：
- `MEMORY.md`
- `memory/YYYY-MM-DD.md`
- `memory/tasks/`
- `memory/incidents/`
- `memory/decisions/`

规则：
- `MEMORY.md` 只写长期稳定内容
- daily memory 是原始材料，不等于长期记忆
- 外部研究不要直接进入 `MEMORY.md`

### Context
用于保存资料、研究、项目背景和共享上下文。

典型目录：
- `shared-context/`
- `context/`

区分方式：
- `shared-context/` 存当前共享信息、跨 Agent 共识、阶段性优先级
- `context/` 存长期可复用资料和研究沉淀

### Learning
用于保存错误、纠正、需求和候选晋升内容。

典型目录：
- `.learnings/`
- `reviews/`

规则：
- 所有学习先进入候选池
- 不自动写入核心文件
- 先 review，再晋升

## 初始化边界

首次接管 workspace 时，应先补齐最小目录骨架，再在骨架内工作。

优先使用：
- `python3 ./scripts/init_workspace.py <workspace-root>`

应主动创建的最小目录：
- `memory/`
- `.learnings/`
- `context/`
- `shared-context/`
- `reviews/`

边界：
- 只在当前 agent 的 workspace 根路径内创建
- 只创建最小可用结构
- 不预填虚假内容
- 不要批量制造无意义空文件
- 已存在文件必须保留，不能覆盖用户已有内容

## 从归档走向闭环

仅仅把错误和经验写入文件还不够。要形成真正闭环，还需要：

1. 执行相关任务前主动回看旧错和旧经验
2. 执行后把新错误和新经验写回文件系统
3. 周期性用 heartbeat 检查是否出现重复错误或可晋升经验
4. 让用户作为外部知识吸收和规则晋升的治理阀门

## 常见误区

### 误区一
把 `shared-context/` 当成 Context 之外的新一级层。

修正：
- `shared-context/` 属于 Context
- 它和 `context/` 是同层不同分工

### 误区二
把 `reviews/` 单独解释成一个与 Learning 并列的大层。

修正：
- `reviews/` 属于 Learning
- 它负责索引、审查模板和 review 入口

### 误区三
把 `MEMORY.md` 当作资料总仓。

修正：
- `MEMORY.md` 只放长期稳定内容
- 研究、仓库分析、文章总结应进入 `context/`

### 误区四
把一次性错误直接升级为长期规则。

修正：
- 先写 `.learnings/`
- 审核后再决定是否进入核心文件

### 误区五
只记录错误，不在类似任务前回看旧错。

修正：
- 在高频、易错或被纠正过的问题域，执行前先检查相关 `.learnings/`
- 把错误回读作为复杂任务前置检查的一部分

### 误区六
把外部资料直接当作新规则写进核心文件。

修正：
- 先做候选摘要
- 先问用户是否同意吸收
- 用户同意后，再决定写入 `context/`、`.learnings/` 或核心文件

### 误区七
把无 Git 环境当成任务阻塞。

修正：
- 有 Git 就提交
- 没有 Git 时，以文件写入成功和产物可用作为完成标准

### 误区八
把某个 agent 的 `HEARTBEAT.md` 误当成所有 agent 共用文件。

修正：
- 先确认当前 agent 的 workspace
- 再读取该 workspace 根里的 `HEARTBEAT.md`
