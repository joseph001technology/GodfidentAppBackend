"""
apps/api/views.py

Browsable API root for Godfident.
Visit /api/ in the browser to see all endpoints.
"""
from django.views import View
from django.http import HttpResponse
from django.urls import reverse, NoReverseMatch


# ──────────────────────────────────────────────────────────────────────────────
# REGISTRY
# Tuple layout: (method, url_name, url_pattern, description, auth, throttle, params)
# params = {param_name: description_string}   (? suffix = optional)
# ──────────────────────────────────────────────────────────────────────────────

GROUPS = [
    {
        "label": "accounts",
        "color": "#6C5CE7",
        "prefix": "/api/auth/",
        "endpoints": [
            ("POST",  "register",            "/api/auth/register/",            "Register a new user. Sends a verification email.",                         False, None,     {"email": "string", "password": "string", "password_confirm": "string", "first_name?": "string", "last_name?": "string"}),
            ("POST",  "login",               "/api/auth/login/",               "Login — returns access + refresh JWT tokens.",                             False, "5/min",  {"email": "string", "password": "string"}),
            ("POST",  "token-refresh",       "/api/auth/token/refresh/",       "Exchange a refresh token for a new access token.",                         False, None,     {"refresh": "JWT string"}),
            ("POST",  "verify-email",        "/api/auth/verify-email/",        "Verify email using the UUID token sent on registration.",                  False, None,     {"token": "UUID"}),
            ("POST",  "resend-verification", "/api/auth/resend-verification/", "Resend the verification email to the logged-in user.",                     True,  None,     {}),
            ("POST",  "forgot-password",     "/api/auth/forgot-password/",     "Request a password reset email. Never reveals if email exists.",           False, "3/hour", {"email": "string"}),
            ("POST",  "reset-password",      "/api/auth/reset-password/",      "Set a new password using the UUID token from the reset email.",            False, None,     {"token": "UUID", "new_password": "string", "new_password_confirm": "string"}),
            ("GET",   "me",                  "/api/auth/me/",                  "Get the current user with their full profile.",                            True,  None,     {}),
            ("PATCH", "me",                  "/api/auth/me/",                  "Update first_name or last_name.",                                          True,  None,     {"first_name?": "string", "last_name?": "string"}),
            ("GET",   "profile",             "/api/auth/profile/",             "Get profile (translation preference, timezone, reminders).",               True,  None,     {}),
            ("PATCH", "profile",             "/api/auth/profile/",             "Update profile preferences.",                                              True,  None,     {"preferred_translation?": "KJV|NIV|ESV|NKJV|NLT", "timezone?": "string", "reading_reminder?": "bool", "reminder_time?": "HH:MM"}),
            ("POST",  "change-password",     "/api/auth/change-password/",     "Change password while logged in. Requires old password.",                  True,  None,     {"old_password": "string", "new_password": "string", "new_password_confirm": "string"}),
        ],
    },
    {
        "label": "bible",
        "color": "#00B894",
        "prefix": "/api/bible/",
        "endpoints": [
            ("GET",    "translation-list",  "/api/bible/translations/",        "List all active translations (KJV, NIV, ESV, NKJV, NLT).",                False, None, {}),
            ("GET",    "book-list",         "/api/bible/books/",               "List all 66 books. Filter by testament, search by name.",                  False, None, {"testament?": "OT|NT", "search?": "string"}),
            ("GET",    "verse",             "/api/bible/verse/",               "Fetch a single verse by book, chapter, verse, translation.",               True,  None, {"book": "e.g. John", "chapter": "int", "verse": "int", "translation?": "default KJV"}),
            ("GET",    "chapter",           "/api/bible/chapter/",             "All verses in a chapter with prev/next navigation.",                       True,  None, {"book": "string", "chapter": "int", "translation?": "default KJV"}),
            ("GET",    "parallel",          "/api/bible/parallel/",            "Same verse in multiple translations side by side.",                        True,  None, {"book": "string", "chapter": "int", "verse": "int", "translations?": "comma-sep e.g. KJV,NIV,ESV"}),
            ("GET",    "search",            "/api/bible/search/",              "Full-text search across verses. Returns up to 50 results.",                True,  None, {"q": "string", "translation?": "default KJV", "testament?": "OT|NT"}),
            ("GET",    "cross-references",  "/api/bible/cross-references/",    "Related verses for a given verse, ordered by relevance score.",            True,  None, {"book": "string", "chapter": "int", "verse": "int"}),
            ("GET",    "bookmark-list",     "/api/bible/bookmarks/",           "List your bookmarks.",                                                     True,  None, {}),
            ("POST",   "bookmark-list",     "/api/bible/bookmarks/",           "Create a bookmark on a verse.",                                            True,  None, {"book": "int (Book ID)", "chapter": "int", "verse": "int", "note?": "string"}),
            ("DELETE", "bookmark-detail",   "/api/bible/bookmarks/{id}/",      "Delete a bookmark.",                                                       True,  None, {}),
            ("GET",    "highlight-list",    "/api/bible/highlights/",          "List highlights. Filter by color.",                                        True,  None, {"color?": "yellow|green|blue|pink|orange"}),
            ("POST",   "highlight-list",    "/api/bible/highlights/",          "Create a colour-coded highlight on a verse.",                              True,  None, {"book": "int", "chapter": "int", "verse": "int", "color?": "yellow|green|blue|pink|orange", "note?": "string"}),
            ("GET",    "verse-note-list",   "/api/bible/notes/",               "List your personal study notes.",                                          True,  None, {}),
            ("POST",   "verse-note-list",   "/api/bible/notes/",               "Create a study note on a verse.",                                          True,  None, {"book": "int", "chapter": "int", "verse": "int", "content": "string"}),
            ("PATCH",  "verse-note-detail", "/api/bible/notes/{id}/",          "Update a study note.",                                                     True,  None, {"content": "string"}),
            ("DELETE", "verse-note-detail", "/api/bible/notes/{id}/",          "Delete a study note.",                                                     True,  None, {}),
        ],
    },
    {
        "label": "devotionals",
        "color": "#E67E22",
        "prefix": "/api/devotionals/",
        "endpoints": [
            ("GET",    "today-devotional",         "/api/devotionals/today/",         "Today's devotional. Falls back to latest. Auto-marks as read.",   True, None, {}),
            ("GET",    "devotional-list",          "/api/devotionals/",               "List published devotionals. Search and filter by category.",       True, None, {"search?": "string", "category?": "int"}),
            ("GET",    "devotional-detail",        "/api/devotionals/{id}/",          "Get a devotional. Marks it read in your history.",                 True, None, {}),
            ("POST",   "devotional-save",          "/api/devotionals/{id}/save/",     "Save a devotional to favourites.",                                True, None, {}),
            ("DELETE", "devotional-unsave",        "/api/devotionals/{id}/unsave/",   "Remove from saved.",                                              True, None, {}),
            ("GET",    "saved-devotionals",        "/api/devotionals/saved/",         "List your saved devotionals, most recently saved first.",         True, None, {}),
            ("GET",    "devotional-category-list", "/api/devotionals/categories/",    "List all devotional categories.",                                 True, None, {}),
        ],
    },
    {
        "label": "reading_plans",
        "color": "#2980B9",
        "prefix": "/api/reading-plans/",
        "endpoints": [
            ("GET",  "reading-plan-list",              "/api/reading-plans/plans/",                      "List all available reading plans.",                       True, None, {}),
            ("GET",  "reading-plan-days",              "/api/reading-plans/plans/{id}/days/",            "All daily reading assignments for a plan.",               True, None, {}),
            ("GET",  "user-reading-plan-list",         "/api/reading-plans/my-plans/",                   "Plans you are enrolled in with progress info.",           True, None, {}),
            ("POST", "user-reading-plan-list",         "/api/reading-plans/my-plans/",                   "Enroll in a reading plan.",                               True, None, {"plan_id": "int"}),
            ("POST", "user-reading-plan-complete-day", "/api/reading-plans/my-plans/{id}/complete_day/", "Mark a day done. Advances progress and updates streak.",  True, None, {"day_number?": "int (defaults to current_day)"}),
            ("POST", "user-reading-plan-pause",        "/api/reading-plans/my-plans/{id}/pause/",        "Pause an active plan.",                                   True, None, {}),
            ("POST", "user-reading-plan-resume",       "/api/reading-plans/my-plans/{id}/resume/",       "Resume a paused plan.",                                   True, None, {}),
            ("GET",  "reading-streak",                 "/api/reading-plans/streak/",                     "Current streak, longest streak, total days read.",        True, None, {}),
        ],
    },
    {
        "label": "prayer",
        "color": "#C0392B",
        "prefix": "/api/prayer/",
        "endpoints": [
            ("GET",    "prayer-list",          "/api/prayer/",                    "List prayers. Filter by type/status, search, order.",             True, None, {"prayer_type?": "request|praise|intercession|thanksgiving", "status?": "active|answered|archived", "search?": "string", "ordering?": "-created_at"}),
            ("POST",   "prayer-list",          "/api/prayer/",                    "Create a prayer.",                                                True, None, {"title": "string", "content": "string", "prayer_type?": "default: request", "scripture?": "string", "is_private?": "bool"}),
            ("PATCH",  "prayer-detail",        "/api/prayer/{id}/",               "Update a prayer.",                                                True, None, {"title?": "string", "content?": "string", "status?": "string"}),
            ("DELETE", "prayer-detail",        "/api/prayer/{id}/",               "Delete a prayer.",                                                True, None, {}),
            ("POST",   "prayer-mark-answered", "/api/prayer/{id}/mark_answered/", "Mark as answered with optional testimony note.",                 True, None, {"note?": "string"}),
            ("POST",   "prayer-log-prayer",    "/api/prayer/{id}/log_prayer/",    "Record that you prayed for this item.",                          True, None, {"note?": "string"}),
            ("GET",    "prayer-stats",         "/api/prayer/stats/",              "Stats: totals, answer rate, by type, times prayed.",             True, None, {}),
        ],
    },
    {
        "label": "ai_assistant",
        "color": "#27AE60",
        "prefix": "/api/ai/",
        "endpoints": [
            ("POST", "ai-chat",             "/api/ai/chat/",                 "Bible-focused chat with session memory.",                                     True, "30/min", {"message": "string", "session_id?": "int (omit to start new)"}),
            ("POST", "explain-verse",       "/api/ai/explain-verse/",        "Deep explanation: context, meaning, theology, application, cross-refs.",      True, "30/min", {"reference": "e.g. John 3:16", "translation?": "string", "verse_text?": "string"}),
            ("POST", "explain-chapter",     "/api/ai/explain-chapter/",      "Chapter overview, key themes, key verses, characters, reflection question.",  True, "30/min", {"book": "string", "chapter": "int", "translation?": "string"}),
            ("POST", "topic-study",         "/api/ai/topic-study/",          "Biblical research — OT and NT perspectives, application, prayer.",            True, "30/min", {"topic": "e.g. forgiveness"}),
            ("POST", "character-study",     "/api/ai/character-study/",      "Full study: background, key moments, strengths, failures, legacy.",           True, "30/min", {"character": "e.g. David"}),
            ("GET",  "daily-encouragement", "/api/ai/daily-encouragement/",  "Generate a fresh daily verse, reflection, and prayer.",                      True, "30/min", {}),
            ("POST", "prayer-assistance",   "/api/ai/prayer-assistance/",    "Scriptural promises and a model prayer for your topic.",                     True, "30/min", {"topic": "string", "scripture?": "string"}),
            ("GET",  "study-history",       "/api/ai/study-history/",        "Past AI study sessions. Filter by type.",                                    True, None,     {"type?": "verse|chapter|topic|character"}),
            ("GET",  "chat-session-list",   "/api/ai/sessions/",             "List your chat sessions.",                                                   True, None,     {}),
        ],
    },
    {
        "label": "notifications",
        "color": "#8E44AD",
        "prefix": "/api/notifications/",
        "endpoints": [
            ("GET",  "notification-list",          "/api/notifications/",                "List notifications. Filter to unread only.",     True, None, {"unread?": "true"}),
            ("POST", "notification-mark-read",     "/api/notifications/{id}/mark_read/", "Mark one notification as read.",                 True, None, {}),
            ("POST", "notification-mark-all-read", "/api/notifications/mark_all_read/",  "Mark all notifications as read.",               True, None, {}),
            ("GET",  "notification-unread-count",  "/api/notifications/unread_count/",   "Unread count for a mobile badge.",              True, None, {}),
        ],
    },
    {
        "label": "analytics",
        "color": "#34495E",
        "prefix": "/api/analytics/",
        "endpoints": [
            ("GET",  "analytics-dashboard", "/api/analytics/dashboard/",   "Full dashboard: reading, prayer, devotionals, plans, annotations.",  True, None, {}),
            ("GET",  "reading-heatmap",     "/api/analytics/heatmap/",     "Chapter counts per day for the past N days (heatmap data).",         True, None, {"days?": "int (default 365)"}),
            ("GET",  "weekly-report",       "/api/analytics/weekly/",      "Day-by-day breakdown of the current week.",                          True, None, {}),
            ("GET",  "monthly-report",      "/api/analytics/monthly/",     "Monthly summary with consistency score.",                            True, None, {"year?": "int", "month?": "int"}),
            ("POST", "log-reading",         "/api/analytics/log-reading/", "Log a chapter read. Updates streak automatically.",                  True, None, {"book_name": "string", "chapter": "int", "translation?": "string"}),
        ],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

_METHOD_COLORS = {
    "GET":    ("#d4edda", "#155724"),
    "POST":   ("#cce5ff", "#004085"),
    "PATCH":  ("#fff3cd", "#856404"),
    "DELETE": ("#f8d7da", "#721c24"),
    "PUT":    ("#fff3cd", "#856404"),
}

def _badge(method):
    bg, fg = _METHOD_COLORS.get(method, ("#e9ecef", "#495057"))
    return (
        f'<span style="font-family:monospace;font-size:11px;font-weight:700;'
        f'padding:2px 8px;border-radius:4px;'
        f'background:{bg};color:{fg};">{method}</span>'
    )

def _resolve(name):
    try:
        return reverse(name)
    except NoReverseMatch:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# VIEW
# ──────────────────────────────────────────────────────────────────────────────

class ApiRootView(View):
    """Render the Godfident API reference at /api/."""

    def get(self, request):
        total = sum(len(g["endpoints"]) for g in GROUPS)
        base  = request.build_absolute_uri("/").rstrip("/")
        return HttpResponse(self._page(base, total))

    # ── page ──────────────────────────────────────────────────────────────────

    def _page(self, base, total):
        groups_html = "\n".join(self._group(g, i) for i, g in enumerate(GROUPS))
        sidebar = "\n".join(
            f'<a href="#g{i}" style="display:flex;align-items:center;gap:8px;padding:5px 8px;'
            f'border-radius:6px;color:#495057;text-decoration:none;font-size:13px;transition:background .1s"'
            f' onmouseover="this.style.background=\'#f8f9fa\'" onmouseout="this.style.background=\'\'">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{g["color"]};flex-shrink:0"></span>'
            f'{g["label"]}'
            f'<span style="margin-left:auto;font-size:11px;color:#adb5bd">{len(g["endpoints"])}</span>'
            f'</a>'
            for i, g in enumerate(GROUPS)
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Godfident API</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:14px;background:#f4f5f7;color:#212529;line-height:1.5}}
.navbar{{background:#1a252f;color:#fff;padding:0 24px;height:52px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:100;box-shadow:0 2px 6px rgba(0,0,0,.3)}}
.brand{{font-size:16px;font-weight:700;color:#1abc9c}}
.brand-sub{{font-size:12px;color:#7f8c8d;margin-left:4px}}
.npill{{font-size:11px;padding:3px 10px;border-radius:99px;font-weight:600;text-decoration:none}}
.layout{{display:flex;max-width:1280px;margin:24px auto;gap:24px;padding:0 16px;align-items:flex-start}}
.sidebar{{width:210px;flex-shrink:0;position:sticky;top:68px;background:#fff;border:1px solid #dee2e6;border-radius:8px;padding:12px}}
.sb-label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6c757d;padding:8px 8px 4px;margin-top:8px;border-top:1px solid #f0f0f0}}
.sb-label:first-child{{margin-top:0;border-top:none}}
.main{{flex:1;min-width:0}}
.page-hdr{{background:#fff;border:1px solid #dee2e6;border-radius:8px;padding:20px 24px;margin-bottom:16px}}
.page-hdr h1{{font-size:20px;font-weight:700;margin-bottom:4px}}
.page-hdr p{{color:#6c757d;font-size:13px}}
.meta{{display:flex;gap:20px;margin-top:10px;flex-wrap:wrap;font-size:12px;color:#6c757d}}
.meta strong{{color:#212529}}
.controls{{background:#fff;border:1px solid #dee2e6;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
.controls input{{flex:1;min-width:200px;border:1px solid #dee2e6;border-radius:6px;padding:7px 12px;font-size:13px;outline:none}}
.controls input:focus{{border-color:#1a252f}}
.pills{{display:flex;gap:6px;flex-wrap:wrap}}
.pill{{font-size:11px;padding:4px 12px;border-radius:99px;border:1px solid #dee2e6;cursor:pointer;background:#fff;color:#6c757d;font-weight:500;transition:all .15s;user-select:none}}
.pill.on{{background:#1a252f;color:#fff;border-color:#1a252f}}
.group{{background:#fff;border:1px solid #dee2e6;border-radius:8px;margin-bottom:14px;overflow:hidden}}
.g-hdr{{display:flex;align-items:center;gap:10px;padding:11px 16px;background:#f8f9fa;border-bottom:1px solid #dee2e6;cursor:pointer;user-select:none}}
.g-hdr:hover{{background:#e9ecef}}
.g-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.g-title{{font-weight:600;font-size:14px;flex:1}}
.g-prefix{{font-size:11px;font-family:monospace;color:#6c757d}}
.g-count{{font-size:11px;background:#e9ecef;color:#495057;padding:2px 8px;border-radius:99px}}
.chev{{font-size:11px;color:#6c757d;transition:transform .2s;margin-left:4px;display:inline-block}}
.chev.open{{transform:rotate(180deg)}}
.ep-row{{border-bottom:1px solid #f0f0f0;cursor:pointer}}
.ep-row:last-child{{border-bottom:none}}
.ep-row:hover .ep-main{{background:#f8f9fa}}
.ep-row.hidden{{display:none}}
.ep-main{{display:grid;grid-template-columns:78px 1fr auto;gap:12px;align-items:center;padding:10px 16px;transition:background .1s}}
.ep-url{{font-family:monospace;font-size:13px;font-weight:500;word-break:break-all;color:#212529}}
.ep-desc{{font-size:12px;color:#6c757d;margin-top:2px}}
.ep-right{{display:flex;flex-direction:column;align-items:flex-end;gap:3px;white-space:nowrap}}
.rev{{font-family:monospace;font-size:11px;color:#0055aa}}
.ab{{font-size:10px;padding:2px 7px;border-radius:3px}}
.ab-jwt{{background:#fff3cd;color:#856404}}
.ab-pub{{background:#d4edda;color:#155724}}
.tb{{font-size:10px;padding:2px 7px;border-radius:3px;background:#f8d7da;color:#721c24}}
.detail{{display:none;background:#f8f9fa;border-top:1px solid #e9ecef;padding:14px 16px 14px 106px}}
.detail.open{{display:block}}
.dl{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#6c757d;margin-bottom:5px;margin-top:12px}}
.dl:first-child{{margin-top:0}}
.dg{{display:grid;grid-template-columns:140px 1fr;gap:3px 12px;font-size:12px}}
.dk{{color:#6c757d;padding:2px 0}}
.dv{{color:#212529;font-family:monospace;font-size:11px;padding:2px 0;word-break:break-all}}
.pt{{width:100%;border-collapse:collapse;font-size:12px;margin-top:4px}}
.pt th{{text-align:left;color:#6c757d;font-weight:600;padding:4px 10px 4px 0;border-bottom:1px solid #dee2e6}}
.pt td{{padding:4px 10px 4px 0;border-bottom:1px solid #f0f0f0;vertical-align:top}}
.pt .pn{{font-family:monospace;color:#0055aa}}
.no-results{{text-align:center;padding:40px;color:#6c757d;display:none}}
</style>
</head>
<body>
<nav class="navbar">
  <span class="brand">✝ Godfident</span>
  <span class="brand-sub">API Reference</span>
  <div style="margin-left:auto;display:flex;gap:8px">
    <span class="npill" style="background:#1abc9c;color:#fff">{total} endpoints</span>
    <a class="npill" href="/api/docs/" style="background:#e74c3c;color:#fff">Swagger</a>
    <a class="npill" href="/admin/" style="background:#2c3e50;color:#fff;border:1px solid #555">Admin</a>
  </div>
</nav>
<div class="layout">
  <aside class="sidebar">
    <div class="sb-label">Apps</div>
    {sidebar}
    <div class="sb-label">Links</div>
    <a href="/api/docs/" style="display:block;padding:5px 8px;font-size:13px;color:#0055aa;text-decoration:none;border-radius:6px">Swagger UI</a>
    <a href="/api/schema/" style="display:block;padding:5px 8px;font-size:13px;color:#0055aa;text-decoration:none;border-radius:6px">OpenAPI Schema</a>
  </aside>
  <main class="main">
    <div class="page-hdr">
      <h1>✝ Godfident API</h1>
      <p>Personal Bible study &amp; spiritual growth platform — REST API reference.</p>
      <div class="meta">
        <div><strong>Base URL</strong>&nbsp;{base}</div>
        <div><strong>Auth</strong>&nbsp;Authorization: Bearer &lt;access_token&gt;</div>
        <div><strong>Format</strong>&nbsp;application/json</div>
      </div>
    </div>
    <div class="controls">
      <input id="q" type="text" placeholder="Search by URL, description, or name…" oninput="applyFilters()">
      <div class="pills">
        <span class="pill on" data-m="ALL"    onclick="setM(this)">All</span>
        <span class="pill"    data-m="GET"    onclick="setM(this)">GET</span>
        <span class="pill"    data-m="POST"   onclick="setM(this)">POST</span>
        <span class="pill"    data-m="PATCH"  onclick="setM(this)">PATCH</span>
        <span class="pill"    data-m="DELETE" onclick="setM(this)">DELETE</span>
      </div>
    </div>
    <div id="gc">{groups_html}</div>
    <div class="no-results" id="nr">No endpoints match your search.</div>
  </main>
</div>
<script>
let aM='ALL';
function toggleG(id){{
  const b=document.getElementById('b'+id),c=document.getElementById('c'+id);
  const open=b.style.display!=='none';
  b.style.display=open?'none':'block';
  c.classList.toggle('open',!open);
}}
function toggleD(id){{
  const el=document.getElementById('d'+id);
  const was=el.classList.contains('open');
  document.querySelectorAll('.detail.open').forEach(e=>e.classList.remove('open'));
  if(!was) el.classList.add('open');
}}
function setM(el){{
  document.querySelectorAll('.pill').forEach(p=>p.classList.remove('on'));
  el.classList.add('on'); aM=el.dataset.m; applyFilters();
}}
function applyFilters(){{
  const q=document.getElementById('q').value.toLowerCase();
  let any=false;
  document.querySelectorAll('.group').forEach(g=>{{
    let vis=0;
    g.querySelectorAll('.ep-row').forEach(r=>{{
      const ok=(aM==='ALL'||r.dataset.m===aM)&&(!q||r.dataset.t.includes(q));
      r.classList.toggle('hidden',!ok);
      if(ok) vis++;
    }});
    g.style.display=vis?'':'none';
    const c=g.querySelector('.g-count');
    if(c) c.textContent=vis+(vis===1?' endpoint':' endpoints');
    if(vis&&(q||aM!=='ALL')){{
      const id=g.id.replace('g','');
      document.getElementById('b'+id).style.display='block';
      document.getElementById('c'+id).classList.add('open');
    }}
    if(vis) any=true;
  }});
  document.getElementById('nr').style.display=any?'none':'block';
}}
</script>
</body>
</html>"""

    # ── group ─────────────────────────────────────────────────────────────────

    def _group(self, g, idx):
        rows = "\n".join(self._row(ep, f"{idx}_{ei}") for ei, ep in enumerate(g["endpoints"]))
        return (
            f'<div class="group" id="g{idx}">'
            f'<div class="g-hdr" onclick="toggleG({idx})">'
            f'<span class="g-dot" style="background:{g["color"]}"></span>'
            f'<span class="g-title">{g["label"]}</span>'
            f'<span class="g-prefix">{g["prefix"]}</span>'
            f'<span class="g-count">{len(g["endpoints"])} endpoints</span>'
            f'<span class="chev open" id="c{idx}">&#9660;</span>'
            f'</div>'
            f'<div id="b{idx}">{rows}</div>'
            f'</div>'
        )

    # ── row ───────────────────────────────────────────────────────────────────

    def _row(self, ep, uid):
        method, name, url, desc, auth, throttle, params = ep

        resolved   = _resolve(name)
        url_html   = f'<a href="{resolved}" style="color:#212529">{url}</a>' if resolved else url
        auth_html  = '<span class="ab ab-jwt">&#128274; JWT</span>' if auth else '<span class="ab ab-pub">&#10003; public</span>'
        th_html    = f'<span class="tb">&#9889; {throttle}</span>' if throttle else ""
        search_txt = f"{method} {url} {name} {desc}".lower()

        if params:
            p_rows = "".join(
                f'<tr><td class="pn">{k}</td><td style="color:#495057">{v}</td></tr>'
                for k, v in params.items()
            )
            params_html = (
                f'<div class="dl">Parameters</div>'
                f'<table class="pt"><thead><tr><th>Name</th><th>Type / notes</th></tr></thead>'
                f'<tbody>{p_rows}</tbody></table>'
            )
        else:
            params_html = '<p style="font-size:12px;color:#6c757d;margin-top:6px">No parameters.</p>'

        return (
            f'<div class="ep-row" data-m="{method}" data-t="{search_txt}" onclick="toggleD(\'{uid}\')">'
            f'<div class="ep-main">'
            f'<div>{_badge(method)}</div>'
            f'<div><div class="ep-url">{url_html}</div><div class="ep-desc">{desc}</div></div>'
            f'<div class="ep-right"><span class="rev">reverse(\'{name}\')</span>{auth_html}{th_html}</div>'
            f'</div>'
            f'<div class="detail" id="d{uid}">'
            f'<div class="dl">Details</div>'
            f'<div class="dg">'
            f'<span class="dk">URL name</span><span class="dv">{name}</span>'
            f'<span class="dk">reverse() call</span><span class="dv">reverse(\'{name}\')</span>'
            f'<span class="dk">Full pattern</span><span class="dv">{url}</span>'
            f'<span class="dk">Auth</span><span class="dv">{"Bearer JWT required" if auth else "Public"}</span>'
            f'<span class="dk">Throttle</span><span class="dv">{throttle or "None"}</span>'
            f'</div>'
            f'{params_html}'
            f'</div>'
            f'</div>'
        )
