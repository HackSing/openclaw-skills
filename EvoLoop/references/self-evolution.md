# 自我进化机制

## 目标

把两类学习来源分开治理：

1. 用户当场纠正触发的实时学习
2. 定时任务自己发现的候选规则

前者可信度高，可沿既有通道直接记录。后者必须先经过 pending 缓冲与 review 审核，不能直接污染核心规则。

## 固定对象名称

以下名称是这套机制中的固定运行名，不要自行发明别名：

- 候选规则队列文件：`.learnings/pending/rules.json`
- 信息源清单文件：`.learnings/pending/info-sources.json`
- 候选规则归档目录：`.learnings/pending/archive/`
- 信息流更新 cron：`daily-info-update`
- 每日回顾 cron：`daily-review`
- 运行层主文档：`AGENTS.md`
- 运行层备份文件模式：`AGENTS.backup-YYYYMMDD-HHMM.md`

## 文件结构

```text
.learnings/
├── ERRORS.md
├── LEARNINGS.md
├── pending/
│   ├── rules.json
│   ├── info-sources.json
│   └── archive/
│       └── rules_YYYY-MM-DD.json
```

说明：
- `ERRORS.md`：记录错误模式
- `LEARNINGS.md`：记录纠正经验与可复用修正规则
- `pending/rules.json`：待审核规则队列
- `pending/info-sources.json`：信息流来源清单
- `pending/archive/`：已处理规则归档

## 两条通道

### 实时纠正通道

适用场景：
- 用户正在纠正你
- 可信度足够高
- 需要立刻修正与记忆

可直接写：
- `.learnings/ERRORS.md`
- `.learnings/LEARNINGS.md`
- `memory/YYYY-MM-DD.md`
- 必要时 `MEMORY.md`
- 必要时 `AGENTS.md`

### 定时学习通道

适用场景：
- 名称为 `daily-info-update` 的 cron 任务发现新规则候选
- 名称为 `daily-review` 的 cron 任务复盘时发现潜在规则
- `ERRORS.md` 中同类错误累计达到阈值后提炼出的规则

硬规则：
- 不得直接写入 `MEMORY.md` 或 `AGENTS.md`
- 必须先写进 `.learnings/pending/rules.json`
- 只能由名称为 `daily-review` 的 cron 任务审核后决定是否晋升

## rules.json 结构

顶层结构固定为：

```json
{
  "version": "YYYY-MM-DD",
  "rules": []
}
```

单条规则结构固定为：

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

## source 取值

- `info_update`
  - 来自名称为 `daily-info-update` 的 cron 任务
- `review`
  - 来自名称为 `daily-review` 的 cron 任务中的直接复盘判断
  - 不是错误累计触发，而是复盘时直接发现的潜在规则
- `error_pattern`
  - 来自名称为 `daily-review` 的 cron 任务中，对同类错误累计后的规则提炼

## target_files 判断原则

- 长期认知、偏好、稳定事实 → `MEMORY.md`
- 执行规则、流程、输出要求 → `AGENTS.md`
- 同时涉及认知与执行 → 两个都写，但内容各自拆分，不要原样复制

如果规则来自 `error_pattern` 并被采纳：
- 除写入目标文件外
- 还要在 `LEARNINGS.md` 追加一条记录
- 写明它来自哪些错误模式，形成“错误 → 经验 → 规则”的链路

## 生命周期

状态只有四种：

- `pending`
- `integrated`
- `rejected`
- `expired`

规则：
- `.learnings/pending/rules.json` 永远只保留 `pending`
- 一旦某条规则变成 `integrated`、`rejected`、`expired`
- 必须在同次 `daily-review` 执行中立即移入 `.learnings/pending/archive/rules_YYYY-MM-DD.json`
- 不允许这些状态残留在 `rules.json`

过期机制：
- `pending` 超过 7 天仍未审核 → 标记为 `expired`
- 填写 `reviewed_at` 和 `review_note`
- 立即移入 archive

archive 清理：
- archive 文件默认保留 30 天
- 超过 30 天自动删除

## 建制层必须建立的两个 cron

启用自我进化机制时，必须检查以下两个固定名称的 cron 任务：
- `daily-info-update`
- `daily-review`

检查原则：
- 先检查 OpenClaw 的 cron 任务是否存在
- 判断标准不是“有没有同名任务”，而是“有没有绑定到当前智能体自己的同名任务”
- 不存在则通过 `openclaw cron` 创建
- 已存在则核对调度、时区、会话目标、delivery、agent 与消息内容是否符合约定
- `agent` 必须显式绑定到当前智能体自己，不能绑定到其他智能体
- 每个智能体维护自己的一对任务，即使任务名相同，也必须以当前智能体自己的 agent id 运行
- 如果发现同名任务属于其他智能体，应视为当前智能体自己的任务不存在，并直接为当前智能体新建一对任务
- 不要修改、改绑或接管属于其他智能体的同名任务
- 如果只有文案不完整，优先修正文案，不轻易改动整体机制
- 不要重复创建属于当前智能体自己的同名任务

