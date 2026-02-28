"""
推特 Watcher 节点 — 信源巡逻与防重缓存

使用方式：
  1. 手动模式：将推文 URL 写入 input_urls.txt（每行一个），运行脚本自动抓取
  2. 程序调用：调用 watch() 函数，传入 URL 列表

输出：pending_tweets.json（洗净的新推文列表，供 Processor 消费）
"""

import json
import os
import sys
from datetime import datetime
from fetcher import get_tweet

# 文件路径常量
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_IDS_FILE = os.path.join(BASE_DIR, "seen_ids.json")
INPUT_URLS_FILE = os.path.join(BASE_DIR, "input_urls.txt")
PENDING_FILE = os.path.join(BASE_DIR, "pending_tweets.json")


def load_seen_ids():
    """加载已读推文 ID 集合"""
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_ids(seen_ids):
    """持久化已读推文 ID"""
    with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ids), f, ensure_ascii=False, indent=2)


def load_input_urls():
    """从 input_urls.txt 读取待抓取的 URL 列表"""
    if not os.path.exists(INPUT_URLS_FILE):
        return []
    with open(INPUT_URLS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return urls


def extract_id_from_url(url):
    """从 URL 中提取推文 ID（复用 fetcher 的逻辑）"""
    from fetcher import extract_tweet_id
    return extract_tweet_id(url)


def watch(urls=None):
    """
    核心巡逻逻辑：
    1. 接收 URL 列表（默认从 input_urls.txt 读取）
    2. 过滤已读 ID
    3. 逐条抓取新推文
    4. 输出到 pending_tweets.json
    
    返回：新抓取的推文数量
    """
    if urls is None:
        urls = load_input_urls()

    if not urls:
        print("⚠ 没有待处理的 URL，请在 input_urls.txt 中添加推文链接", file=sys.stderr)
        return 0

    seen_ids = load_seen_ids()
    new_tweets = []
    skipped = 0
    failed = 0

    print(f"📡 开始巡逻，共 {len(urls)} 条 URL...")

    for i, url in enumerate(urls, 1):
        tweet_id = extract_id_from_url(url)
        if not tweet_id:
            print(f"  [{i}/{len(urls)}] ✗ 无法解析 ID: {url}")
            failed += 1
            continue

        if tweet_id in seen_ids:
            print(f"  [{i}/{len(urls)}] → 已读跳过: {tweet_id}")
            skipped += 1
            continue

        print(f"  [{i}/{len(urls)}] 抓取中: {tweet_id}...", end=" ")
        result = get_tweet(url)

        if result.get("success"):
            result["tweet_id"] = tweet_id
            result["original_url"] = url
            result["fetched_at"] = datetime.now().isoformat()
            new_tweets.append(result)
            seen_ids.add(tweet_id)
            print("✓")
        else:
            print(f"✗ {result.get('error', '未知错误')}")
            failed += 1

    # 持久化结果
    save_seen_ids(seen_ids)

    # 追加模式：如果 pending 文件已有内容，合并进去
    existing = []
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

    all_pending = existing + new_tweets
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(all_pending, f, ensure_ascii=False, indent=2)

    print(f"\n📊 巡逻完成: 新增 {len(new_tweets)} | 跳过 {skipped} | 失败 {failed}")
    print(f"   待处理队列: {len(all_pending)} 条 → {PENDING_FILE}")

    return len(new_tweets)


if __name__ == "__main__":
    # 支持命令行直接传入 URL
    if len(sys.argv) > 1:
        watch(sys.argv[1:])
    else:
        watch()
