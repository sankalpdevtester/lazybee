import random
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.storage import read_json, write_json, append_log
from app.services.gemini_service import generate_project_idea, generate_daily_commit, generate_maintenance_commit, generate_readme
from app.services.github_service import create_repo_and_init, commit_file

scheduler = BackgroundScheduler()

AUTOMATION_ACCOUNT = "sankalpdevtester"
BLOCKED_REPOS = {"lazybee"}  # never touch these
PROJECT_DAYS = 7  # days before starting a new project

# 30+ languages and stacks to cycle through
LANGUAGES = [
    # Core languages
    "Python", "TypeScript", "JavaScript", "Java", "Go",
    "Rust", "C++", "C#", "PHP", "Ruby",
    "Swift", "Kotlin", "Scala", "R", "Dart",
    "Elixir", "Haskell", "Lua", "Perl", "Shell",
    "C", "Zig",
    # Full stacks
    "MERN Stack (MongoDB + Express + React + Node.js)",
    "MEAN Stack (MongoDB + Express + Angular + Node.js)",
    "PERN Stack (PostgreSQL + Express + React + Node.js)",
    "Next.js + Prisma + PostgreSQL",
    "Django + React + PostgreSQL",
    "FastAPI + React + SQLite",
    "Laravel + Vue.js",
    "Ruby on Rails + React",
    # Specialized
    "Web3 + Solidity + Ethers.js + React",
    "Three.js + WebGL + React (3D)",
    "Babylon.js + TypeScript (3D Game)",
    "React Native + Expo (Mobile)",
    "Flutter + Dart (Mobile)",
    "Electron + React (Desktop)",
    "GraphQL + Apollo + React",
    "tRPC + Next.js + Prisma",
    "Svelte + SvelteKit",
    "Remix + React",
]

def _log(message: str, level: str = "info"):
    append_log(datetime.utcnow().isoformat(), AUTOMATION_ACCOUNT, message, level)

def _get_token() -> str:
    data = read_json("accounts")
    account = next((a for a in data.get("accounts", []) if a["username"] == AUTOMATION_ACCOUNT), None)
    return account["token"] if account else ""

def _get_state() -> dict:
    return read_json("rotation")

def _save_state(state: dict):
    write_json("rotation", state)

def _days_since(iso_str: str) -> int:
    if not iso_str:
        return 999
    try:
        return (datetime.utcnow() - datetime.fromisoformat(iso_str)).days
    except Exception:
        return 999

def _week_of_month() -> int:
    return (datetime.utcnow().day - 1) // 7

def _day_of_week() -> int:
    return datetime.utcnow().weekday()  # 0=Monday, 6=Sunday

def _projects_this_month(projects: dict) -> int:
    now = datetime.utcnow()
    count = 0
    for p in projects.values():
        started = p.get("started_at", "")
        if started:
            try:
                d = datetime.fromisoformat(started)
                if d.month == now.month and d.year == now.year:
                    count += 1
            except Exception:
                pass
    return count

def _next_language(projects: dict) -> str:
    used = [p.get("language", "") for p in projects.values()]
    # Pick least used language
    counts = {lang: used.count(lang) for lang in LANGUAGES}
    min_count = min(counts.values())
    available = [lang for lang, c in counts.items() if c == min_count]
    return random.choice(available)