固定约定：

### `daily-info-update`
- 名称：`daily-info-update`
- 调度：`0 22 * * *`
- 时区：`Asia/Shanghai`
- 会话：`isolated`
- delivery：`none`
- agent：当前智能体自己的 agent id，例如当前智能体是 `creator`，则 agent 必须是 `creator`
- 作用：信息流更新，只产出 pending 规则，不直接写核心文件

### `daily-review`
- 名称：`daily-review`
- 调度：`0 23 * * *`
- 时区：`Asia/Shanghai`
- 会话：`isolated`
- delivery：`none`
- agent：当前智能体自己的 agent id，例如当前智能体是 `creator`，则 agent 必须是 `creator`
- 作用：清理、补录、审核、归档和每日进化摘要，是候选规则的唯一晋升闸门

### cron message 模板

创建 cron 任务时，message 内容必须自包含——隔离会话中 Agent 可能无法访问 EvoLoop 技能文件。以下是两个任务的 message 参考模板，创建时将 `<workspace-root>` 替换为你的工作空间的实际路径。

#### `daily-info-update` message 模板

```text
执行每日信息流更新。工作目录固定为 <workspace-root>。

使用北京时间当前日期生成当天 daily memory 路径 memory/YYYY-MM-DD.md。

读取 <workspace-root>/.learnings/pending/info-sources.json 作为信息源清单，只处理 enabled 为 true 的条目。如果 sources 为空或没有 enabled 为 true 的条目，直接结束任务，并在当天 daily memory 记录：22:00 信息流更新跳过，信息源为空。

每个信息源条目包含一个 instructions 字段，描述如何获取该信息源的内容。按 instructions 指引执行获取，然后对获取到的内容进行筛选和规则提取。

rules.json 顶层结构固定为：
{
  "version": "YYYY-MM-DD",
  "rules": []
}

写入 <workspace-root>/.learnings/pending/rules.json 时，单条规则必须严格使用以下字段，不得缺字段、不得改字段名：
{
  "id": "pending_YYYYMMDD_001",
  "source": "info_update",
  "source_detail": "具体来源描述，写清哪个信息源、哪篇内容或哪条更新",
  "created_at": "ISO 8601 带时区时间",
  "content": "建议的规则内容，一句话描述在什么情况下应该怎么做",
  "reason": "为什么建议新增这条规则",
  "target_files": ["AGENTS.md"],
  "status": "pending",
  "reviewed_at": null,
  "review_note": null
}

逐条检查今日新内容，必须同时满足以下四条才允许写入 rules.json：
1. 与当前职责直接相关，能提升编程、代码审查、调试、文档或 agent 工作流质量，不是泛新闻、泛观点
2. 对现有规则存在明确补充或冲突，能说清影响哪条现有规则；说不清则视为不明确
3. 能写成一句可执行规则（当 X 时应做 Y / 不做 Z），抽象感想不入队
4. 能明确判断 target_files 为 AGENTS.md 或 MEMORY.md 或两者

四条全部满足才新增。source 固定 info_update，status 固定 pending。模糊直接丢弃。每日不超过 3 条。

如果 rules.json 不存在则创建；结构不合法先修正再写入。写入后 rules.json 中所有条目 status 必须为 pending。

完成后在当天 daily memory 记录：22:00 信息流更新完成，新增 N 条 pending 规则。
```

#### `daily-review` message 模板

