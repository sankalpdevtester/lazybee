import random
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.storage import read_json, write_json
from app.services.gemini_service import generate_project_idea, generate_daily_commit, generate_maintenance_commit, generate_readme
from app.services.github_service import create_repo_and_init, commit_file

scheduler = BackgroundScheduler()

AUTOMATION_ACCOUNT = "sankalpdevtester"
DAYS_PER_SLOT = 3       # switch project slot every 3 days
PROJECT_COMPLETE_DAYS = 28  # ~1 month to complete a project

def _log(message: str, level: str = "info"):
    data = read_json("logs.json")
    logs = data.get("logs", [])
    logs.append({
        "timestamp": datetime.utcnow().isoformat(),
        "account": AUTOMATION_ACCOUNT,
        "message": message,
        "level": level,
    })
    write_json("logs.json", {"logs": logs[-500:]})

def _get_automation_account() -> dict | None:
    data = read_json("accounts.json")
    return next((a for a in data.get("accounts", []) if a["username"] == AUTOMATION_ACCOUNT and not a.get("display_only")), None)

def _get_state() -> dict:
    return read_json("rotation.json")

def _save_state(state: dict):
    write_json("rotation.json", state)

def _days_since(iso_str: str) -> int:
    if not iso_str:
        return 999
    return (datetime.utcnow() - datetime.fromisoformat(iso_str)).days

def run_daily_automation():
    account = _get_automation_account()
    if not account:
        _log("No automation account found", "error")
        return

    token = account["token"]
    state = _get_state()
    projects = state.get("projects", {})  # { repo_name: project_data }
    slot_start = state.get("slot_start")
    current_slot = state.get("current_slot", 0)  # which project slot is active

    # Determine if we need to switch slots (every 3 days)
    if not slot_start or _days_since(slot_start) >= DAYS_PER_SLOT:
        current_slot = (current_slot + 1) % 2  # alternate between slot 0 and slot 1
        state["current_slot"] = current_slot
        state["slot_start"] = datetime.utcnow().isoformat()
        _save_state(state)
        _log(f"Switched to project slot {current_slot}")

    # Get or create project for current slot
    slot_key = f"slot_{current_slot}"
    slot_project_name = state.get(slot_key)
    project = projects.get(slot_project_name) if slot_project_name else None

    if not project:
        # No project in this slot - create a new one
        _create_new_project(token, state, projects, current_slot, slot_key)
    else:
        days_on_project = _days_since(project.get("started_at", ""))
        if days_on_project >= PROJECT_COMPLETE_DAYS:
            # Project is complete - mark it and start fresh next cycle
            projects[slot_project_name]["completed"] = True
            state["projects"] = projects
            state[slot_key] = None  # clear slot so new project gets created
            _save_state(state)
            _log(f"Project {project['title']} marked complete after {days_on_project} days")
            _create_new_project(token, state, projects, current_slot, slot_key)
        else:
            _continue_project(token, state, projects, slot_project_name)

def _create_new_project(token: str, state: dict, projects: dict, current_slot: int, slot_key: str):
    try:
        # Check if there's an incomplete project from a previous cycle to resume
        incomplete = [p for p in projects.values() if not p.get("completed") and p.get("name") not in [state.get("slot_0"), state.get("slot_1")]]

        # Every 2nd week (even weeks) try to resume an old incomplete project
        week_number = (datetime.utcnow() - datetime(2025, 1, 1)).days // 7
        if incomplete and week_number % 2 == 0:
            project = incomplete[0]
            _log(f"Resuming incomplete project: {project['title']}")
        else:
            existing_names = [p["name"] for p in projects.values()]
            project = generate_project_idea(existing_names)
            if not project:
                _log("Gemini returned empty project idea", "error")
                return

            readme = generate_readme(project)
            repo_url = create_repo_and_init(token, project["name"], project["description"], readme)

            # Scaffold folder structure
            for folder in project.get("folder_structure", []):
                if folder.endswith("/"):
                    try:
                        commit_file(token, project["name"], f"{folder}.gitkeep", "", f"chore: scaffold {folder} directory")
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
            _log(f"Created new project: {project['title']} at {repo_url}")

        state[slot_key] = project["name"]
        state["projects"] = projects
        state["current_index"] = 0
        _save_state(state)

    except Exception as e:
        _log(f"Failed to create project: {e}", "error")

def _continue_project(token: str, state: dict, projects: dict, project_name: str):
    try:
        project = projects[project_name]
        day = project.get("day", 1)
        existing_files = project.get("files", [])

        commit_data = generate_daily_commit(project, day, existing_files)
        if not commit_data:
            _log("Gemini returned empty commit", "error")
            return

        commit_file(token, project["name"], commit_data["file_path"], commit_data["content"], commit_data["commit_message"])

        if commit_data["file_path"] not in existing_files:
            existing_files.append(commit_data["file_path"])

        projects[project_name]["day"] = day + 1
        projects[project_name]["files"] = existing_files
        state["projects"] = projects
        _save_state(state)
        _log(f"Committed to {project['title']}: {commit_data['commit_message']}")

    except Exception as e:
        _log(f"Failed daily commit: {e}", "error")

def start_scheduler():
    hour = random.randint(9, 23)
    minute = random.randint(0, 59)
    scheduler.add_job(run_daily_automation, CronTrigger(hour=hour, minute=minute), id="daily_automation", replace_existing=True)
    scheduler.start()
    _log(f"Scheduler started - daily job at {hour:02d}:{minute:02d} UTC")
