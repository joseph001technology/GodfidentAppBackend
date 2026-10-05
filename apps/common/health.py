"""
Health check used by the uptime cron job that keeps the Render free instance awake.

    GET /health        ->  {"status": "ok"}

No login, no throttle and no database query, so it is as cheap as possible and
always answers 200 while the process is up.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def health(request):
    response = JsonResponse({"status": "ok"})
    response["Cache-Control"] = "no-store"
    return response
