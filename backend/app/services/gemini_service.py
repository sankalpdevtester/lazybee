import os
import json
import re
import time
import httpx
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

def _get_client(key: str) -> Groq:
    return Groq(api_key=key, http_client=httpx.Client(timeout=60.0))

def _ask(prompt: str, model: str = None) -> str:
    use_model = model or MODEL
    keys = [k for k in [
        os.getenv("GROQ_API_KEY", ""),
        os.getenv("GROQ_API_KEY_2", ""),
        os.getenv("GROQ_API_KEY_3", ""),
        os.getenv("GROQ_API_KEY_4", ""),
        os.getenv("GROQ_API_KEY_5", ""),
    ] if k]
    if not keys:
        raise ValueError("No GROQ_API_KEY set")
    last_error = None
    for key in keys:
        client = _get_client(key)
        try:
            response = client.chat.completions.create(
                model=use_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            err = str(e)
            if "429" in err or "rate_limit" in err.lower() or "quota" in err.lower():
                continue  # immediately try next key
            else:
                raise
    raise RuntimeError(f"All Groq keys exhausted. Last error: {last_error}")

def _parse_json(text: str) -> dict:
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except Exception:
        return {}

def _parse_file_format(text: str) -> dict:
    try:
        file_path = re.search(r'FILE_PATH:\s*(.+)', text)
        commit_msg = re.search(r'COMMIT_MESSAGE:\s*(.+)', text)
        code_match = re.search(r'CODE_START\s*\n(.*?)\nCODE_END', text, re.DOTALL)
        if file_path and commit_msg and code_match:
            return {
                "file_path": file_path.group(1).strip(),
                "content": code_match.group(1).strip(),
                "commit_message": commit_msg.group(1).strip(),
            }
        code_block = re.search(r'```(?:\w+)?\n(.*?)\n```', text, re.DOTALL)
        if file_path and commit_msg and code_block:
            return {
                "file_path": file_path.group(1).strip(),
                "content": code_block.group(1).strip(),
                "commit_message": commit_msg.group(1).strip(),
            }
    except Exception:
        pass
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
    title = project.get("title", "")
    description = project.get("description", "")

    prompt = f"""You are an expert {stack} developer working on a real open source project.

Project: {title}
Description: {description}
Stack: {stack}
Day {day} goal: {step}
Files already in repo: {', '.join(existing_files) if existing_files else 'only README.md'}

Write ONE complete, production-quality code file that makes real progress on this project.

Strict rules:
- This must be REAL working code that actually implements the described functionality
- No placeholder comments like "# TODO" or "# implement this"
- No fake data or mock implementations - real algorithms and logic
- Minimum 80 lines of actual implementation
- For {title}:
  - If it's a language/compiler: write real lexer tokens, parser rules, AST nodes, or interpreter logic
  - If it's a database: write real storage engine, WAL, or consensus algorithm code
  - If it's a blockchain: write real cryptographic hashing, block validation, or transaction logic
  - If it's a collab editor: write real CRDT operations, WebSocket handlers, or OT algorithms
  - If it's an AI tool: write real API integrations, analysis logic, or ML pipeline code
- Use proper data structures, error handling, and type annotations
- Commit message must describe the EXACT feature implemented

Respond in this EXACT format:
FILE_PATH: src/lexer/tokenizer.py
COMMIT_MESSAGE: feat: implement tokenizer with full token type support
CODE_START
(complete working code here)
CODE_END"""

    return _parse_file_format(_ask(prompt))

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
    stack = project.get('stack', project.get('language', ''))
    title = project.get('title', '')
    description = project.get('description', '')
    existing = project.get('files', [])[:10]

    prompt = f"""You are an expert {stack} developer adding a new feature to a real open source project.

Project: {title}
Description: {description}
Stack: {stack}
Existing files: {', '.join(existing)}

Add a NEW real feature or module. Not a fix - actual new functionality specific to this project:
- Language/compiler project: add a new built-in function, operator, or optimization pass
- Database project: add a new query type, index structure, or replication feature
- Blockchain project: add a new transaction type, merkle tree, or P2P networking
- Collab editor: add syntax highlighting, user presence, or version history
- AI tool: add a new analysis type, integration, or reporting feature
- Other: add the most impactful missing feature

Rules:
- Real working code, minimum 60 lines
- Must actually implement the feature, no placeholders
- Specific commit message describing exactly what was added

Respond in this EXACT format:
FILE_PATH: src/feature/new_module.py
COMMIT_MESSAGE: feat: add specific feature name
CODE_START
(complete working code)
CODE_END"""

    return _parse_file_format(_ask(prompt))

def generate_leetcode_solution(problem: dict, difficulty: str, lang: str = "python3") -> str:
    title = problem.get("title", "")
    content = (problem.get("content", "") or "")[:400]
    snippet = next((s["code"] for s in (problem.get("codeSnippets") or []) if s["langSlug"] == lang), "")
    prompt = f"""Solve this LeetCode problem correctly in {lang}. Return ONLY the code, no explanation.

Problem: {title}
{content}

Code template:
{snippet}"""
    return _ask(prompt)

def chat_with_context(message: str, context: str) -> str:
    system = "You are the LazyBee AI assistant. LazyBee automates GitHub commits, builds CS projects daily, and solves LeetCode problems. Be concise and direct."
    return _ask(f"{system}\n\n{context}\n\nUser: {message}")
