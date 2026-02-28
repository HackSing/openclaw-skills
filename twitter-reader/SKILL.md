---
name: twitter-reader
description: 推特内容抓取与自动化运营技能。支持实时读取单条推文内容，也支持定时批量巡逻、LLM 提炼和审阅推送。
---

# Twitter Reader 技能

该技能封装了 Twitter 内容抓取与自动化监控工作流。提供两种使用模式：
- **交互模式**：智能体实时抓取单条推文，在对话中阅读、讨论或生成回复。
- **管线模式**：后台批量巡逻信源，LLM 提炼后推送审阅。

## 依赖

```bash
pip install requests
```

## 配置文件

| 文件 | 用途 |
|------|------|
| `prompt.txt` | Processor 节点的 LLM 系统提示词 |
| `sources.json` | 关注的推特账号列表及抓取间隔（用于管线模式） |
| `input_urls.txt` | 手动输入的推文 URL 列表（每行一个，`#` 开头为注释） |
| `seen_ids.json` | 已读推文 ID 缓存（防重，仅管线模式写入） |
| `pending_tweets.json` | Watcher 输出的待处理队列 |
| `drafts.json` | Processor 输出的 LLM 提炼草稿 |
| `archive.json` | 已归档的历史记录 |

### 环境变量（仅管线模式的 Processor 节点需要）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | LLM API 密钥（必须） | 无 |
| `LLM_BASE_URL` | API 端点 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-4o-mini` |

---

## 模式一：智能体交互式调用（推荐）

当用户发来一条推特链接，要求你"阅读内容并讨论"或"生成高质量回复"时，**请直接调用底层的 `fetcher.py`，不要使用 `run_pipeline.py`**。

`run_pipeline.py` 会触发防重缓存、LLM 定式提炼和浏览器弹窗，不适合交互场景。

### 调用示例

```python
import sys

skill_dir = r"d:\AIWareTop\Agent\openclaw-skills\twitter-reader"
if skill_dir not in sys.path:
    sys.path.append(skill_dir)

from fetcher import get_tweet

result = get_tweet("用户提供的推特链接")

if result.get("success"):
    content = result["content"]
    # 现在你可以基于 content 与用户讨论，或生成回复
```

### `get_tweet()` 返回值结构

```json
{
  "source": "fxtwitter",
  "success": true,
  "type": "tweet",
  "content": {
    "text": "推文正文",
    "author": "作者显示名",
    "username": "作者用户名",
    "created_at": "发布时间",
    "likes": 123,
    "retweets": 45,
    "views": 6789,
    "replies": 10,
    "media": ["图片URL1", "图片URL2"]
  }
}
```

当 `type` 为 `"article"`（X 长文章）时，`content` 额外包含：
- `title`：文章标题
- `preview`：预览文本
- `full_text`：完整正文（Markdown 格式）
- `cover_image`：封面图 URL

此调用完全无状态，不写入任何缓存文件，不触发通知服务。

---

## 模式二：后台管线批量运营

通过 `run_pipeline.py` 串联 Watcher → Processor → Action 三节点，适用于定时任务或批量处理。

### 三大节点

1. **Watcher 巡逻抓取** (`watcher.py`)
   - 读取 `input_urls.txt` 或 `sources.json`，通过 `seen_ids.json` 去重，新推文写入 `pending_tweets.json`。

2. **Processor LLM 提炼** (`processor.py`)
   - 读取 `pending_tweets.json`，调用 LLM 生成锐评，输出到 `drafts.json`。
   - 需要设置 `LLM_API_KEY` 环境变量。

3. **Action 通知审阅** (`notifier.py`)
   - 启动本地 HTTP 审阅服务（端口 18923），弹出浏览器页面，支持通过/驳回/重写/归档操作。

### 命令行示例

```bash
# 完整管线
python run_pipeline.py

# 指定 URL
python run_pipeline.py https://x.com/elonmusk/status/123456

# 单节点执行
python run_pipeline.py --watch-only
python run_pipeline.py --process-only
python run_pipeline.py --notify-only
```

