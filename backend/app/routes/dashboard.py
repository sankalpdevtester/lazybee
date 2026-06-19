from fastapi import APIRouter, Depends
from app.routes.deps import require_auth
from app.storage import read_json, write_json, get_logs
from app.services.leetcode_service import fetch_daily_problem
from datetime import datetime, timezone
import os

router = APIRouter()

COOKIE_EXPIRY_DAYS = 26
WARN_AT_DAYS = [23, 25, 26]

def _get_cookie_reminder() -> dict:
    state = read_json("lc_cookie_state")
    updated_at = state.get("updated_at")
    if not updated_at:
        return {"status": "unknown", "days_old": None, "warn": True, "message": "LeetCode session date unknown — click \"Cookies Updated\" after setting them."}
    try:
        updated = datetime.fromisoformat(updated_at)
        days_old = (datetime.now(timezone.utc) - updated.replace(tzinfo=timezone.utc)).days
        days_left = COOKIE_EXPIRY_DAYS - days_old
        if days_old >= COOKIE_EXPIRY_DAYS:
            return {"status": "expired", "days_old": days_old, "days_left": 0, "warn": True,
                    "message": f"LeetCode cookies are {days_old}d old — likely expired! Update LEETCODE_SESSION + CSRF on Render now."}
        if days_old in WARN_AT_DAYS or days_old > max(WARN_AT_DAYS):
            return {"status": "expiring", "days_old": days_old, "days_left": days_left, "warn": True,
                    "message": f"LeetCode cookies expire in {days_left} day(s)! Update LEETCODE_SESSION + CSRF on Render."}
        return {"status": "ok", "days_old": days_old, "days_left": days_left, "warn": False,
                "message": f"Cookies OK — {days_left} days until refresh needed."}
    except Exception:
        return {"status": "unknown", "days_old": None, "warn": True, "message": "Could not parse cookie date."}

@router.get("/", dependencies=[Depends(require_auth)])
async def dashboard():
    accounts_data = read_json("accounts")
    accounts = [{"username": a["username"], "active": a.get("active", True)} for a in accounts_data.get("accounts", [])]
    rotation = read_json("rotation")
    logs = get_logs(10)
    leetcode = await fetch_daily_problem()
    lc_reminder = _get_cookie_reminder()

    return {
        "accounts": accounts,
        "rotation": rotation,
        "recent_logs": logs,
        "leetcode_daily": leetcode,
        "lc_cookie_reminder": lc_reminder,
    }

@router.post("/run-now", dependencies=[Depends(require_auth)])
def run_now():
    from app.scheduler.jobs import _get_token, _get_state, _save_state, _create_new_project, _continue_project, _next_language, _projects_this_month, BLOCKED_REPOS
    import threading
    def _run():
        token = _get_token()
        if not token:
            return
        state = _get_state()
        projects = state.get("projects", {})
        slot_key = "slot_0"
        slot_project_name = state.get(slot_key)
        project = projects.get(slot_project_name) if slot_project_name else None
        if not project or slot_project_name in BLOCKED_REPOS:
            _create_new_project(token, state, projects, 0, slot_key)
        else:
            _continue_project(token, state, projects, slot_project_name)
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "GitHub automation triggered. Check logs for progress."}

@router.post("/update-all-projects", dependencies=[Depends(require_auth)])
def update_all_projects():
    """Add multi-file feature updates to ALL projects right now."""
    import threading
    from app.scheduler.jobs import _get_token, update_all_projects as _update_all
    def _run():
        token = _get_token()
        if token:
            _update_all(token)
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "Updating all projects with new features. Check logs for progress."}

@router.post("/run-leetcode", dependencies=[Depends(require_auth)])
def run_leetcode():
    import threading, asyncio
    from app.services.leetcode_auto import run_daily_leetcode
    def _run():
        asyncio.run(run_daily_leetcode(10))
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "LeetCode automation triggered. Solving 8 problems. Check logs."}

@router.post("/update-profile", dependencies=[Depends(require_auth)])
def update_profile():
    import threading
    from app.services.profile_updater import update_profile_readme
    threading.Thread(target=update_profile_readme, daemon=True).start()
    return {"message": "Profile README update triggered. Check logs."}

