"""
Health check used by the uptime cron job that keeps the Render free instance awake.

    GET /api/health/   ->  {"status": "ok", "online_videos": true}

"online_videos" is present only when this deployment contains the Online Videos routes, so opening the
health URL in a browser tells you at once whether the latest backend code is really live (the app's
"share to Godfident" links are saved through those routes).

No login, no throttle and no database query, so it is as cheap as possible and
always answers 200 while the process is up.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def _online_videos_deployed() -> bool:
    """True when the Online Videos URL prefix is wired into this deployment (no database access)."""
    try:
        from django.urls import resolve
        resolve('/api/online-videos/videos/')
        return True
    except Exception:
        return False


@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def health(request):
    response = JsonResponse({"status": "ok", "online_videos": _online_videos_deployed()})
    response["Cache-Control"] = "no-store"
    return response
