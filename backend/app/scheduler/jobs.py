import random
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.storage import read_json, write_json, append_log
from app.services.gemini_service import generate_project_idea, generate_daily_commit, generate_maintenance_commit, generate_readme
from app.services.github_service import create_repo_and_init, commit_file

scheduler = BackgroundScheduler()

AUTOMATION_ACCOUNT = "sankalpdevtester"
DAYS_PER_SLOT = 3
PROJECT_COMPLETE_DAYS = 28

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

def run_daily_automation():
    token = _get_token()
    if not token:
        _log("No token found for sankalpdevtester", "error")
        return

    state = _get_state()
    projects = state.get("projects", {})
    slot_start = state.get("slot_start")
    current_slot = state.get("current_slot", 0)

    # Switch project slot every 3 days
    if not slot_start or _days_since(slot_start) >= DAYS_PER_SLOT:
        current_slot = (current_slot + 1) % 2
        state["current_slot"] = current_slot
        state["slot_start"] = datetime.utcnow().isoformat()
        _save_state(state)
        _log(f"Switched to project slot {current_slot}")

    slot_key = f"slot_{current_slot}"
    slot_project_name = state.get(slot_key)
    project = projects.get(slot_project_name) if slot_project_name else None

    if not project:
        _create_new_project(token, state, projects, current_slot, slot_key)
    else:
        days_on_project = _days_since(project.get("started_at", ""))
        if days_on_project >= PROJECT_COMPLETE_DAYS:
            projects[slot_project_name]["completed"] = True
            state["projects"] = projects
            state[slot_key] = None
            _save_state(state)
            _log(f"Project {project['title']} completed after {days_on_project} days")
            _create_new_project(token, state, projects, current_slot, slot_key)
        else:
            _continue_project(token, state, projects, slot_project_name)

def _create_new_project(token: str, state: dict, projects: dict, current_slot: int, slot_key: str):
    try:
        # On even weeks resume an incomplete project, odd weeks create new
        week_number = (datetime.utcnow() - datetime(2025, 1, 1)).days // 7
        incomplete = [p for p in projects.values() if not p.get("completed") and p.get("name") not in [state.get("slot_0"), state.get("slot_1")]]

        if incomplete and week_number % 2 == 0:
            project = incomplete[0]
            _log(f"Resuming project: {project['title']}")
        else:
            existing_names = [p["name"] for p in projects.values()]
            project = generate_project_idea(existing_names)
            if not project:
                _log("Gemini returned empty project idea", "error")
                return

            readme = generate_readme(project)
            repo_url = create_repo_and_init(token, project["name"], project["description"], readme)

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