@router.post("/star-repos", dependencies=[Depends(require_auth)])
def star_repos():
    import threading
    from app.services.auto_star import star_all_repos
    threading.Thread(target=star_all_repos, daemon=True).start()
    return {"message": "Auto-starring repos with all accounts. Check logs."}

@router.post("/backfill-github", dependencies=[Depends(require_auth)])
def backfill_github():
    """Backfill GitHub contribution graphs for all accounts up to June 7 2026."""
    import threading, subprocess, sys, os
    def _run():
        try:
            script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backfill_contributions.py")
            from app.storage import append_log
            from datetime import datetime
            append_log(datetime.utcnow().isoformat(), "backfill", f"Starting backfill from {script}", "info")
            subprocess.run([sys.executable, script], timeout=7200, capture_output=False)
        except Exception as e:
            from app.storage import append_log
            from datetime import datetime
            append_log(datetime.utcnow().isoformat(), "backfill", f"Backfill failed: {e}", "error")
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "GitHub contribution backfill started. Takes 15-30 mins. Check Logs page."}

@router.post("/refresh-lc-session", dependencies=[Depends(require_auth)])
async def refresh_lc_session():
    """
    Calls the Cloudflare worker /login endpoint to get fresh LeetCode cookies
    bound to Cloudflare's edge IP, then auto-updates Render env vars.
    """
    import httpx
    proxy_url = os.getenv("LEETCODE_PROXY_URL", "").strip()
    proxy_secret = os.getenv("LEETCODE_PROXY_SECRET", "").strip()

    if not proxy_url or not proxy_secret:
        return {"message": "No proxy configured. Set LEETCODE_PROXY_URL and LEETCODE_PROXY_SECRET on Render."}

    # Call the /login route on the worker
    login_url = proxy_url.rstrip("/") + "/login"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(login_url, headers={"X-Proxy-Secret": proxy_secret})
        data = r.json()
    except Exception as e:
        return {"message": f"Worker login failed: {e}"}

    if not data.get("success"):
        return {"message": f"Login failed: {data.get('error', 'unknown')}"}

    new_session = data.get("LEETCODE_SESSION", "")
    new_csrf = data.get("LEETCODE_CSRF", "")

    if not new_session:
        return {"message": "No session returned from worker"}

    # Update in-process env immediately
    os.environ["LEETCODE_SESSION"] = new_session
    if new_csrf:
        os.environ["LEETCODE_CSRF"] = new_csrf

    # Try to update Render env vars automatically
    render_api_key = os.getenv("RENDER_API_KEY", "").strip()
    service_id = os.getenv("RENDER_SERVICE_ID", "").strip()
    render_updated = False
    if render_api_key and service_id:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"https://api.render.com/v1/services/{service_id}/env-vars",
                    headers={"Authorization": f"Bearer {render_api_key}", "Accept": "application/json"},
                )
                if r.status_code == 200:
                    env_vars = r.json()
                    updated = []
                    for ev in env_vars:
                        key = ev.get("envVar", {}).get("key", "")
                        if key == "LEETCODE_SESSION":
                            updated.append({"key": "LEETCODE_SESSION", "value": new_session})
                        elif key == "LEETCODE_CSRF" and new_csrf:
                            updated.append({"key": "LEETCODE_CSRF", "value": new_csrf})
                        else:
                            updated.append({"key": key, "value": ev["envVar"]["value"]})
                    await client.put(
                        f"https://api.render.com/v1/services/{service_id}/env-vars",
                        headers={"Authorization": f"Bearer {render_api_key}", "Content-Type": "application/json"},
                        json=updated,
                    )
                    render_updated = True
        except Exception:
            pass

    # Reset cookie timer
    from datetime import datetime, timezone
    write_json("lc_cookie_state", {"updated_at": datetime.now(timezone.utc).isoformat()})

    return {
        "message": f"Session refreshed from Cloudflare edge IP. {'Render env vars updated.' if render_updated else 'Update LEETCODE_SESSION on Render manually.'} LeetCode submissions should work now."
    }


def mark_cookies_updated():
    """Call this after you update LEETCODE_SESSION + CSRF on Render to reset the 26-day timer."""
    from datetime import datetime, timezone
    write_json("lc_cookie_state", {"updated_at": datetime.now(timezone.utc).isoformat()})
    return {"message": "Cookie timer reset. Next reminder in 23 days."}
