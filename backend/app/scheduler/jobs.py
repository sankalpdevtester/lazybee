import random
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.storage import read_json, write_json, append_log
from app.services.gemini_service import generate_project_idea, generate_scaffold, generate_daily_commit, generate_multi_file_commit, generate_maintenance_commit, generate_readme
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
    from app.routes.dashboard import _get_cookie_reminder
    reminder = _get_cookie_reminder()
    if reminder.get("warn"):
        _log(f"COOKIE REMINDER: {reminder['message']}", "error")

    token = _get_token()
    if not token:
        _log("No token for sankalpdevtester", "error")
        return

    state = _get_state()
    projects = state.get("projects", {})
    day_of_week = _day_of_week()

    if day_of_week == 6:
        _do_weekly_maintenance(token, state, projects)

    # Revive old projects every day, not just first Monday
    _revive_old_projects(token, state, projects)

    current_slot = 0 if day_of_week < 3 else 1
    state["current_slot"] = current_slot
    slot_key = f"slot_{current_slot}"
    slot_project_name = state.get(slot_key)
    project = projects.get(slot_project_name) if slot_project_name else None
    monthly_count = _projects_this_month(projects)

    if not project:
        if monthly_count >= 8:
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
        days_on_project = _days_since(project.get("started_at", ""))
        if days_on_project >= PROJECT_DAYS:
            projects[slot_project_name]["completed"] = True
            state[slot_key] = None
            state["projects"] = projects
            _save_state(state)
            _log(f"Project {project['title']} completed after {days_on_project} days")
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
            _log("Project idea generation returned empty", "error")
            return

        # Generate README first and init repo
        readme = generate_readme(project)
        repo_url = create_repo_and_init(token, project["name"], project["description"][:350], readme)
        _log(f"Created repo: {repo_url}")

        # Generate ALL scaffold files so project is runnable from day 1
        committed_files = ["README.md"]
        scaffold_files = generate_scaffold(project)
        if not scaffold_files:
            _log(f"Scaffold generation returned empty for {project['title']}, continuing anyway", "error")
        for f in scaffold_files:
            try:
                commit_file(token, project["name"], f["file_path"], f["content"], f["commit_message"])
                committed_files.append(f["file_path"])
                _log(f"Scaffolded: {f['file_path']}")
            except Exception as e:
                _log(f"Failed to commit scaffold {f['file_path']}: {e}", "error")

        project = {
            **project,
            "repo_url": repo_url,
            "day": 1,
            "files": committed_files,
            "started_at": datetime.utcnow().isoformat(),
            "completed": False,
        }
        projects[project["name"]] = project
        state[slot_key] = project["name"]
        state["projects"] = projects
        _save_state(state)
        _log(f"New project ready: {project['title']} ({lang}) — {len(committed_files)} files committed, runnable at {repo_url}")
    except Exception as e:
        _log(f"Failed to create project: {e}", "error")

def _continue_project(token: str, state: dict, projects: dict, project_name: str):
    try:
        project = projects[project_name]
        day = project.get("day", 1)
        existing_files = project.get("files", [])

        _log(f"Generating multi-file batch for day {day} of {project['title']}...")
        files = generate_multi_file_commit(project, day, existing_files)

        if not files:
            single = generate_daily_commit(project, day, existing_files)
            files = [single] if single else []

        committed_any = False
        for f in files:
            if not f or not f.get("file_path") or not f.get("content"):
                continue
            if f["file_path"] in existing_files:
                continue
            try:
                commit_file(token, project["name"], f["file_path"], f["content"], f["commit_message"])
                existing_files.append(f["file_path"])
                _log(f"  + {f['file_path']}: {f['commit_message']}")
                committed_any = True
            except Exception as e:
                _log(f"  Failed {f['file_path']}: {e}", "error")

        if committed_any:
            projects[project_name]["day"] = day + 1
            projects[project_name]["files"] = existing_files
            state["projects"] = projects
            _save_state(state)
            _log(f"Day {day} done for {project['title']} — {len(existing_files)} total files")
        else:
            _log(f"No files committed for {project['title']} day {day}", "error")
    except Exception as e:
        _log(f"Failed daily commit: {e}", "error")