```text
执行每日回顾。工作目录固定为 <workspace-root>。

使用北京时间当前日期生成当天 daily memory 路径 memory/YYYY-MM-DD.md。

rules.json 路径：<workspace-root>/.learnings/pending/rules.json
rules.json 顶层结构固定为：
{
  "version": "YYYY-MM-DD",
  "rules": []
}
单条规则字段：
{
  "id": "pending_YYYYMMDD_001",
  "source": "info_update / review / error_pattern",
  "source_detail": "具体来源描述",
  "created_at": "ISO 8601 带时区时间",
  "content": "建议的规则内容",
  "reason": "为什么建议新增这条规则",
  "target_files": ["AGENTS.md"],
  "status": "pending / integrated / rejected / expired",
  "reviewed_at": null,
  "review_note": null
}

阶段一 清理：
读取 rules.json。把所有非 pending 条目移入 <workspace-root>/.learnings/pending/archive/rules_YYYY-MM-DD.json。超过 7 天的 pending 标记 expired，填 reviewed_at 和 review_note，移入 archive。删除 archive 中超过 30 天的文件。阶段结束后 rules.json 只保留 pending。

阶段二 错误回顾：
读取当天 daily memory，回溯过去 24 小时对话与记录。重点扫描：用户重复换措辞、语气变化、任务中途放弃、输出被忽略。遗漏错误补录到 <workspace-root>/.learnings/ERRORS.md 和当天 daily memory，标注 review_discovered。ERRORS.md 中同类错误达 3 次以上，提炼为规则写入 rules.json，source 设 error_pattern，status 设 pending。复盘中直接发现的潜在规则（非错误累计触发），source 设 review，status 设 pending。

阶段三 规则审核：
逐条审核 rules.json 中 pending 条目。
采纳：写入 target_files 对应文件；如果 source 为 error_pattern，还必须在 <workspace-root>/.learnings/LEARNINGS.md 追加提炼记录，说明来自哪些错误模式。标记 integrated，填 reviewed_at 和 review_note，立即归档。
拒绝：标记 rejected，填 reviewed_at 和 review_note，立即归档。
需修改：先改 content 或 target_files，再决定采纳或拒绝；不再是 pending 就立即归档。
阶段结束后 rules.json 不允许 integrated、rejected、expired 残留。

阶段四 每日进化摘要：
写入当天 daily memory，包含：今日新增错误数（实时与补录分开）、pending 规则审核结果、新写入 MEMORY.md/AGENTS.md/LEARNINGS.md 条数、高频错误模式提醒、信息流覆盖情况。过期未审核规则醒目标注。

硬规则：rules.json 永远只保留 pending。integrated/rejected/expired 一律归档，不残留。
```

## `daily-info-update`

推荐调度：
- 每天 22:00
- 时区 `Asia/Shanghai`
- 隔离会话执行

职责：
1. 读取 `.learnings/pending/info-sources.json`，只处理 `enabled=true` 的条目
2. 按每个条目的 `instructions` 获取信息（可能是搜索、访问网页、调用其他技能等）
3. 对获取到的内容进行筛选，只把高相关、能改变行为、目标文件明确的内容写成 pending 规则
4. 每日新增规则不超过 3 条
5. 完成后在当天 daily memory 写摘要

写入标准：
- 与当前职责直接相关
- 能说清补充或冲突的是哪条现有规则
- 能写成一句可执行规则
- 能明确判断 `target_files`

只要有一项不明确，就丢弃。

## `daily-review`

推荐调度：
- 每天 23:00
- 时区 `Asia/Shanghai`
- 隔离会话执行

四个阶段：

### 阶段一：清理
- 读取 `.learnings/pending/rules.json`
- 把非 pending 条目移入 archive
- 把超过 7 天的 pending 标记为 expired 后移入 archive
- 删除 archive 中超过 30 天的文件
- 阶段结束后，`rules.json` 只能保留 pending

### 阶段二：错误回顾
- 读取当天 daily memory
- 回溯过去 24 小时可访问的对话与记录
- 重点扫描：重复要求换措辞、语气变化、任务中途放弃、输出被忽略
- 遗漏错误补录到 `ERRORS.md` 与当天 daily memory，标注 `review_discovered`
- 如果同类错误达到 3 次以上，提炼为新规则，`source=error_pattern`
- 如果复盘中直接发现潜在规则，但并非错误累计触发，则新规则 `source=review`

### 阶段三：规则审核
- 审核所有 pending 规则
- 采纳：写入目标文件，补 `reviewed_at`、`review_note`，标记为 `integrated`，立即归档
- 拒绝：补 `reviewed_at`、`review_note`，标记为 `rejected`，立即归档
- 需修改：先改 `content` 或 `target_files`，再决定采纳或拒绝
- 一旦规则不再是 pending，就必须立即归档

### 阶段四：每日进化摘要
写入当天 daily memory，至少包含：
- 今日新增错误数，区分实时与补录
- pending 规则审核结果
- 新写入 `MEMORY.md`、`AGENTS.md`、`LEARNINGS.md` 的条数
- 高频错误模式提醒
- 信息流覆盖情况
- 若有过期未审核规则，醒目标注

## 建制后接管 `AGENTS.md`

首次完成以下任一动作后，必须立即检查并更新当前 workspace 的 `AGENTS.md`：
- 初始化最小目录骨架
- 启用 `.learnings/pending/`
- 启用自我进化机制
- 从旧结构迁移到五层结构

### 接管步骤

1. 读取当前 `AGENTS.md`
2. 判断它是否已经覆盖运行层最小规则
3. 如果要修改，先创建备份文件 `AGENTS.backup-YYYYMMDD-HHMM.md`
4. 再更新 `AGENTS.md`
5. 更新完成后再次检查：仅依赖新的 `AGENTS.md`，后续会话是否仍能按新架构运行

