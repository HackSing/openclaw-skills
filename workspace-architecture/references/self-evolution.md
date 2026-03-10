# 自我进化机制

## 目标

把两类学习来源分开治理：

1. 用户当场纠正触发的实时学习
2. 定时任务自己发现的候选规则

前者可信度高，可沿既有通道直接记录。后者必须先经过 pending 缓冲与 review 审核，不能直接污染核心规则。

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
- `daily-info-update` 发现新规则候选
- `daily-review` 复盘时发现潜在规则
- `ERRORS.md` 中同类错误累计达到阈值后提炼出的规则

硬规则：
- 不得直接写入 `MEMORY.md` 或 `AGENTS.md`
- 必须先写进 `pending/rules.json`
- 只能由 `daily-review` 审核后决定是否晋升

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
  - 来自每日信息流更新
- `review`
  - 来自每日回顾中的直接复盘判断
  - 不是错误累计触发，而是复盘时直接发现的潜在规则
- `error_pattern`
  - 来自同类错误累计后的规则提炼

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
- `rules.json` 永远只保留 `pending`
- 一旦某条规则变成 `integrated`、`rejected`、`expired`
- 必须在同次 review 中立即移入 `archive/rules_YYYY-MM-DD.json`
- 不允许这些状态残留在 `rules.json`

过期机制：
- `pending` 超过 7 天仍未审核 → 标记为 `expired`
- 填写 `reviewed_at` 和 `review_note`
- 立即移入 archive

archive 清理：
- archive 文件默认保留 30 天
- 超过 30 天自动删除

## daily-info-update

推荐调度：
- 每天 22:00
- 时区 `Asia/Shanghai`
- 隔离会话执行

职责：
1. 读取 `pending/info-sources.json`
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

## daily-review

推荐调度：
- 每天 23:00
- 时区 `Asia/Shanghai`
- 隔离会话执行

四个阶段：

### 阶段一：清理
- 读取 `rules.json`
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

## 初始化建议

首次接管 workspace 时，除创建目录骨架外，还应准备：

### rules.json

```json
{
  "version": "YYYY-MM-DD",
  "rules": []
}
```

### info-sources.json

```json
{
  "version": "YYYY-MM-DD",
  "sources": []
}
```

如果 `info-sources.json` 为空：
- `daily-info-update` 应直接跳过
- 并在当天 daily memory 记录“信息源为空”

## 常见错误

### 错误一
把定时任务发现的候选规则直接写进 `AGENTS.md` 或 `MEMORY.md`。

修正：
- 先写 `pending/rules.json`
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
只建了 cron，没有把机制写回 skill。

修正：
- 必须把 schema、状态机、职责边界和审核链路写入 skill 与 references
- 否则新 agent 无法稳定复现
