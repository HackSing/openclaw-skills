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
- 先检查是否存在
- 不存在则创建
- 已存在则核对调度、时区、会话目标、delivery 与消息内容是否符合约定
- 如果只有文案不完整，优先修正文案，不轻易改动整体机制
- 不要重复创建同名任务

固定约定：

### `daily-info-update`
- 名称：`daily-info-update`
- 调度：`0 22 * * *`
- 时区：`Asia/Shanghai`
- 会话：`isolated`
- delivery：`none`
- 作用：信息流更新，只产出 pending 规则，不直接写核心文件

### `daily-review`
- 名称：`daily-review`
- 调度：`0 23 * * *`
- 时区：`Asia/Shanghai`
- 会话：`isolated`
- delivery：`none`
- 作用：清理、补录、审核、归档和每日进化摘要，是候选规则的唯一晋升闸门

## `daily-info-update`

推荐调度：
- 每天 22:00
- 时区 `Asia/Shanghai`
- 隔离会话执行

职责：
1. 读取 `.learnings/pending/info-sources.json`
2. 只处理 `enabled=true` 的信息源
3. 检查今日新内容
4. 只把高相关、能改变行为、目标文件明确的内容写成 pending 规则
5. 每日新增规则不超过 3 条
6. 完成后在当天 daily memory 写摘要

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

如果 `info-sources.json` 为空：
- `daily-info-update` 应直接跳过
- 并在当天 daily memory 记录“信息源为空”

## 建制验收标准

建制完成后，至少同时满足：
- 目录和最小文件已建立
- `daily-info-update` 已存在且配置正确
- `daily-review` 已存在且配置正确
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
- 建制时必须检查这两个固定名称的 cron
- 不存在则创建
- 存在则核对配置，不要跳过
