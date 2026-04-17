from google import genai
import os, json, re

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.0-flash"

def _ask(prompt: str) -> str:
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text

def _parse_json(text: str) -> dict:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except Exception:
        return {}

def generate_project_idea(existing_projects: list[str]) -> dict:
    avoid = ", ".join(existing_projects) if existing_projects else "none"
    prompt = f"""
You are a senior software engineer. Suggest ONE large, comprehensive CS project for a developer portfolio.

Requirements:
- Must be a REAL, impressive full-stack project: web app, SaaS tool, developer platform, or CS-related website
- Must have AT LEAST 50 distinct features across 10+ pages/routes
- Must be production-quality with professional UI
- Examples: full e-commerce platform, project management SaaS, social coding platform, AI-powered dashboard, developer portfolio CMS, real-time collaboration tool, learning management system, job board platform
- Language: TypeScript (React/Next.js + Node/FastAPI backend)
- Must be completable incrementally over 28 days with daily commits
- Avoid these already existing: {avoid}

Respond ONLY in this exact JSON format, no extra text:
{{
  "name": "repo-name-in-kebab-case",
  "title": "Human Readable Title",
  "description": "Two sentence description of what it does and who it helps",
  "language": "TypeScript",
  "stack": "React + TypeScript + Tailwind + FastAPI + SQLite",
  "folder_structure": ["src/", "src/components/", "src/pages/", "src/hooks/", "src/lib/", "src/types/", "backend/", "backend/routes/", "backend/models/", "docs/", "public/"],
  "features": [
    "User authentication and authorization",
    "Dashboard with analytics"
  ],
  "pages": [
    "/home - Landing page",
    "/dashboard - Main dashboard"
  ],
  "roadmap": [
    "Day 1-2: Project setup, folder structure, README, auth system",
    "Day 3-4: Database models, core API endpoints",
    "Day 5-6: Main dashboard UI",
    "Day 7-8: Core feature 1 implementation",
    "Day 9-10: Core feature 2 implementation",
    "Day 11-12: Core feature 3 + API integration",
    "Day 13-14: Secondary features batch 1",
    "Day 15-16: Secondary features batch 2",
    "Day 17-18: UI polish, responsive design",
    "Day 19-20: Testing, error handling",
    "Day 21-22: Performance optimization",
    "Day 23-24: Documentation, API docs",
    "Day 25-26: Deployment config, CI/CD",
    "Day 27-28: Final polish, README update"
  ]
}}
"""
    return _parse_json(_ask(prompt))


def generate_daily_commit(project: dict, day: int, existing_files: list[str]) -> dict:
    roadmap = project.get("roadmap", [])
    step = roadmap[min(day // 2, len(roadmap) - 1)] if roadmap else "continue development"
    structure = project.get("folder_structure", [])
    stack = project.get("stack", project.get("language", ""))
    features = project.get("features", [])
    pages = project.get("pages", [])

    prompt = f"""
You are a developer building a large production-quality project: {project['title']}
Description: {project['description']}
Stack: {stack}
Folder structure: {', '.join(structure)}
Total planned features: {len(features)}
Pages: {', '.join(pages[:5]) if pages else 'multiple'}
Today's goal (day {day}/28): {step}
Files already created: {', '.join(existing_files) if existing_files else 'none yet'}

Write ONE real, complete, working code file that makes meaningful progress.
Rules:
- Real working code only, no placeholders, no TODOs
- Must be substantial - at least 50-100 lines of real code
- Must fit the project folder structure
- Day 1-2: setup files (package.json, tsconfig, tailwind config, README)
- Day 3-6: core models, types, API routes
- Day 7+: actual UI components and pages with full implementation
- Use TypeScript with proper types
- Use Tailwind for styling if frontend
- Make it look professional

Respond ONLY in this exact JSON format, no extra text:
{{
  "file_path": "src/components/Header.tsx",
  "content": "full working file content here",
  "commit_message": "feat: add header component with navigation and auth state"
}}
"""
    return _parse_json(_ask(prompt))


def generate_readme(project: dict) -> str:
    prompt = f"""
Write a professional README.md for this project:
Title: {project['title']}
Description: {project['description']}
Stack: {project.get('stack', project.get('language', ''))}
Folder structure: {', '.join(project.get('folder_structure', []))}

Include: badges, description, features list, installation steps, usage, folder structure, contributing, license.
Return ONLY the raw markdown content, nothing else.
"""
    return _ask(prompt)


def generate_maintenance_commit(project: dict) -> dict:
    prompt = f"""
You are maintaining: {project['title']}
Description: {project['description']}
Stack: {project.get('stack', project.get('language', ''))}
Existing files: {', '.join(project.get('files', []))}

Write a small but real maintenance update. Choose one:
- Fix a bug or edge case
- Add a missing docstring or JSDoc comment to an existing function
- Improve error handling
- Add a small utility helper
- Update README with better docs

Respond ONLY in this exact JSON format, no extra text:
{{
  "file_path": "src/utils/helpers.py",
  "content": "full file content",
  "commit_message": "fix: handle edge case in input validation"
}}
"""
    return _parse_json(_ask(prompt))


def chat_with_context(message: str, context: str) -> str:
    system = """You are the LazyBee AI assistant. LazyBee automates GitHub commits across multiple accounts on a rotating 3-day cycle, builds real CS projects over 2 weeks per account, and shows daily LeetCode problems. Be concise and direct."""
    return _ask(f"{system}\n\n{context}\n\nUser: {message}")
