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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # 技能根目录（scripts/ 的上级）
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DRAFTS_FILE = os.path.join(DATA_DIR, "drafts.json")
ARCHIVE_FILE = os.path.join(DATA_DIR, "archive.json")
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


def regenerate_commentary(draft, lang="zh"):
    """Regenerate LLM commentary for a single draft"""
    from processor import get_llm_client, call_llm, build_prompt, truncate_text

    config = get_llm_client()
    if not config:
        return None

    fake_tweet = {
        "type": "tweet",
        "content": {
            "text": draft.get("original_text", ""),
            "author": draft.get("original_author", ""),
            "username": draft.get("original_username", ""),
        }
    }
    prompt = build_prompt(fake_tweet)
    commentary = call_llm(config, prompt, lang=lang)
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
        elif path == "/api/refresh":
            self._handle_refresh()
        else:
            self.send_error(404)

    def _handle_review(self):
        """处理审阅状态更新"""
        body = self._read_body()
        tweet_id = body.get("tweet_id")
        status = body.get("status")  # approved / rejected

        if not tweet_id or status not in ("approved", "rejected"):
            self._send_json({"error": "Invalid parameters"}, 400)
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
            self._send_json({"error": "Draft not found"}, 404)

    def _handle_regenerate(self):
        """处理驳回后重新生成"""
        body = self._read_body()
        tweet_id = body.get("tweet_id")

        if not tweet_id:
            self._send_json({"error": "Missing tweet_id"}, 400)
            return

        lang = body.get("lang", "zh")
        if lang not in ("zh", "en"):
            lang = "zh"

        drafts = load_drafts()
        target = None
        for draft in drafts:
            if draft.get("tweet_id") == tweet_id:
                target = draft
                break

        if not target:
            self._send_json({"error": "Draft not found"}, 404)
            return

        print(f"  \u0052egenerate {tweet_id} (lang={lang})...", end=" ")
        new_commentary = regenerate_commentary(target, lang=lang)

        if new_commentary:
            target["commentary"] = new_commentary
            target["char_count"] = len(new_commentary)
            target["status"] = "pending_review"
            target["generated_at"] = datetime.now().isoformat()
            target["regenerated"] = target.get("regenerated", 0) + 1
            target["lang"] = lang
            save_drafts(drafts)
            print(f"done ({len(new_commentary)} chars)")
            self._send_json({
                "success": True,
                "commentary": new_commentary,
                "char_count": len(new_commentary),
                "lang": lang,
            })
        else:
            print("failed")
            self._send_json({"error": "LLM regeneration failed"}, 500)

    def _handle_archive(self):
        """归档已审阅的草稿"""
        drafts = load_drafts()
        to_archive = [d for d in drafts if d.get("status") in ("approved", "rejected")]
        remaining = [d for d in drafts if d.get("status") not in ("approved", "rejected")]

        if not to_archive:
            self._send_json({"error": "No items to archive"}, 400)
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
        print(f"  Archived {len(to_archive)}, remaining {len(remaining)}")
        self._send_json({"success": True, "archived": len(to_archive), "remaining": len(remaining)})

    def _handle_refresh(self):
        """Trigger watcher + processor to pick up new URLs and generate drafts"""
        print("  🔄 Refresh triggered from web UI...")
        try:
            from watcher import watch
            from processor import process

            new_tweets = watch()
            new_drafts = 0
            if new_tweets > 0:
                new_drafts = process()

            print(f"  Refresh done: {new_tweets} fetched, {new_drafts} processed")
            self._send_json({
                "success": True,
                "fetched": new_tweets,
                "processed": new_drafts,
            })
        except Exception as e:
            print(f"  Refresh failed: {e}")
            self._send_json({"error": str(e)}, 500)

    def _serve_html(self):
        """返回审阅页面 HTML"""
        html = generate_review_html()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def generate_review_html():
    """Generate the review dashboard HTML"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Social Reader Review</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, 'Segoe UI', sans-serif;
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
    .badge-lang { background: #1d2e1f; color: #7ee787; border: 1px solid #7ee78733; }
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
    .btn-lang { border-color: #7ee78744; }
    .btn-lang:hover { border-color: #7ee787; color: #7ee787; }
    .toolbar {
      display: flex; justify-content: flex-end; margin-bottom: 20px; gap: 10px;
    }
    .btn-toolbar {
      padding: 8px 20px; border: 1px solid #30363d; border-radius: 8px;
      background: #21262d; cursor: pointer;
      font-size: 14px; font-weight: 600; transition: all 0.15s;
    }
    .btn-refresh { color: #58a6ff; border-color: #58a6ff44; }
    .btn-refresh:hover { background: #58a6ff22; border-color: #58a6ff; }
    .btn-refresh:disabled { opacity: 0.4; cursor: not-allowed; }
    .btn-archive { color: #f0883e; border-color: #f0883e44; }
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
    <h1>🔍 Social Reader Review</h1>
    <p class="subtitle" id="subtitle">Loading...</p>
    <div class="toolbar">
      <button class="btn-toolbar btn-refresh" id="refreshBtn" onclick="refreshPipeline()">🔄 Refresh</button>
      <button class="btn-toolbar btn-archive" id="archiveBtn" onclick="archiveAll()" disabled>🗂 Archive</button>
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
    `Pending: ${pendingReview.length} · Reviewed: ${reviewed.length}`;
  document.getElementById('archiveBtn').disabled = reviewed.length === 0;

  const container = document.getElementById('cards');
  if (drafts.length === 0) {
    container.innerHTML = '<div class="empty">No drafts yet</div>';
    return;
  }

  container.innerHTML = drafts.map((d, i) => {
    const regenBadge = d.regenerated
      ? `<span class="badge badge-regen">Rewritten ${d.regenerated}x</span>` : '';
    const currentLang = d.lang || 'zh';
    const langBadge = currentLang === 'en'
      ? '<span class="badge badge-lang">EN</span>' : '';
    const isApproved = d.status === 'approved';
    const toggleLabel = currentLang === 'zh' ? '🌐 English' : '🌐 Chinese';
    const toggleLang = currentLang === 'zh' ? 'en' : 'zh';

    return `
    <div class="card ${d.status === 'approved' ? 'approved' : ''} ${d.status === 'rejected' ? 'rejected' : ''}" id="card-${i}" data-id="${d.tweet_id}" data-lang="${currentLang}">
      <div class="card-header">
        <span class="author">@${escapeHtml(d.original_username || '?')}</span>
        <div class="badges">
          ${regenBadge}
          ${langBadge}
          <span class="char-count">${d.char_count || '?'} chars</span>
        </div>
      </div>
      <div class="original">
        <div class="label">Original</div>
        <p>${escapeHtml((d.original_text || '').substring(0, 200))}</p>
        <a href="${d.original_url || '#'}" target="_blank" class="link">View source</a>
      </div>
      <div class="commentary">
        <div class="label">AI Commentary</div>
        <p id="commentary-${i}">${escapeHtml(d.commentary || '')}</p>
      </div>
      <div class="actions">
        <button class="btn btn-copy" onclick="copyText(${i})" ${isApproved ? 'disabled' : ''}>📋 Copy</button>
        <button class="btn btn-approve" onclick="review(${i}, 'approved')" ${isApproved ? 'disabled' : ''}>✓ Approve</button>
        <button class="btn btn-reject" onclick="review(${i}, 'rejected')" ${isApproved ? 'disabled' : ''}>✗ Reject</button>
        <button class="btn btn-regen" onclick="regenerate(${i})" id="regen-${i}" ${isApproved ? 'disabled' : ''}>🔄 Rewrite</button>
        <button class="btn btn-lang" onclick="toggleLang(${i}, '${toggleLang}')" id="lang-${i}" ${isApproved ? 'disabled' : ''}>${toggleLabel}</button>
      </div>
    </div>`;
  }).join('');
}

async function copyText(index) {
  const el = document.getElementById('commentary-' + index);
  try {
    await navigator.clipboard.writeText(el.textContent);
    showToast('Copied to clipboard');
  } catch(e) {
    showToast('Copy failed', true);
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
      showToast('✓ Approved');
    } else {
      showToast('✗ Rejected — click Rewrite to regenerate');
    }
  } else {
    showToast(data.error || 'Operation failed', true);
  }
}

async function regenerate(index) {
  const card = document.getElementById('card-' + index);
  const tweetId = card.dataset.id;
  const currentLang = card.dataset.lang || 'zh';
  const btn = document.getElementById('regen-' + index);

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Rewriting...';

  const resp = await fetch(API + '/api/regenerate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({tweet_id: tweetId, lang: currentLang})
  });
  const data = await resp.json();

  if (data.success) {
    document.getElementById('commentary-' + index).textContent = data.commentary;
    card.className = 'card';
    card.querySelector('.char-count').textContent = data.char_count + ' chars';
    btn.innerHTML = '🔄 Rewrite';
    btn.disabled = false;
    loadDrafts();
    showToast('🔄 Rewritten (' + data.char_count + ' chars)');
  } else {
    btn.innerHTML = '🔄 Rewrite';
    btn.disabled = false;
    showToast(data.error || 'Rewrite failed', true);
  }
}

async function toggleLang(index, targetLang) {
  const card = document.getElementById('card-' + index);
  const tweetId = card.dataset.id;
  const btn = document.getElementById('lang-' + index);

  btn.disabled = true;
  const langName = targetLang === 'en' ? 'English' : 'Chinese';
  btn.innerHTML = '<span class="spinner"></span>' + langName + '...';

  const resp = await fetch(API + '/api/regenerate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({tweet_id: tweetId, lang: targetLang})
  });
  const data = await resp.json();

  if (data.success) {
    document.getElementById('commentary-' + index).textContent = data.commentary;
    card.dataset.lang = targetLang;
    card.querySelector('.char-count').textContent = data.char_count + ' chars';
    loadDrafts();
    showToast('🌐 Switched to ' + langName);
  } else {
    btn.disabled = false;
    btn.innerHTML = '🌐 ' + langName;
    showToast(data.error || 'Language switch failed', true);
  }
}

async function refreshPipeline() {
  const btn = document.getElementById('refreshBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Refreshing...';

  try {
    const resp = await fetch(API + '/api/refresh', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: '{}'
    });
    const data = await resp.json();

    if (data.success) {
      showToast(`🔄 Fetched: ${data.fetched}, Processed: ${data.processed}`);
      loadDrafts();
    } else {
      showToast(data.error || 'Refresh failed', true);
    }
  } catch(e) {
    showToast('Refresh failed: ' + e.message, true);
  }
  btn.innerHTML = '🔄 Refresh';
  btn.disabled = false;
}

async function archiveAll() {
  const btn = document.getElementById('archiveBtn');
  btn.disabled = true;
  btn.textContent = '🗂 Archiving...';

  const resp = await fetch(API + '/api/archive', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: '{}'
  });
  const data = await resp.json();

  if (data.success) {
    showToast(`🗂 Archived ${data.archived} items`);
    loadDrafts();
  } else {
    showToast(data.error || 'Archive failed', true);
  }
  btn.textContent = '🗂 Archive';
  btn.disabled = false;
}

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