### 运行层最小规则

更新后的 `AGENTS.md` 至少要接住：
- 会话启动顺序
- 最小检索顺序
- 写入边界
- 定时任务发现的候选规则先进 `.learnings/pending/rules.json`
- `daily-review` 是候选规则晋升闸门
- 关键改动前先给方案并等用户确认
- 长任务主动汇报
- 有 Git 就提交，无 Git 不阻塞
- daily memory 先读今天 `memory/YYYY-MM-DD.md` 再读昨天，不存在必须明确说明
- 高频易错任务执行前先检查 `.learnings/ERRORS.md`、`LEARNINGS.md`、`pending/rules.json`
- 任务结束后判断是否需要写回错误、经验、资料或候选规则
- 不要把外部资料直接写进核心文件，先征得用户同意
- 写入目标子目录不存在时先创建再写入

### 更新原则

- 先备份，再更新
- 保留人格、协作习惯和安全边界
- 不要把本 skill 的完整机制全文复制进 `AGENTS.md`
- 只写运行时必需规则
- 不要无备份直接覆盖旧文档

## 初始化建议

首次接管 workspace 时，除创建目录骨架外，还应准备：

### `.learnings/pending/rules.json`

```json
{
  "version": "YYYY-MM-DD",
  "rules": []
}
```

### `.learnings/pending/info-sources.json`

```json
{
  "version": "YYYY-MM-DD",
  "sources": []
}
```

单条 source 条目结构：

```json
{
  "name": "信息源名称",
  "instructions": "用自然语言描述如何获取该信息源的内容",
  "enabled": true,
  "focus": "与当前职责相关的关注点描述",
  "added_at": "ISO 8601 带时区时间"
}
```

字段说明：
- `name`：人类可读的信息源名称
- `instructions`：获取指令，用自然语言描述如何获取内容（可以是联网搜索、访问特定网页、调用其他技能等）
- `enabled`：是否启用，`daily-info-update` 只处理 `enabled=true` 的条目
- `focus`：该信息源中需要重点关注的内容方向
- `added_at`：添加时间

示例：

```json
{
  "version": "2026-03-11",
  "sources": [
    {
      "name": "OpenClaw changelog",
      "instructions": "访问 https://github.com/nichochar/openclaw/releases 页面，提取最近 3 天的 release notes",
      "enabled": true,
      "focus": "新版本中影响 skill 或 cron 行为的变更",
      "added_at": "2026-03-11T20:00:00+08:00"
    }
  ]
}
```

如果 `info-sources.json` 为空：
- `daily-info-update` 应直接跳过
- 并在当天 daily memory 记录“信息源为空”

## 建制验收标准

建制完成后，至少同时满足：
- 目录和最小文件已建立
- OpenClaw 的 `daily-info-update` 已存在且配置正确
- OpenClaw 的 `daily-review` 已存在且配置正确
- 这两个任务的 `agent` 都绑定到当前智能体自己
- 没有通过修改或改绑其他智能体的同名任务来冒充完成建制
- `AGENTS.md` 已接住运行层最小规则
- 如果下一次会话不再触发本 skill，仅依赖新的 `AGENTS.md`，当前 agent 仍然能按新架构运行

## 常见错误

### 错误一
把定时任务发现的候选规则直接写进 `AGENTS.md` 或 `MEMORY.md`。

修正：
- 先写 `.learnings/pending/rules.json`
- 只能由 `daily-review` 审核后再晋升

### 错误二
把 `review` 与 `error_pattern` 混成同一种 source。

修正：
- 错误累计触发 → `error_pattern`
- 复盘中直接判断发现 → `review`

### 错误三
把 `integrated` 或 `rejected` 留在 `rules.json`。

修正：
- `rules.json` 只保留 pending
- 其他状态立即归档

### 错误四
让 `daily-info-update` 写太多模糊候选。

修正：
- 每日最多 3 条
- 模糊内容直接丢弃

### 错误五
建制完成后没有更新 `AGENTS.md`。

修正：
- 建制后必须接管运行层
- 先备份 `AGENTS.md`
- 再把新架构运行规则写回主文档

### 错误六
启用自我进化机制后没有创建 `daily-info-update` 或 `daily-review`。

修正：
- 建制时必须检查这两个固定名称的 OpenClaw cron
- 不存在则创建
- 存在则核对配置与 agent 绑定，不要跳过

### 错误七
看到同名任务已存在，就直接修改或改绑了其他智能体的任务。

修正：
- 同名不等于属于当前智能体
- 如果同名任务绑定到其他智能体，应视为当前智能体自己的任务不存在
- 直接为当前智能体新建自己的任务，不要接管别人的任务