def run_daily_automation():
    """Main daily job - runs once per day for GitHub commits."""
    token = _get_token()
    if not token:
        _log("No token for sankalpdevtester", "error")
        return

    state = _get_state()
    projects = state.get("projects", {})
    day_of_week = _day_of_week()

    # Day 7 (Sunday) = maintenance on both active projects
    if day_of_week == 6:
        _do_weekly_maintenance(token, state, projects)
        return

    # First week of month = check if any old projects need revival
    if _week_of_month() == 0 and day_of_week == 0:
        _revive_old_projects(token, state, projects)

    # Determine active slot (slot 0 = Mon-Wed, slot 1 = Thu-Sat)
    current_slot = 0 if day_of_week < 3 else 1
    state["current_slot"] = current_slot
    slot_key = f"slot_{current_slot}"
    slot_project_name = state.get(slot_key)
    project = projects.get(slot_project_name) if slot_project_name else None

    # Check monthly project cap (max 8)
    monthly_count = _projects_this_month(projects)

    if not project:
        if monthly_count >= 8:
            # Cap reached - work on existing incomplete project
            incomplete = [p for p in projects.values() if not p.get("completed") and p.get("name") not in BLOCKED_REPOS]
            if incomplete:
                project = incomplete[0]
                state[slot_key] = project["name"]
                _save_state(state)
                _log(f"Monthly cap reached, resuming: {project['title']}")
                _continue_project(token, state, projects, project["name"])
            else:
                _log("Monthly cap of 8 projects reached, skipping")
            return
        _create_new_project(token, state, projects, current_slot, slot_key)
    else:
        if slot_project_name in BLOCKED_REPOS:
            _log(f"Blocked repo {slot_project_name} - clearing slot", "error")
            state[slot_key] = None
            _save_state(state)
            return
        # Check if project exceeded 7 days - start new one
        days_on_project = _days_since(project.get("started_at", ""))
        if days_on_project >= PROJECT_DAYS:
            projects[slot_project_name]["completed"] = True
            state[slot_key] = None
            state["projects"] = projects
            _save_state(state)
            _log(f"Project {project['title']} completed after {days_on_project} days, starting new one")
            _create_new_project(token, state, projects, current_slot, slot_key)
        else:
            _continue_project(token, state, projects, slot_project_name)

def run_12h_automation():
    """Runs every 12 hours - adds a commit to one active project."""
    token = _get_token()
    if not token:
        return

    state = _get_state()
    projects = state.get("projects", {})

    # Pick any active non-completed project
    active = [p for p in projects.values() if not p.get("completed") and p.get("name") not in BLOCKED_REPOS]
    if not active:
        return

    project = random.choice(active)
    try:
        commit_data = generate_maintenance_commit(project)
        if not commit_data:
            return
        commit_file(token, project["name"], commit_data["file_path"], commit_data["content"], commit_data["commit_message"])
        projects[project["name"]]["files"] = list(set(project.get("files", []) + [commit_data["file_path"]]))
        state["projects"] = projects
        _save_state(state)
        _log(f"12h commit to {project['title']}: {commit_data['commit_message']}")
    except Exception as e:
        _log(f"12h commit failed: {e}", "error")

def _create_new_project(token: str, state: dict, projects: dict, current_slot: int, slot_key: str):
    try:
        existing_names = [p["name"] for p in projects.values()]
        lang = _next_language(projects)
        project = generate_project_idea(existing_names, lang)
        if not project:
            _log("Gemini returned empty project idea", "error")
            return

        readme = generate_readme(project)
        repo_url = create_repo_and_init(token, project["name"], project["description"][:350], readme)

        for folder in project.get("folder_structure", []):
            if folder.endswith("/"):
                try:
                    commit_file(token, project["name"], f"{folder}.gitkeep", "", f"chore: scaffold {folder}")
                except Exception:
                    pass

        project = {
            **project,
            "repo_url": repo_url,
            "day": 1,
            "files": ["README.md"],
            "started_at": datetime.utcnow().isoformat(),
            "completed": False,
        }
        projects[project["name"]] = project
        state[slot_key] = project["name"]
        state["projects"] = projects
        _save_state(state)
        _log(f"Created new {lang} project: {project['title']} at {repo_url}")
    except Exception as e:
        _log(f"Failed to create project: {e}", "error")

