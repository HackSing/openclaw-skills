"""
推特 Processor 节点 — LLM 提炼引擎

读取 pending_tweets.json，调用 LLM 生成技术锐评，输出到 drafts.json。

配置方式（环境变量）：
  LLM_API_KEY     - API 密钥（必须）
  LLM_BASE_URL    - API 端点（默认 https://api.openai.com/v1）
  LLM_MODEL       - 模型名称（默认 gpt-4o-mini）
"""

import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # 技能根目录（scripts/ 的上级）
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
PENDING_FILE = os.path.join(DATA_DIR, "pending_tweets.json")
DRAFTS_FILE = os.path.join(DATA_DIR, "drafts.json")

def get_system_prompt():
    """从同级目录的 prompt.txt 读取系统 Prompt"""
    prompt_path = os.path.join(BASE_DIR, "prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    print("⚠ 警告：未找到 prompt.txt，降级使用内建精简模式", file=sys.stderr)
    return "你是一个犀利的技术评论家，请将输入的推文提炼成250字以内的带有个人观点的推特贴文，使用中文输出。"

SYSTEM_PROMPT = get_system_prompt()


def get_llm_client():
    """构建 LLM API 请求配置"""
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("✗ 未设置 LLM_API_KEY 环境变量", file=sys.stderr)
        print("  请设置: $env:LLM_API_KEY = 'your-api-key'", file=sys.stderr)
        return None

    return {
        "api_key": api_key,
        "base_url": os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    }


def call_llm(config, user_content):
    """调用 OpenAI 兼容 API"""
    import requests

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(
            f"{config['base_url']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  LLM 调用失败: {e}", file=sys.stderr)
        return None


def build_prompt(tweet):
    """将推文数据组装为 LLM 输入"""
    content = tweet.get("content", {})
    tweet_type = tweet.get("type", "tweet")

    parts = []
    author = content.get("author", "未知")
    username = content.get("username", "")
    parts.append(f"作者: {author} (@{username})")

    if tweet_type == "article":
        title = content.get("title", "")
        full_text = content.get("full_text", "") or content.get("preview", "")
        parts.append(f"标题: {title}")
        parts.append(f"正文:\n{full_text[:2000]}")
    else:
        text = content.get("text", "")
        parts.append(f"内容:\n{text}")

    # 附加互动数据作为参考
    likes = content.get("likes", 0)
    retweets = content.get("retweets", 0)
    if likes or retweets:
        parts.append(f"互动: {likes} 赞 / {retweets} 转发")

    return "\n".join(parts)


def truncate_text(text, max_chars=280):
    """强制截断至指定字符数"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + "…"


def process():
    """
    核心处理逻辑：
    1. 读取 pending_tweets.json
    2. 逐条调用 LLM 生成锐评
    3. 输出到 drafts.json
    
    返回：成功生成的草稿数量
    """
    if not os.path.exists(PENDING_FILE):
        print("⚠ 没有待处理推文，请先运行 watcher.py", file=sys.stderr)
        return 0

    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        pending = json.load(f)

    if not pending:
        print("⚠ pending_tweets.json 为空", file=sys.stderr)
        return 0

    config = get_llm_client()
    if not config:
        return 0

    # 加载已有草稿
    existing_drafts = []
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
            try:
                existing_drafts = json.load(f)
            except json.JSONDecodeError:
                existing_drafts = []

    new_drafts = []
    success = 0
    failed = 0

    print(f"🧠 开始提炼，共 {len(pending)} 条待处理...")

    for i, tweet in enumerate(pending, 1):
        tweet_id = tweet.get("tweet_id", "?")
        content = tweet.get("content", {})
        author = content.get("author", "未知")

        print(f"  [{i}/{len(pending)}] @{content.get('username', '?')} - ", end="")

        prompt = build_prompt(tweet)
        commentary = call_llm(config, prompt)

        if commentary:
            commentary = truncate_text(commentary)
            draft = {
                "tweet_id": tweet_id,
                "original_url": tweet.get("original_url", ""),
                "original_author": author,
                "original_username": content.get("username", ""),
                "original_text": content.get("text", "") or content.get("title", ""),
                "commentary": commentary,
                "char_count": len(commentary),
                "generated_at": datetime.now().isoformat(),
                "status": "pending_review",  # pending_review / approved / rejected
            }
            new_drafts.append(draft)
            success += 1
            print(f"✓ ({len(commentary)} 字)")
        else:
            failed += 1
            print("✗")

    # 保存草稿
    all_drafts = existing_drafts + new_drafts
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_drafts, f, ensure_ascii=False, indent=2)

    # 清空已处理的 pending
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

    print(f"\n📝 提炼完成: 成功 {success} | 失败 {failed}")
    print(f"   草稿队列: {len(all_drafts)} 条 → {DRAFTS_FILE}")

    return success


if __name__ == "__main__":
    process()
