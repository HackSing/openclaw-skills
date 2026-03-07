"""
推特 Action 节点 — 审阅服务器

启动本地 HTTP 服务，提供：
  1. 可视化审阅页面（通过/驳回/复制）
  2. POST /api/review — 回写审阅状态到 drafts.json
  3. POST /api/regenerate — 对驳回项重新调用 LLM 生成锐评
  4. GET /api/drafts — 获取当前草稿数据
"""

import json
import os
import sys
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRAFTS_FILE = os.path.join(BASE_DIR, "drafts.json")
ARCHIVE_FILE = os.path.join(BASE_DIR, "archive.json")
SERVER_PORT = 18923


def load_drafts():
    if not os.path.exists(DRAFTS_FILE):
        return []
    with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_drafts(drafts):
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(drafts, f, ensure_ascii=False, indent=2)


def regenerate_commentary(draft):
    """对单条草稿重新调用 LLM 生成锐评"""
    from processor import get_llm_client, call_llm, build_prompt, truncate_text

    config = get_llm_client()
    if not config:
        return None

    # 构造一个与 pending 格式兼容的结构
    fake_tweet = {
        "type": "tweet",
        "content": {
            "text": draft.get("original_text", ""),
            "author": draft.get("original_author", ""),
            "username": draft.get("original_username", ""),
        }
    }
    prompt = build_prompt(fake_tweet)
    commentary = call_llm(config, prompt)
    if commentary:
        return truncate_text(commentary)
    return None


