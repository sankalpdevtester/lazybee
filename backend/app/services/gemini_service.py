import os
import json
import re
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def _ask(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content

def _parse_json(text: str) -> dict:
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # Try extracting JSON block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except Exception:
        # Try cleaning common issues
        cleaned = match.group().replace('\n', '\\n').replace('\t', '\\t')
        try:
            return json.loads(cleaned)
        except Exception:
            return {}

def generate_project_idea(existing_projects: list[str], language: str = "TypeScript") -> dict:
    avoid = ", ".join(existing_projects) if existing_projects else "none"
    prompt = f"""You are a senior software engineer. Suggest ONE large comprehensive CS project for a developer portfolio.

Requirements:
- Must be a REAL impressive project: web app, SaaS, CLI tool, API, developer platform
- Must have AT LEAST 50 distinct features across 10+ pages/routes
- Production-quality with professional UI
- Language/Stack: {language} - use the most appropriate framework
- Completable incrementally over 28 days with daily commits
- Avoid these existing projects: {avoid}

Respond ONLY in this exact JSON format, no extra text:
{{
  "name": "repo-name-in-kebab-case",
  "title": "Human Readable Title",
  "description": "Two sentence description",
  "language": "{language}",
  "stack": "specific framework and tools",
  "folder_structure": ["src/", "src/components/", "src/pages/", "src/lib/", "docs/", "tests/"],
  "features": ["feature 1", "feature 2", "feature 3"],
  "pages": ["/home", "/dashboard", "/settings"],
  "roadmap": [
    "Day 1-2: Project setup, folder structure, README, core config",
    "Day 3-4: Database models and core data layer",
    "Day 5-6: Authentication and user management",
    "Day 7-8: Core feature 1",
    "Day 9-10: Core feature 2",
    "Day 11-12: Core feature 3",
    "Day 13-14: Secondary features batch 1",
    "Day 15-16: Secondary features batch 2",
    "Day 17-18: UI components and styling",
    "Day 19-20: API integration and testing",
    "Day 21-22: Performance and optimization",
    "Day 23-24: Documentation and API docs",
    "Day 25-26: Deployment config",
    "Day 27-28: Final polish and README"
  ]
}}"""
    return _parse_json(_ask(prompt))

def generate_daily_commit(project: dict, day: int, existing_files: list[str]) -> dict:
    roadmap = project.get("roadmap", [])
    step = roadmap[min(day // 2, len(roadmap) - 1)] if roadmap else "continue development"
    stack = project.get("stack", project.get("language", ""))
    features = project.get("features", [])
    pages = project.get("pages", [])

    prompt = f"""You are a developer building: {project['title']}
Description: {project['description']}
Stack: {stack}
Today goal (day {day}/28): {step}
Files already created: {', '.join(existing_files) if existing_files else 'none yet'}

Write ONE real working code file. Respond in this EXACT format with no deviation:
FILE_PATH: src/example.py
COMMIT_MESSAGE: feat: add example feature
CODE_START
(put the full code here)
CODE_END"""

    text = _ask(prompt)
    try:
        file_path = re.search(r'FILE_PATH:\s*(.+)', text)
        commit_msg = re.search(r'COMMIT_MESSAGE:\s*(.+)', text)
        code_match = re.search(r'CODE_START\n(.*?)\nCODE_END', text, re.DOTALL)
        if file_path and commit_msg and code_match:
            return {
                "file_path": file_path.group(1).strip(),
                "content": code_match.group(1).strip(),
                "commit_message": commit_msg.group(1).strip(),
            }
    except Exception:
        pass
    return {}

def generate_readme(project: dict) -> str:
    prompt = f"""Write a professional README.md for this project:
Title: {project['title']}
Description: {project['description']}
Stack: {project.get('stack', project.get('language', ''))}
Features: {', '.join(project.get('features', [])[:10])}
Folder structure: {', '.join(project.get('folder_structure', []))}

Include: badges, description, features list, installation steps, usage, folder structure, contributing, license.
Return ONLY the raw markdown content, nothing else."""
    return _ask(prompt)

def generate_maintenance_commit(project: dict) -> dict:
    prompt = f"""You are maintaining: {project['title']}
Description: {project['description']}
Stack: {project.get('stack', project.get('language', ''))}
Existing files: {', '.join(project.get('files', [])[:10])}

Write a small real maintenance update: fix a bug, add a docstring, improve error handling, or add a small helper.

Respond in this EXACT format:
FILE_PATH: src/utils/helpers.py
COMMIT_MESSAGE: fix: improve error handling
CODE_START
(put the full code here)
CODE_END"""

    text = _ask(prompt)
    try:
        file_path = re.search(r'FILE_PATH:\s*(.+)', text)
        commit_msg = re.search(r'COMMIT_MESSAGE:\s*(.+)', text)
        code_match = re.search(r'CODE_START\n(.*?)\nCODE_END', text, re.DOTALL)
        if file_path and commit_msg and code_match:
            return {
                "file_path": file_path.group(1).strip(),
                "content": code_match.group(1).strip(),
                "commit_message": commit_msg.group(1).strip(),
            }
    except Exception:
        pass
    return {}

def chat_with_context(message: str, context: str) -> str:
    system = "You are the LazyBee AI assistant. LazyBee automates GitHub commits across multiple accounts, builds real CS projects daily, and solves LeetCode problems automatically. Be concise and direct."
    return _ask(f"{system}\n\n{context}\n\nUser: {message}")