def _continue_project(token: str, state: dict, projects: dict, project_name: str):
    try:
        project = projects[project_name]
        day = project.get("day", 1)
        existing_files = project.get("files", [])

        _log(f"Generating day {day} commit for {project['title']}...")
        commit_data = generate_daily_commit(project, day, existing_files)
        if not commit_data:
            _log("Groq returned empty commit - retrying", "error")
            commit_data = generate_daily_commit(project, day, existing_files)
        if not commit_data:
            _log("Commit generation failed twice, skipping today", "error")
            return

        _log(f"Pushing {commit_data['file_path']} to {project['name']}...")
        commit_file(token, project["name"], commit_data["file_path"], commit_data["content"], commit_data["commit_message"])

        if commit_data["file_path"] not in existing_files:
            existing_files.append(commit_data["file_path"])

        projects[project_name]["day"] = day + 1
        projects[project_name]["files"] = existing_files
        state["projects"] = projects
        _save_state(state)
        _log(f"✅ Day {day} commit to {project['title']}: {commit_data['commit_message']}")
    except Exception as e:
        _log(f"Failed daily commit: {e}", "error")

def _do_weekly_maintenance(token: str, state: dict, projects: dict):
    """Sunday - add small commits to both active projects."""
    for slot in ["slot_0", "slot_1"]:
        name = state.get(slot)
        if not name or name not in projects:
            continue
        try:
            project = projects[name]
            commit_data = generate_maintenance_commit(project)
            if not commit_data:
                continue
            commit_file(token, project["name"], commit_data["file_path"], commit_data["content"], commit_data["commit_message"])
            projects[name]["files"] = list(set(project.get("files", []) + [commit_data["file_path"]]))
            state["projects"] = projects
            _save_state(state)
            _log(f"Weekly maintenance on {project['title']}: {commit_data['commit_message']}")
        except Exception as e:
            _log(f"Weekly maintenance failed for {name}: {e}", "error")

def _revive_old_projects(token: str, state: dict, projects: dict):
    """First Monday of month - add commits to old completed projects to keep them alive."""
    completed = [p for p in projects.values() if p.get("completed") and p.get("name") not in BLOCKED_REPOS]
    if not completed:
        return
    # Pick up to 3 random old projects
    to_revive = random.sample(completed, min(3, len(completed)))
    for project in to_revive:
        try:
            commit_data = generate_maintenance_commit(project)
            if not commit_data:
                continue
            commit_file(token, project["name"], commit_data["file_path"], commit_data["content"], commit_data["commit_message"])
            _log(f"Monthly revival commit to {project['title']}: {commit_data['commit_message']}")
        except Exception as e:
            _log(f"Revival failed for {project['name']}: {e}", "error")

def _ist_to_utc(ist_hour: int) -> int:
    """IST = UTC+5:30, so UTC = IST - 5 (ignoring 30min, handled by minute offset)"""
    return (ist_hour - 5) % 24

def start_scheduler():
    # Fixed IST times - never change on redeploy
    # GitHub main commit - 11AM IST daily
    scheduler.add_job(run_daily_automation, CronTrigger(hour=_ist_to_utc(11), minute=30), id="daily_automation", replace_existing=True)
    # 12h commit - 11PM IST daily  
    scheduler.add_job(run_12h_automation, CronTrigger(hour=_ist_to_utc(23), minute=30), id="12h_automation", replace_existing=True)
    # LeetCode 4x daily at 9AM, 2PM, 7PM, 11PM IST
    for i, (ist_h, ist_m) in enumerate([(9,15),(14,30),(19,0),(23,0)]):
        scheduler.add_job(_run_leetcode, CronTrigger(hour=_ist_to_utc(ist_h), minute=ist_m), id=f"leetcode_{i}", replace_existing=True)
    scheduler.start()
    _log("Scheduler started - GitHub 11:30AM IST, 12h 11:30PM IST, LeetCode 9:15AM/2:30PM/7:00PM/11:00PM IST")

def _run_leetcode():
    import asyncio
    from app.services.leetcode_auto import run_daily_leetcode
    asyncio.run(run_daily_leetcode(8))
