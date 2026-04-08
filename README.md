---
title: SQL Debugger & Optimizer
emoji: 🛠️
colorFrom: blue
colorTo: indigo
sdk: docker
app_file: app.py
pinned: false
---

# 🛠️ SQL Debugger & Optimizer — OpenEnv Environment

> 🚀 **NeuroHack — OpenEnv Submission**
> A real-world reinforcement learning environment where an AI agent debugs broken SQL queries using **deterministic SQLite execution** — no LLM-based scoring.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Why This Wins](#why-this-wins)
- [Live Demo](#live-demo)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Run Locally](#run-locally)
  - [Docker](#docker)
  - [API Example](#api-example)
- [Environment Details](#environment-details)
  - [Tasks](#tasks)
  - [Reward System](#reward-system)
  - [Performance](#performance)
- [License](#license)

---

## Overview

The **SQL Debugger & Optimizer** is an OpenEnv-compatible reinforcement learning environment where an AI agent receives broken SQL queries and must output corrected versions.

The agent receives:
- 🔴 A **broken SQL query**
- 🗂️ The **database schema**
- 📝 A **natural language description** of the intended behavior

It must output a **corrected SQL query**, which is then:
1. Executed against a real SQLite database
2. Compared against the reference (correct) query output
3. Scored with a layered reward from `0.0 → 1.0`

---

## Why This Wins

Unlike traditional LLM-evaluated systems:

| Feature | Description |
|--------|-------------|
| ✅ **100% Deterministic Grading** | Real SQLite execution — no subjective LLM scoring |
| ✅ **Layered Reward System** | Syntax → Logic → Data → Optimization |
| ✅ **Real-World Bugs** | JOIN errors, N+1 queries, SQL injection vulnerabilities |
| ✅ **Engineering Relevance** | Mirrors production database debugging scenarios |
| ✅ **OpenEnv-Compatible API** | Drop-in `/reset` and `/step` endpoints |

---

## Live Demo

Open the interactive UI at:

```
http://localhost:7860/ui
```

With the UI you can:
- Fix broken SQL queries interactively
- View the corrected SQL output
- See reward scores in real-time
- Track agent performance with graphs

---

## Project Structure

```
sql-debugger-env/
├── app.py                 # FastAPI server — /reset, /step, /ui endpoints
├── sql_debugger_env.py    # Core RL environment logic & SQLite execution
├── inference.py           # Agent inference utilities
├── openenv.yaml           # OpenEnv environment specification
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container build configuration
└── README.md              # This file
```

---

## Getting Started

### Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Then open: [http://localhost:7860/ui](http://localhost:7860/ui)

---

### Docker

```bash
# Build the image
docker build -t sql-debugger-env .

# Run the container
docker run -p 7860:7860 sql-debugger-env
```

---

### API Example

The environment exposes an OpenEnv-compatible REST API:

```python
import requests

# 1. Start a new episode
r = requests.post("http://localhost:7860/reset", json={"task": "medium"})
session_id = r.json()["session_id"]
obs = r.json()["observation"]

# 2. Submit a fix action
action = {
    "challenge_id": obs["challenge"]["id"],
    "fixed_sql": "SELECT users.id, orders.total FROM users JOIN orders ON users.id = orders.user_id",
    "explanation": "Fixed JOIN logic — was using wrong foreign key",
    "detected_issues": ["wrong_join"]
}

r = requests.post("http://localhost:7860/step", json={
    "session_id": session_id,
    "action": action
})

print(r.json()["reward"])   # e.g. 0.92
```

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Start a new episode. Accepts `{"task": "easy" \| "medium" \| "hard"}` |
| `POST` | `/step` | Submit a fix. Returns reward, done flag, and next observation |
| `GET`  | `/ui`   | Interactive web interface |

---

## Environment Details

### Tasks

| Difficulty | Bug Types |
|------------|-----------|
| 🟢 **Easy** | Syntax errors (`SELCT`, `FORM`, missing `WHERE`) |
| 🟡 **Medium** | JOIN logic errors, aggregation mistakes |
| 🔴 **Hard** | N+1 query patterns, optimization issues, complex aggregations |

---

### Reward System

Each submitted query is evaluated across multiple components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Syntax Correctness | `0.20` | Query parses and executes without error |
| Row Count Match | `0.25` | Output row count matches reference |
| Column Match | `0.15` | Returned columns match expected schema |
| Data Exact Match | `0.30` | Row-by-row data comparison |
| Security Fix | `0.10` | SQL injection or unsafe patterns resolved |
| Optimization | `0.05` | Query avoids N+1 or redundant scans |
| Explanation Quality | `0.05` | Detected issues and explanation provided |
| **Total** | **1.00** | |

---

### Performance

Benchmarks from the reference agent (`inference.py`):

| Task | Score |
|------|-------|
| Easy | ~0.90 |
| Medium | ~0.90 |
| Hard | ~0.76 |
| **Average** | 🚀 **~0.85** |

---

## License

This project is licensed under the **MIT License** — see [`LICENSE`](LICENSE) for details.

---

<div align="center">
  Built for <strong>NeuroHack</strong> · OpenEnv Track · 2025
</div>