def update_all_projects(token: str):
    """Manually trigger multi-file update on ALL projects (active + completed), except lazybee."""
    state = _get_state()
    projects = state.get("projects", {})
    if not projects:
        _log("No projects found to update")
        return

    updated = 0
    for name, project in projects.items():
        if name in BLOCKED_REPOS:
            continue
        try:
            existing_files = project.get("files", [])
            day = project.get("day", 1)
            _log(f"Updating {project.get('title', name)}...")
            files = generate_multi_file_commit(project, day, existing_files)
            if not files:
                single = generate_maintenance_commit(project)
                files = [single] if single else []

            committed = 0
            for f in files:
                if not f or not f.get("file_path") or not f.get("content"):
                    continue
                if f["file_path"] in existing_files:
                    continue
                try:
                    commit_file(token, name, f["file_path"], f["content"], f["commit_message"])
                    existing_files.append(f["file_path"])
                    _log(f"  + {f['file_path']}: {f['commit_message']}")
                    committed += 1
                except Exception as e:
                    _log(f"  Failed {f['file_path']}: {e}", "error")

            if committed > 0:
                projects[name]["files"] = existing_files
                projects[name]["day"] = day + 1
                updated += 1
                _log(f"Updated {project.get('title', name)}: {committed} files added")
        except Exception as e:
            _log(f"Failed to update {name}: {e}", "error")

    state["projects"] = projects
    _save_state(state)
    _log(f"Update all done: {updated}/{len(projects)} projects updated")

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
    """Every day - add commits to 1-2 old completed projects to keep them alive."""
    completed = [p for p in projects.values() if p.get("completed") and p.get("name") not in BLOCKED_REPOS]
    if not completed:
        return
    to_revive = random.sample(completed, min(2, len(completed)))
    for project in to_revive:
        try:
            commit_data = generate_maintenance_commit(project)
            if not commit_data:
                continue
            commit_file(token, project["name"], commit_data["file_path"], commit_data["content"], commit_data["commit_message"])
            _log(f"Revival commit to {project['title']}: {commit_data['commit_message']}")
        except Exception as e:
            _log(f"Revival failed for {project['name']}: {e}", "error")

def _ist_to_utc(ist_hour: int) -> int:
    """IST = UTC+5:30, so UTC = IST - 5 (ignoring 30min, handled by minute offset)"""
    return (ist_hour - 5) % 24

def start_scheduler():
    # Random IST times - changes on each redeploy to look natural
    ist_hour = random.randint(10, 21)
    minute = random.randint(0, 59)
    hour = _ist_to_utc(ist_hour)
    scheduler.add_job(run_daily_automation, CronTrigger(hour=hour, minute=minute), id="daily_automation", replace_existing=True)
    hour2 = (hour + 12) % 24
    scheduler.add_job(run_12h_automation, CronTrigger(hour=hour2, minute=minute), id="12h_automation", replace_existing=True)
    # LeetCode 4x daily at random IST times
    ist_lc_hours = sorted(random.sample(range(7, 24), 4))
    for i, ist_lc in enumerate(ist_lc_hours):
        lc_minute = random.randint(0, 59)
        scheduler.add_job(_run_leetcode, CronTrigger(hour=_ist_to_utc(ist_lc), minute=lc_minute), id=f"leetcode_{i}", replace_existing=True)
    scheduler.start()
    # Daily LinkedIn post at a random IST evening time (6-9pm)
    ist_li = random.randint(18, 21)
    li_minute = random.randint(0, 59)
    scheduler.add_job(_run_linkedin, CronTrigger(hour=_ist_to_utc(ist_li), minute=li_minute), id="linkedin_daily", replace_existing=True)
    _log(f"Scheduler started - GitHub IST {ist_hour:02d}:{minute:02d} (UTC {hour:02d}:{minute:02d}), +12h UTC {hour2:02d}:{minute:02d}, LeetCode IST {ist_lc_hours}, LinkedIn IST {ist_li:02d}:{li_minute:02d}")

def _run_leetcode():
    import asyncio
    from app.services.leetcode_auto import run_daily_leetcode
    asyncio.run(run_daily_leetcode(10))

def _run_linkedin():
    import asyncio
    from app.services.linkedin_content import run_linkedin_post
    asyncio.run(run_linkedin_post("daily_update"))
