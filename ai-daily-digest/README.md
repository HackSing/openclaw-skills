# AI Daily Digest

skill 制作详情可查看 ➡️ https://mp.weixin.qq.com/s/rkQ28KTZs5QeZqjwSCvR4Q

支持多角色的 AI 每日精选日报生成器。不同角色拥有不同的信息源、评分标准和输出风格，通过 AI 多维评分筛选，生成一份结构化的每日精选日报。

![AI Daily Digest 概览](assets/overview.png)

## 多角色支持

| 角色 ID | 名称 | 信息源数 | 说明 |
|---------|------|---------|------|
| `tech-blogger` | 技术博主 | 90 | Karpathy 推荐的 HN 顶级技术博客（默认） |
| `ai-pm` | AI 产品经理 | 13 | AI 产品动态、开源项目和产品策略 |
| `programmer` | 程序员 | 15 | 工程博客、代码质量、工具和系统架构 |
| `trader` | 交易员 | 10 | 金融新闻、Fintech 动态和市场分析 |

每个角色定义在 `roles/<role-id>.json` 中，包含独立的 RSS 源、分类体系、评分标准和输出品牌。

## 使用方式

作为 OpenCode Skill 使用，在对话中输入 `/digest` 即可启动交互式引导流程：

```
/digest
```

Agent 会依次询问：

| 参数 | 选项 | 默认值 |
|------|------|--------|
| 角色 | 技术博主 / AI 产品经理 / 程序员 / 交易员 / 自定义 | 技术博主 |
| 时间范围 | 24h / 48h / 72h / 7天 | 48h |
| 精选数量 | 10 / 15 / 20 篇 | 15 篇 |
| 输出语言 | 中文 / English | 中文 |
| AI API Key | 手动输入（首次需要，之后自动记忆） | — |

配置会自动保存到 `~/.hn-daily-digest/config.json`，下次运行可一键复用（按角色独立保存偏好）。

### 直接命令行运行

```bash
export GEMINI_API_KEY="your-key"
export OPENAI_API_KEY="your-openai-compatible-key"  # 可选，Gemini 失败时兜底
export OPENAI_API_BASE="https://api.deepseek.com/v1" # 可选
export OPENAI_MODEL="deepseek-chat"                  # 可选

# 默认角色（技术博主）
npx -y bun scripts/digest.ts --hours 48 --top-n 15 --lang zh

# 指定角色
npx -y bun scripts/digest.ts --role ai-pm --hours 24 --top-n 10 --lang zh
npx -y bun scripts/digest.ts --role programmer --hours 48 --top-n 15
npx -y bun scripts/digest.ts --role trader --hours 24 --top-n 10

# 查看所有可用角色
npx -y bun scripts/digest.ts --list-roles
```

## 功能

### 五步处理流水线

```
RSS 抓取 → 时间过滤 → AI 评分+分类 → AI 摘要+翻译 → 趋势总结
```

1. **RSS 抓取** — 并发抓取角色定义的所有源（10 路并发，15s 超时），兼容 RSS 2.0 和 Atom 格式
2. **时间过滤** — 按指定时间窗口筛选近期文章
3. **AI 评分** — AI 基于角色的评分标准从相关性、质量、时效性三个维度打分（1-10），同时完成分类和关键词提取
4. **AI 摘要** — 为 Top N 文章生成结构化摘要、中文标题翻译、推荐理由
5. **趋势总结** — AI 归纳当日领域内的宏观趋势

### 日报结构

| 板块 | 内容 |
|------|------|
| 📝 今日看点 | 3-5 句话的宏观趋势总结（基于角色领域） |
| 🏆 今日必读 | Top 3 深度展示：中英双语标题、摘要、推荐理由、关键词 |
| 📊 数据概览 | 统计表格 + Mermaid 饼图 + Mermaid 柱状图 + ASCII 纯文本图 + 话题标签云 |
| 分类文章列表 | 按角色定义的分类分组，每篇含中文标题、来源、评分、摘要、关键词 |

## 自定义角色

创建自定义角色只需 3 步：

1. 复制 `roles/` 目录下任意角色文件作为模板
2. 修改 `id`、`name`、`feeds`（仅 3 个必填字段）
3. 可选调整 `categories`、`scoring`、`branding`

### 最小角色文件

```json
{
  "id": "my-role",
  "name": "我的角色",
  "feeds": [
    { "name": "示例博客", "xmlUrl": "https://example.com/rss", "htmlUrl": "https://example.com" }
  ]
}
```

### 完整角色文件结构

```json
{
  "id": "my-role",
  "name": "我的角色",
  "description": "角色描述，用于选择 UI 展示",
  "feeds": [
    { "name": "博客名", "xmlUrl": "RSS 地址", "htmlUrl": "博客首页" }
  ],
  "categories": {
    "cat-id": { "emoji": "🔥", "label": "分类名" },
    "other":  { "emoji": "📝", "label": "其他" }
  },
  "scoring": {
    "persona": "你正在为一位 XXX 筛选文章",
    "relevanceDescription": "对 XXX 的价值",
    "relevanceLevels": {
      "high": "高相关性描述",
      "medium": "中相关性描述",
      "low": "低相关性描述"
    }
  },
  "branding": {
    "title": "日报标题",
    "subtitle": "日报副标题",
    "highlightsLabel": "今日 XX 圈动态",
    "footer": "自定义页脚"
  }
}
```

省略的可选字段会使用默认值（tech-blogger 的分类和评分标准）。

## 亮点

- **多角色支持** — 4 个预置角色 + 自定义角色，一套引擎服务不同职业
- **零依赖** — 纯 TypeScript 单文件，无第三方库，基于 Bun 运行时
- **中英双语** — 所有标题自动翻译为中文，原文保留为链接
- **结构化摘要** — 4-6 句完整概述，30 秒判断是否值得读
- **可视化统计** — Mermaid 图表 + ASCII 柱状图 + 标签云
- **智能分类** — AI 自动归类，按角色定义的分类体系组织
- **配置记忆** — 按角色独立保存偏好，一键复用

## 环境要求

- [Bun](https://bun.sh) 运行时（通过 `npx -y bun` 自动安装）
- 至少一个可用的 AI API Key：
  - `GEMINI_API_KEY`（[免费获取](https://aistudio.google.com/apikey)）
  - 或 `OPENAI_API_KEY`（可配合 `OPENAI_API_BASE` 使用 DeepSeek / OpenAI 等兼容服务）
- 网络连接

## 信息源

默认角色的 90 个 RSS 源精选自 [Hacker News Popularity Contest 2025](https://refactoringenglish.com/tools/hn-popularity/)，由 [Andrej Karpathy](https://x.com/karpathy) 推荐。

其他角色的信息源定义在各自的 `roles/<role-id>.json` 文件中。完整列表可通过 `--list-roles` 查看。