class ReviewHandler(BaseHTTPRequestHandler):
    """处理审阅页面和 API 请求"""

    def log_message(self, format, *args):
        """静默日志，避免刷屏"""
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/" or path == "/index.html":
            self._serve_html()
        elif path == "/api/drafts":
            self._send_json(load_drafts())
        elif path == "/api/shutdown":
            self._send_json({"status": "shutting_down"})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/review":
            self._handle_review()
        elif path == "/api/regenerate":
            self._handle_regenerate()
        elif path == "/api/archive":
            self._handle_archive()
        else:
            self.send_error(404)

    def _handle_review(self):
        """处理审阅状态更新"""
        body = self._read_body()
        tweet_id = body.get("tweet_id")
        status = body.get("status")  # approved / rejected

        if not tweet_id or status not in ("approved", "rejected"):
            self._send_json({"error": "参数错误"}, 400)
            return

        drafts = load_drafts()
        updated = False
        for draft in drafts:
            if draft.get("tweet_id") == tweet_id:
                draft["status"] = status
                draft["reviewed_at"] = datetime.now().isoformat()
                updated = True
                break

        if updated:
            save_drafts(drafts)
            print(f"  📋 {tweet_id} → {status}")
            self._send_json({"success": True, "status": status})
        else:
            self._send_json({"error": "未找到该草稿"}, 404)

    def _handle_regenerate(self):
        """处理驳回后重新生成"""
        body = self._read_body()
        tweet_id = body.get("tweet_id")

        if not tweet_id:
            self._send_json({"error": "参数错误"}, 400)
            return

        drafts = load_drafts()
        target = None
        for draft in drafts:
            if draft.get("tweet_id") == tweet_id:
                target = draft
                break

        if not target:
            self._send_json({"error": "未找到该草稿"}, 404)
            return

        print(f"  🔄 重新生成 {tweet_id}...", end=" ")
        new_commentary = regenerate_commentary(target)

        if new_commentary:
            target["commentary"] = new_commentary
            target["char_count"] = len(new_commentary)
            target["status"] = "pending_review"
            target["generated_at"] = datetime.now().isoformat()
            target["regenerated"] = target.get("regenerated", 0) + 1
            save_drafts(drafts)
            print(f"✓ ({len(new_commentary)} 字)")
            self._send_json({
                "success": True,
                "commentary": new_commentary,
                "char_count": len(new_commentary),
            })
        else:
            print("✗")
            self._send_json({"error": "LLM 重新生成失败"}, 500)

    def _handle_archive(self):
        """归档已审阅的草稿"""
        drafts = load_drafts()
        to_archive = [d for d in drafts if d.get("status") in ("approved", "rejected")]
        remaining = [d for d in drafts if d.get("status") not in ("approved", "rejected")]

        if not to_archive:
            self._send_json({"error": "没有可归档的条目"}, 400)
            return

        # 追加到 archive.json
        existing_archive = []
        if os.path.exists(ARCHIVE_FILE):
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                try:
                    existing_archive = json.load(f)
                except json.JSONDecodeError:
                    existing_archive = []

        for item in to_archive:
            item["archived_at"] = datetime.now().isoformat()
        existing_archive.extend(to_archive)

        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_archive, f, ensure_ascii=False, indent=2)

        # 更新 drafts.json
        save_drafts(remaining)
        print(f"  🗂 已归档 {len(to_archive)} 条，剩余 {len(remaining)} 条")
        self._send_json({"success": True, "archived": len(to_archive), "remaining": len(remaining)})

    def _serve_html(self):
        """返回审阅页面 HTML"""
        html = generate_review_html()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def generate_review_html():
    """生成审阅台 HTML（从服务器动态加载数据）"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>推文锐评审阅台</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, 'Segoe UI', 'Microsoft YaHei', sans-serif;
      background: #0d1117; color: #c9d1d9; padding: 40px 20px;
    }
    .container { max-width: 720px; margin: 0 auto; }
    h1 { text-align: center; color: #58a6ff; margin-bottom: 8px; font-size: 24px; }
    .subtitle { text-align: center; color: #8b949e; margin-bottom: 32px; font-size: 14px; }
    .empty { text-align: center; color: #8b949e; padding: 60px 0; font-size: 16px; }
    .card {
      background: #161b22; border: 1px solid #30363d;
      border-radius: 12px; padding: 24px; margin-bottom: 20px;
      transition: all 0.3s;
    }
    .card:hover { border-color: #58a6ff; }
    .card.approved { border-color: #3fb950; opacity: 0.5; }
    .card.rejected { border-color: #f85149; }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .author { color: #58a6ff; font-weight: 600; }
    .badges { display: flex; gap: 8px; align-items: center; }
    .char-count { color: #8b949e; font-size: 13px; }
    .badge {
      font-size: 11px; padding: 2px 8px; border-radius: 10px;
      font-weight: 600; text-transform: uppercase;
    }
    .badge-regen { background: #1f1d2e; color: #d2a8ff; border: 1px solid #d2a8ff33; }
    .label {
      color: #8b949e; font-size: 12px; text-transform: uppercase;
      letter-spacing: 1px; margin-bottom: 6px;
    }
    .original {
      background: #0d1117; border-radius: 8px; padding: 14px; margin-bottom: 16px;
    }
    .original p { color: #8b949e; font-size: 14px; line-height: 1.6; }
    .link {
      color: #58a6ff; font-size: 13px; text-decoration: none;
      margin-top: 8px; display: inline-block;
    }
    .link:hover { text-decoration: underline; }
    .commentary p {
      font-size: 16px; line-height: 1.7; color: #f0f6fc; margin-bottom: 16px;
    }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; }
    .btn {
      padding: 8px 18px; border: 1px solid #30363d; border-radius: 8px;
      background: #21262d; color: #c9d1d9; cursor: pointer;
      font-size: 14px; transition: all 0.15s;
    }
    .btn:hover { background: #30363d; }
    .btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .btn-copy:hover { border-color: #58a6ff; color: #58a6ff; }
    .btn-approve:hover { border-color: #3fb950; color: #3fb950; }
    .btn-reject:hover { border-color: #f85149; color: #f85149; }
    .btn-regen { border-color: #d2a8ff44; }
    .btn-regen:hover { border-color: #d2a8ff; color: #d2a8ff; }
    .toolbar {
      display: flex; justify-content: flex-end; margin-bottom: 20px; gap: 10px;
    }
    .btn-archive {
      padding: 8px 20px; border: 1px solid #f0883e44; border-radius: 8px;
      background: #21262d; color: #f0883e; cursor: pointer;
      font-size: 14px; font-weight: 600; transition: all 0.15s;
    }
    .btn-archive:hover { background: #f0883e22; border-color: #f0883e; }
    .btn-archive:disabled { opacity: 0.4; cursor: not-allowed; }
    .spinner { display: inline-block; width: 14px; height: 14px;
      border: 2px solid #30363d; border-top-color: #d2a8ff;
      border-radius: 50%; animation: spin 0.6s linear infinite;
      vertical-align: middle; margin-right: 6px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .toast {
      position: fixed; bottom: 24px; right: 24px;
      background: #3fb950; color: #0d1117;
      padding: 12px 24px; border-radius: 8px;
      font-weight: 600; font-size: 14px;
      opacity: 0; transition: opacity 0.3s;
      pointer-events: none; z-index: 100;
    }
    .toast.show { opacity: 1; }
    .toast.error { background: #f85149; color: #fff; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔍 推文锐评审阅台</h1>
    <p class="subtitle" id="subtitle">加载中...</p>
    <div class="toolbar">
      <button class="btn-archive" id="archiveBtn" onclick="archiveAll()" disabled>🗂 归档已处理</button>
    </div>
    <div id="cards"></div>
  </div>
  <div class="toast" id="toast"></div>

<script>
const API = '';

function showToast(msg, isError) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => t.className = 'toast', 2500);
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

async function loadDrafts() {
  const resp = await fetch(API + '/api/drafts');
  const drafts = await resp.json();
  renderCards(drafts);
}

function renderCards(drafts) {
  const pendingReview = drafts.filter(d => d.status === 'pending_review');
  const reviewed = drafts.filter(d => d.status === 'approved' || d.status === 'rejected');
  document.getElementById('subtitle').textContent =
    `待审阅 ${pendingReview.length} 条 · 已处理 ${reviewed.length} 条`;
  document.getElementById('archiveBtn').disabled = reviewed.length === 0;

  const container = document.getElementById('cards');
  if (drafts.length === 0) {
    container.innerHTML = '<div class="empty">暂无草稿</div>';
    return;
  }

  container.innerHTML = drafts.map((d, i) => {
    const regenBadge = d.regenerated
      ? `<span class="badge badge-regen">已重写 ${d.regenerated} 次</span>` : '';
    const isApproved = d.status === 'approved';
    const isRejected = d.status === 'rejected';

    return `
    <div class="card ${d.status === 'approved' ? 'approved' : ''} ${d.status === 'rejected' ? 'rejected' : ''}" id="card-${i}" data-id="${d.tweet_id}">
      <div class="card-header">
        <span class="author">@${escapeHtml(d.original_username || '?')}</span>
        <div class="badges">
          ${regenBadge}
          <span class="char-count">${d.char_count || '?'} 字</span>
        </div>
      </div>
      <div class="original">
        <div class="label">原文摘要</div>
        <p>${escapeHtml((d.original_text || '').substring(0, 200))}</p>
        <a href="${d.original_url || '#'}" target="_blank" class="link">查看原推</a>
      </div>
      <div class="commentary">
        <div class="label">AI 锐评草稿</div>
        <p id="commentary-${i}">${escapeHtml(d.commentary || '')}</p>
      </div>
      <div class="actions">
        <button class="btn btn-copy" onclick="copyText(${i})" ${isApproved ? 'disabled' : ''}>📋 复制</button>
        <button class="btn btn-approve" onclick="review(${i}, 'approved')" ${isApproved ? 'disabled' : ''}>✓ 通过</button>
        <button class="btn btn-reject" onclick="review(${i}, 'rejected')" ${isApproved ? 'disabled' : ''}>✗ 驳回</button>
        <button class="btn btn-regen" onclick="regenerate(${i})" id="regen-${i}" ${isApproved ? 'disabled' : ''}>🔄 重写</button>
      </div>
    </div>`;
  }).join('');
}

async function copyText(index) {
  const el = document.getElementById('commentary-' + index);
  try {
    await navigator.clipboard.writeText(el.textContent);
    showToast('已复制到剪贴板');
  } catch(e) {
    showToast('复制失败', true);
  }
}

async function review(index, status) {
  const card = document.getElementById('card-' + index);
  const tweetId = card.dataset.id;

  const resp = await fetch(API + '/api/review', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({tweet_id: tweetId, status: status})
  });
  const data = await resp.json();

  if (data.success) {
    card.className = 'card ' + status;
    if (status === 'approved') {
      card.querySelectorAll('.btn').forEach(b => b.disabled = true);
      showToast('✓ 已通过，状态已保存');
    } else {
      showToast('✗ 已驳回，可点击"重写"重新生成');
    }
  } else {
    showToast(data.error || '操作失败', true);
  }
}

async function regenerate(index) {
  const card = document.getElementById('card-' + index);
  const tweetId = card.dataset.id;
  const btn = document.getElementById('regen-' + index);

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>重写中...';

  const resp = await fetch(API + '/api/regenerate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({tweet_id: tweetId})
  });
  const data = await resp.json();

  if (data.success) {
    document.getElementById('commentary-' + index).textContent = data.commentary;
    card.className = 'card';
    card.querySelector('.char-count').textContent = data.char_count + ' 字';
    btn.innerHTML = '🔄 重写';
    btn.disabled = false;
    // 刷新页面数据
    loadDrafts();
    showToast('🔄 重写完成 (' + data.char_count + ' 字)');
  } else {
    btn.innerHTML = '🔄 重写';
    btn.disabled = false;
    showToast(data.error || '重写失败', true);
  }
}

async function archiveAll() {
  const btn = document.getElementById('archiveBtn');
  btn.disabled = true;
  btn.textContent = '🗂 归档中...';

  const resp = await fetch(API + '/api/archive', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: '{}'
  });
  const data = await resp.json();

  if (data.success) {
    showToast(`🗂 已归档 ${data.archived} 条`);
    loadDrafts();
  } else {
    showToast(data.error || '归档失败', true);
  }
  btn.textContent = '🗂 归档已处理';
  btn.disabled = false;
}

// 页面加载时拉取数据
loadDrafts();
</script>
</body>
</html>"""


