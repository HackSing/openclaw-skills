---
name: healthmanager
description: Health check, security audit, and scheduled risk patrol for OpenClaw hosts. Use when the user wants a host safety report, OpenClaw runtime risk review, firewall or port exposure check, file permission audit, login review, version status summary, or a recurring daily health check. When the user wants continuous monitoring, create or update a scheduled task that runs every day at 08:00 by default and reports the result back to the user.
---

# HealthManager

## 概览

执行 OpenClaw 所在主机的健康检查与安全巡检，并输出统一格式的风险报告。

默认支持两种模式：
- 单次检查
- 托管巡检。首次启用托管巡检时，默认创建一个每天 08:00 执行的定时任务

本技能的产品名使用 `HealthManager`。目录名与包名使用小写 `healthmanager`。

## 核心能力

### 1. 单次健康检查

当用户要求检查当前机器风险、OpenClaw 部署状态、安全情况、端口暴露、防火墙、权限或登录记录时，执行一次完整巡检并直接给出结果。

### 2. 托管巡检

当用户要求“每天检查”“定时检查”“每天 8 点跑一次”“持续巡检”时：
- 优先创建或更新定时任务
- 默认时间设为每天 08:00
- 默认检查内容聚焦安全与健康状态
- 任务完成后直接给用户发送结果，不要只留内部记录

### 3. 巡检任务管理

当用户要求修改时间、暂停、恢复、手动执行时：
- 先查现有任务
- 优先更新已有任务，不重复创建多个含义相同的任务
- 若必须替换旧任务，明确说明原因

## 标准工作流

### 步骤 1：判断是单次检查还是托管巡检

按用户意图分流：
- 只看一次报告 → 单次检查
- 希望每天自动跑 → 托管巡检
- 已有任务但要改时间或改内容 → 巡检任务管理

### 步骤 2：确定输出模式

默认支持两种模式：
- `summary`
- `full`

选择规则：
- 定时任务默认使用 `summary`
- 用户明确要求“详细报告”“完整巡检”“完整清单”时使用 `full`
- 首次排障、首次审计、需要留底时优先 `full`

### 步骤 3：执行巡检

巡检至少覆盖这些项目：
- OpenClaw 安全审计
- 版本状态
- 防火墙状态
- 监听端口
- 关键文件权限
- 最近登录记录
- 风险分级
- 今日优先处理建议

如果某项无法检查，明确写“未检查到”或“当前环境不适用”，不要假装成功。

### 步骤 4：输出统一格式报告

详细格式见 `references/report-format.md`。
风险分级标准见 `references/risk-levels.md`。
检查范围说明见 `references/host-checklist.md`。
常见问题口径见 `references/common-findings.md`。

## 定时任务规则

### 默认任务名

优先使用统一任务名：
- `healthmanager-daily-check`

如果环境里已经有等价任务，例如旧的安全巡检任务：
- 优先更新原任务而不是重复创建
- 保持任务数量最少
- 明确最终由哪个 agent 执行、回传到哪里

### 默认调度

默认每天 08:00 执行一次。

如果用户没有指定时区，按当前环境时区处理。
如果用户指定了其他时间，以用户要求为准。

### 默认检查目标

默认聚焦：
- 安全状态
- OpenClaw 运行健康
- 风险变化

不要默认塞进无关提醒、待办链接或外部文档链接。

## 启用托管巡检的固定流程

当用户明确启用 HealthManager 的每日巡检时，必须按以下顺序处理：

1. 先检查是否已存在同类巡检任务
2. 若已存在，优先更新原任务，不重复创建
3. 若不存在，创建 `healthmanager-daily-check`
4. 默认调度设为每天 08:00
5. 绑定当前用户或当前会话作为回传目标
6. 明确报告默认使用 `summary`
7. 创建或更新后，立即说明：
   - 最终任务名
   - 执行时间
   - 执行者
   - 回传目标
8. 如果环境允许，补一次手动验证或明确下次触发时间

如果用户只要求看一次报告，不要默认创建定时任务。

## 输出与沟通规则

- 使用直接、简洁、可执行的语言
- 不要把内部日志、原始系统事件、运行统计原样转发给用户
- 当结果来自定时任务时，用正常助手口吻重写后再发
- 如果只有一个最重要的问题，明确告诉用户今天先处理哪一个
- `summary` 模式优先短、准、可执行
- `full` 模式优先完整、结构化、可留档

## 任务变更规则

涉及定时任务创建、修改、替换、停用时：
- 如果用户已明确授权，例如“直接产出”“直接创建”“按这个默认时间做”，可以直接执行
- 如果会影响现有任务归属、回传目标或重复汇报，应先说明将如何处理旧任务
- 优先避免产生多个重复的每日巡检任务

## 推荐触发语句

### 单次检查
- 帮我检查这台 OpenClaw 机器的安全状态
- 给我一份主机健康报告
- 看看当前部署有没有风险

### 启用托管巡检
- 启用 HealthManager，每天早上 8 点巡检
- 帮我开启每日健康检查
- 以后每天自动给我发安全状态

### 巡检任务管理
- 把 HealthManager 改成早上 9 点
- 暂停 HealthManager
- 恢复 HealthManager
- 现在手动跑一次 HealthManager

## v0.3 Roadmap

后续版本优先沿下面三个方向继续补强：

### 1. 环境分流
按部署环境提供更贴合的巡检重点，例如：
- 个人电脑
- Mac mini
- 工作站
- 树莓派
- VPS

目标是让 HealthManager 在不同运行场景下，自动更关注真正有差异的风险点，而不是所有环境都套同一份检查口径。

### 2. 触发示例增强
补充更完整的用户触发语句和调用样例，覆盖：
- 单次检查
- 启用每日巡检
- 修改执行时间
- 暂停与恢复
- 手动执行一次

目标是让其他智能体和终端用户更容易正确触发 HealthManager，而不是依赖猜测。

### 3. 托管巡检验证说明
补充“创建或更新定时任务后如何验证”的固定说明，包括：
- 如何确认任务已创建
- 如何确认调度时间正确
- 如何确认回传目标正确
- 如何做一次手动验证或等待下一次触发

目标是减少托管巡检模式下的重复任务、错绑回传目标和看似创建成功但实际未生效的问题。

## 参考资料

按需读取：
- `references/report-format.md`：报告固定结构与双模式写法
- `references/risk-levels.md`：风险分级口径
- `references/host-checklist.md`：巡检覆盖项与边界
- `references/common-findings.md`：常见风险项库与建议口径
