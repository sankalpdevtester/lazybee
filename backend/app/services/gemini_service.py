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
            content = code_match.group(1).strip()
            # Strip markdown backticks
            content = re.sub(r'^```[\w]*\n', '', content)
            content = re.sub(r'\n```$', '', content).strip()
            return {
                "file_path": file_path.group(1).strip(),
                "content": content,
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
    prompt = f"""You are a senior software engineer. Suggest ONE real CS project for a developer portfolio.

Requirements:
- Must be a genuinely useful project someone would actually use or run
- Realistic scope: completable and FULLY RUNNABLE in 7 days of commits
- Language/Stack: {language} - use the single most standard framework for that stack
- Avoid these existing projects: {avoid}
- Pick projects where the core loop is simple: a CLI tool, a REST API, a small web app, a library
- DO NOT pick compiler/database/blockchain/OS - those are too complex to be runnable in 7 days

Good examples by stack:
- Python: FastAPI CRUD app, CLI data tool, scraper with export, automation script suite
- TypeScript/Node: Express REST API, CLI utility, React dashboard with real data
- Go: HTTP server, CLI tool, file processor
- Rust: CLI tool, file format parser
- React: dashboard app, portfolio site, utility web app

Respond ONLY in this exact JSON format, no extra text:
{{
  "name": "repo-name-in-kebab-case",
  "title": "Human Readable Title",
  "description": "One sentence description of what it does and who uses it.",
  "language": "{language}",
  "stack": "specific framework and tools e.g. FastAPI + SQLite + Python 3.11",
  "run_command": "exact command to run the project e.g. uvicorn main:app or npm run dev or cargo run",
  "install_command": "exact install command e.g. pip install -r requirements.txt or npm install",
  "entry_point": "main entry file e.g. main.py or src/index.ts or cmd/main.go",
  "scaffold_files": [
    {{"path": "requirements.txt", "description": "dependencies"}},
    {{"path": "main.py", "description": "entry point"}},
    {{"path": ".env.example", "description": "env template"}}
  ],
  "features": ["feature 1", "feature 2", "feature 3", "feature 4", "feature 5"],
  "roadmap": [
    "Day 1: Project scaffold - entry point, config, dependencies, .env.example, basic hello world that runs",
    "Day 2: Core data models and database/storage layer",
    "Day 3: Core feature 1 - fully working end to end",
    "Day 4: Core feature 2 - fully working end to end",
    "Day 5: Core feature 3 + error handling",
    "Day 6: Tests and documentation",
    "Day 7: Final polish, deployment config, updated README with real usage examples"
  ]
}}"""
    return _parse_json(_ask(prompt))


def generate_scaffold(project: dict) -> list[dict]:
    """Generate ALL runnable scaffold files upfront on day 1 so the project works from the start."""
    stack = project.get("stack", project.get("language", ""))
    title = project.get("title", "")
    description = project.get("description", "")
    run_cmd = project.get("run_command", "")
    install_cmd = project.get("install_command", "")
    entry = project.get("entry_point", "main.py")
    scaffold_files = project.get("scaffold_files", [])
    features = project.get("features", [])

    files_to_generate = "\n".join(f"- {f['path']}: {f['description']}" for f in scaffold_files)

    prompt = f"""You are an expert {stack} developer. Generate ALL scaffold files for this project so it is IMMEDIATELY RUNNABLE.

Project: {title}
Description: {description}
Stack: {stack}
Entry point: {entry}
Install: {install_cmd}
Run: {run_cmd}
Features to build: {', '.join(features)}

Files needed:
{files_to_generate}

Rules:
- Every file must be complete and real — no TODOs, no placeholders, no "implement this later"
- The project must actually run after `{install_cmd}` and `{run_cmd}`
- Dependencies file (requirements.txt / package.json / go.mod / Cargo.toml) must list real pinned versions
- Entry point must have a working main function / server / CLI handler
- .env.example must list every env var with a clear description comment
- Config files (tsconfig, vite.config, etc) must be correct and complete
- If it's a web app, include a basic working route that returns real data
- If it's a CLI, include at least one working command

Respond with ALL files in this EXACT repeated format (one block per file, no extra text between them):
FILE_PATH: requirements.txt
COMMIT_MESSAGE: chore: add dependencies
CODE_START
(file content)
CODE_END
FILE_PATH: main.py
COMMIT_MESSAGE: feat: project entry point
CODE_START
(file content)
CODE_END"""

    raw = _ask(prompt)
    # Parse multiple file blocks
    results = []
    pattern = re.compile(
        r'FILE_PATH:\s*(.+?)\nCOMMIT_MESSAGE:\s*(.+?)\nCODE_START\s*\n(.*?)\nCODE_END',
        re.DOTALL
    )
    for m in pattern.finditer(raw):
        content = m.group(3).strip()
        content = re.sub(r'^```[\w]*\n', '', content)
        content = re.sub(r'\n```$', '', content).strip()
        results.append({
            "file_path": m.group(1).strip(),
            "commit_message": m.group(2).strip(),
            "content": content,
        })
    return results

def generate_daily_commit(project: dict, day: int, existing_files: list[str]) -> dict:
    """Generate a single file commit for a project — fallback when multi-file fails."""
    roadmap = project.get("roadmap", [])
    step = roadmap[min(day - 1, len(roadmap) - 1)] if roadmap else f"Day {day}: continue development"
    stack = project.get("stack", project.get("language", ""))
    title = project.get("title", "")
    description = project.get("description", "")
    entry = project.get("entry_point", "")
    run_cmd = project.get("run_command", "")

    prompt = f"""You are an expert {stack} developer working on a real open source project that is ALREADY RUNNING.

Project: {title}
Description: {description}
Stack: {stack}
Entry point: {entry}
Run command: {run_cmd}
Files already in repo: {', '.join(existing_files) if existing_files else 'only README.md'}
Today's goal (Day {day}): {step}

Write ONE complete file that implements today's goal.
Rules:
- Real working {stack} code, no TODOs, no placeholders
- Integrates with existing files listed above
- Minimum 60 lines of actual logic
- File path fits the existing project structure
- Do NOT duplicate any file in the existing list

Respond in this EXACT format:
FILE_PATH: src/routes/users.py
COMMIT_MESSAGE: feat: add user CRUD endpoints
CODE_START
(complete working code)
CODE_END"""

    return _parse_file_format(_ask(prompt))


def generate_multi_file_commit(project: dict, day: int, existing_files: list[str]) -> list[dict]:
    """Generate 3-5 real files at once for a project update — looks like a real dev session."""
    stack = project.get("stack", project.get("language", ""))
    title = project.get("title", "")
    description = project.get("description", "")
    entry = project.get("entry_point", "")
    roadmap = project.get("roadmap", [])
    step = roadmap[min(day - 1, len(roadmap) - 1)] if roadmap else f"Day {day}: continue development"
    features = project.get("features", [])

    prompt = f"""You are an expert {stack} developer working on a real open source project.

Project: {title}
Description: {description}
Stack: {stack}
Entry point: {entry}
Existing files: {', '.join(existing_files[:20]) if existing_files else 'only README.md'}
Today's goal: {step}
Project features: {', '.join(features[:5])}

Generate 3 to 5 NEW files that together implement a meaningful feature batch for this project.
Think like a real developer doing a focused work session — multiple related files that work together.

Examples of good file batches:
- An API router + its models + its tests
- A React page + its custom hook + its API client function  
- A CLI command module + its helper utilities + its config
- A service class + its interface/types + its error handlers

Hard rules for EVERY file:
- Real, working {stack} code — no TODOs, no placeholders, no empty functions
- Must integrate with existing files listed above
- Minimum 40 lines of actual logic per file
- Each file must serve a distinct purpose
- File paths must fit the project structure naturally
- Do NOT duplicate any file in: {', '.join(existing_files[:10])}

Respond with ALL files in this EXACT repeated format:
FILE_PATH: src/routes/users.py
COMMIT_MESSAGE: feat: add user management endpoints
CODE_START
(complete working code)
CODE_END
FILE_PATH: src/models/user.py
COMMIT_MESSAGE: feat: add User model with validation
CODE_START
(complete working code)
CODE_END"""

    raw = _ask(prompt)
    results = []
    pattern = re.compile(
        r'FILE_PATH:\s*(.+?)\nCOMMIT_MESSAGE:\s*(.+?)\nCODE_START\s*\n(.*?)\nCODE_END',
        re.DOTALL
    )
    for m in pattern.finditer(raw):
        content = m.group(3).strip()
        content = re.sub(r'^```[\w]*\n', '', content)
        content = re.sub(r'\n```$', '', content).strip()
        if len(content) > 20:
            results.append({
                "file_path": m.group(1).strip(),
                "commit_message": m.group(2).strip(),
                "content": content,
            })
    return results


    roadmap = project.get("roadmap", [])
    step = roadmap[min(day - 1, len(roadmap) - 1)] if roadmap else f"Day {day}: continue development"
    stack = project.get("stack", project.get("language", ""))
    title = project.get("title", "")
    description = project.get("description", "")
    entry = project.get("entry_point", "")
    run_cmd = project.get("run_command", "")

    prompt = f"""You are an expert {stack} developer working on a real open source project that is ALREADY RUNNING.

Project: {title}
Description: {description}
Stack: {stack}
Entry point: {entry}
Run command: {run_cmd}
Files already in repo: {', '.join(existing_files) if existing_files else 'only README.md'}

Today's goal (Day {day}): {step}

Write ONE complete file that implements today's goal.

Hard rules:
- The file must be real, working {stack} code — not a skeleton, not a demo
- It must import from / integrate with the existing files listed above
- No TODO comments, no placeholder functions, no "pass" or empty bodies
- Use real libraries that are already in the project's dependency file
- Minimum 60 lines of actual logic
- The commit message must describe the exact feature added (not "add feature" — be specific)
- File path must fit naturally into the existing project structure

Examples of BAD output:
- def process(): pass  # TODO implement
- // Coming soon
- return null  # implement later

Examples of GOOD output:
- A real FastAPI router with working endpoints and DB queries
- A real React component with state, props, real API calls
- A real CLI command with argument parsing and real logic
- A real utility module with tested functions

Respond in this EXACT format:
FILE_PATH: src/routes/users.py
COMMIT_MESSAGE: feat: add user CRUD endpoints with pagination and filtering
CODE_START
(complete working code)
CODE_END"""

    return _parse_file_format(_ask(prompt))

def generate_readme(project: dict) -> str:
    prompt = f"""Write a complete professional README.md for this project:
Title: {project['title']}
Description: {project['description']}
Stack: {project.get('stack', project.get('language', ''))}
Install: {project.get('install_command', '')}
Run: {project.get('run_command', '')}
Features: {', '.join(project.get('features', []))}

Include ALL of these sections with real content (not placeholders):
1. Badges (language, license)
2. What it does (2-3 sentences)
3. Features list
4. Requirements (exact versions)
5. Installation (exact commands someone can copy-paste)
6. Usage with real example commands and expected output
7. Environment variables table with description for each
8. Project structure tree
9. Contributing
10. License (MIT)

Return ONLY raw markdown. No backtick wrapper around the whole thing."""
    return _ask(prompt)


def generate_maintenance_commit(project: dict) -> dict:
    stack = project.get('stack', project.get('language', ''))
    title = project.get('title', '')
    description = project.get('description', '')
    existing = project.get('files', [])
    entry = project.get('entry_point', '')

    prompt = f"""You are an expert {stack} developer adding a NEW feature to a real running project.

Project: {title}
Description: {description}
Stack: {stack}
Entry point: {entry}
Existing files: {', '.join(existing[:15])}

Add one new feature that:
- Is genuinely useful to the project
- Integrates with the existing files listed
- Is completely implemented with no TODOs or placeholders
- Is a file that doesn't exist yet in the repo

Good examples:
- A new API endpoint file with real route handlers
- A utility/helper module with real functions used by the main app
- A test file with real test cases
- A new CLI command module
- A middleware, validator, or config module

Respond in this EXACT format:
FILE_PATH: src/utils/cache.py
COMMIT_MESSAGE: feat: add in-memory cache with TTL for API responses
CODE_START
(complete working code, minimum 50 lines)
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