def notify(open_browser=True):
    """
    启动审阅服务器：
    1. 在本地启动 HTTP 服务
    2. 弹出桌面通知
    3. 自动打开浏览器
    """
    drafts = load_drafts()
    pending = [d for d in drafts if d.get("status") == "pending_review"]

    if not drafts:
        print("⚠ 没有草稿，请先运行 processor.py", file=sys.stderr)
        return 0

    if not pending:
        print("⚠ 没有待审阅的草稿（全部已处理）")
        return 0

    server = HTTPServer(("127.0.0.1", SERVER_PORT), ReviewHandler)
    url = f"http://127.0.0.1:{SERVER_PORT}"

    print(f"📄 审阅服务已启动: {url}")
    print(f"   待审阅: {len(pending)} 条")
    print(f"   按 Ctrl+C 关闭服务")

    # 桌面通知
    try:
        import subprocess
        msg = f"共 {len(pending)} 条推文锐评待审阅"
        subprocess.Popen(
            ["powershell", "-Command",
             f"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
             f"[System.Windows.Forms.MessageBox]::Show('{msg}', '推文审阅提醒')"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        print("🔔 弹窗通知已发送")
    except Exception:
        pass

    # 自动打开浏览器
    if open_browser:
        webbrowser.open(url)
        print("🌐 已在浏览器中打开审阅页面")

    # 阻塞运行直到 Ctrl+C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 审阅服务已关闭")
        server.server_close()

    return len(pending)


if __name__ == "__main__":
    notify()
