"""
SQL Query Debugger & Optimizer — OpenEnv Environment
======================================================
A real-world environment where an AI agent is given broken, inefficient,
or insecure SQL queries and must:
  - Fix syntax errors
  - Correct logical bugs (wrong JOIN, missing GROUP BY, etc.)
  - Optimize for performance (remove N+1 patterns, add proper indexes hints)
  - Detect & fix SQL injection vulnerabilities

This is a task real data analysts and backend engineers do every single day.

Tasks:
  easy   — Fix obvious syntax errors in simple SELECT queries
  medium — Fix logic bugs (wrong JOINs, incorrect aggregations, missing clauses)
  hard   — Fix + optimize + secure (injection detection, N+1 queries, subquery rewrites)

Why this beats other environments:
  - 100% deterministic graders (execute real SQL in SQLite, compare results)
  - Rich partial rewards at every step (syntax → logic → performance → security)
  - Real engineering pain point that Meta/HF engineers deal with daily
  - Novel domain — not in OpenEnv Hub yet
"""

from __future__ import annotations

import re
import sqlite3
import textwrap
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Database Schema (in-memory SQLite — fully reproducible)
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department TEXT NOT NULL,
    salary REAL NOT NULL,
    hire_date TEXT NOT NULL,
    manager_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','completed','cancelled')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0
);
"""

SEED_SQL = """
INSERT INTO users VALUES
(1,'Alice Chen','alice@co.com','Engineering',95000,'2021-03-01',NULL),
(2,'Bob Smith','bob@co.com','Engineering',82000,'2022-06-15',1),
(3,'Carol Jones','carol@co.com','Marketing',74000,'2020-01-10',NULL),
(4,'Dan Park','dan@co.com','Engineering',91000,'2019-08-22',1),
(5,'Eva Liu','eva@co.com','Marketing',68000,'2023-02-28',3),
(6,'Frank Wu','frank@co.com','HR',61000,'2021-11-05',NULL),
(7,'Grace Kim','grace@co.com','Engineering',103000,'2018-05-14',1),
(8,'Hank Patel','hank@co.com','Marketing',72000,'2022-09-30',3);

INSERT INTO products VALUES
(1,'Laptop Pro','Electronics',1299.99,45),
(2,'Wireless Mouse','Electronics',29.99,200),
(3,'Standing Desk','Furniture',549.00,30),
(4,'Monitor 4K','Electronics',699.99,60),
(5,'Ergonomic Chair','Furniture',399.00,25),
(6,'USB Hub','Electronics',49.99,150);

INSERT INTO orders VALUES
(1,1,'Laptop Pro',1299.99,'completed','2024-01-15'),
(2,2,'Wireless Mouse',29.99,'completed','2024-01-20'),
(3,1,'Monitor 4K',699.99,'completed','2024-02-01'),
(4,3,'Ergonomic Chair',399.00,'pending','2024-02-10'),
(5,4,'Standing Desk',549.00,'completed','2024-02-14'),
(6,2,'USB Hub',49.99,'cancelled','2024-02-20'),
(7,5,'Wireless Mouse',29.99,'completed','2024-03-01'),
(8,7,'Laptop Pro',1299.99,'completed','2024-03-05'),
(9,1,'USB Hub',49.99,'completed','2024-03-10'),
(10,3,'Laptop Pro',1299.99,'pending','2024-03-15'),
(11,4,'Wireless Mouse',29.99,'completed','2024-03-18'),
(12,6,'Ergonomic Chair',399.00,'completed','2024-03-20');
"""

def make_db() -> sqlite3.Connection:
    """Create fresh in-memory SQLite database."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SEED_SQL)
    conn.commit()
    return conn

def run_query(conn: sqlite3.Connection, sql: str) -> Tuple[List[Dict], Optional[str]]:
    """Execute SQL, return (rows, error). rows=[] on error."""
    try:
        cur = conn.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        return rows, None
    except Exception as e:
        return [], str(e)

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class SQLChallenge(BaseModel):
    id: str
    description: str          # What the query SHOULD do (plain English)
    broken_sql: str           # The buggy SQL given to the agent
    expected_row_count: int   # How many rows the correct query returns
    expected_columns: List[str]  # Column names of correct output
    hint: str                 # Nudge without giving the answer
    difficulty: str
    bugs: List[str]           # Human-readable bug descriptions (shown to agent)


class Observation(BaseModel):
    challenge: SQLChallenge
    schema_info: str          # DDL so agent knows table structure
    current_step: int
    max_steps: int
    task: str
    previous_attempts: List[Dict[str, Any]] = Field(default_factory=list)
    instructions: str


class Action(BaseModel):
    challenge_id: str
    fixed_sql: str                        # The agent's corrected SQL
    explanation: Optional[str] = None     # Why the original was wrong
    detected_issues: List[str] = Field(default_factory=list)  # e.g. ["missing_group_by","sql_injection"]


class Reward(BaseModel):
    value: float
    breakdown: Dict[str, float]


# ---------------------------------------------------------------------------
# Challenges Dataset
# ---------------------------------------------------------------------------

CHALLENGES: List[Dict] = [

    # =========== EASY ===========
    {
        "id": "sq001",
        "difficulty": "easy",
        "description": "Get the names and salaries of all employees in the Engineering department, ordered by salary descending.",
        "broken_sql": """
            SELCT name, salary FORM users
            WHER department = 'Engineering'
            ORDER BY salary DESC
        """.strip(),
        "expected_row_count": 4,
        "expected_columns": ["name", "salary"],
        "hint": "Look carefully at the SQL keywords — any typos?",
        "bugs": [
            "Typo: SELCT should be SELECT",
            "Typo: FORM should be FROM",
            "Typo: WHER should be WHERE",
        ],
    },
    {
        "id": "sq002",
        "difficulty": "easy",
        "description": "Count how many orders each user has made, showing user_id and their order count.",
        "broken_sql": """
            SELECT user_id, COUNT(*) as order_count
            FROM orders
        """.strip(),
        "expected_row_count": 7,
        "expected_columns": ["user_id", "order_count"],
        "hint": "When using COUNT with a non-aggregate column, something is missing.",
        "bugs": ["Missing GROUP BY user_id — without it, SQLite returns only 1 row instead of per-user counts"],
    },
    {
        "id": "sq003",
        "difficulty": "easy",
        "description": "Get the total revenue from all completed orders.",
        "broken_sql": """
            SELECT SUM(amount) AS total_revenue
            FROM orders
            WHERE status = 'complete'
        """.strip(),
        "expected_row_count": 1,
        "expected_columns": ["total_revenue"],
        "hint": "Check the exact value used in the WHERE condition against the schema.",
        "bugs": ["Wrong status value: 'complete' should be 'completed' (as defined in the CHECK constraint)"],
    },

    # =========== MEDIUM ===========
    {
        "id": "sq004",
        "difficulty": "medium",
        "description": "Get each user's name and the total amount they've spent on completed orders. Include users who have no completed orders (show 0 for them).",
        "broken_sql": """
            SELECT u.name, SUM(o.amount) AS total_spent
            FROM orders o
            INNER JOIN users u ON u.id = o.user_id
            WHERE o.status = 'completed'
            GROUP BY u.name
        """.strip(),
        "expected_row_count": 8,
        "expected_columns": ["name", "total_spent"],
        "hint": "The problem statement says 'Include users who have no completed orders' — does INNER JOIN do that?",
        "bugs": [
            "INNER JOIN excludes users with no completed orders — should be LEFT JOIN from users to orders",
            "The WHERE clause further removes non-matching rows — it should move to an ON clause or be handled with COALESCE",
        ],
    },
    {
        "id": "sq005",
        "difficulty": "medium",
        "description": "Find all Engineering employees who earn more than the average salary of their own department.",
        "broken_sql": """
            SELECT name, salary
            FROM users
            WHERE department = 'Engineering'
            AND salary > (SELECT AVG(salary) FROM users)
        """.strip(),
        "expected_row_count": 2,
        "expected_columns": ["name", "salary"],
        "hint": "The subquery calculates something — but is it the average of the right group?",
        "bugs": [
            "Subquery uses AVG(salary) across ALL departments, not just Engineering",
            "Fix: WHERE department = 'Engineering' AND salary > (SELECT AVG(salary) FROM users WHERE department = 'Engineering')",
        ],
    },
    {
        "id": "sq006",
        "difficulty": "medium",
        "description": "Get the top 3 products by total revenue from completed orders.",
        "broken_sql": """
            SELECT product, SUM(amount) AS revenue
            FROM orders
            WHERE status = 'completed'
            GROUP BY product
            ORDER BY amount DESC
            LIMIT 3
        """.strip(),
        "expected_row_count": 3,
        "expected_columns": ["product", "revenue"],
        "hint": "The ORDER BY is using a column — but which column should you order by to rank by total revenue?",
        "bugs": [
            "ORDER BY amount DESC orders by the raw column, not the aggregated revenue",
            "Fix: ORDER BY revenue DESC (or ORDER BY SUM(amount) DESC)",
        ],
    },

    # =========== HARD ===========
    {
        "id": "sq007",
        "difficulty": "hard",
        "description": "For each department, show the department name, number of employees, average salary, and highest salary. Only include departments with more than 1 employee.",
        "broken_sql": """
            SELECT department,
                   COUNT(id),
                   AVG(salary) AS avg_salary,
                   MAX(salary)
            FROM users
            GROUP BY department
            HAVING COUNT(*) > 1
            ORDER BY avg_salary
        """.strip(),
        "expected_row_count": 2,
        "expected_columns": ["department", "COUNT(id)", "avg_salary", "MAX(salary)"],
        "hint": "The query runs but has style/clarity issues AND a subtle ordering issue. Also check column aliases.",
        "bugs": [
            "COUNT(id) and MAX(salary) have no aliases — hard to read, unpredictable column names in results",
            "ORDER BY avg_salary is ascending by default — descending is typically more useful for salary reports",
            "Minor: COUNT(id) should be COUNT(*) or COUNT(1) for clarity",
        ],
    },
    {
        "id": "sq008",
        "difficulty": "hard",
        "description": "SECURITY: A web app builds this query using user input for `dept`. Find and fix the SQL injection vulnerability. The query should return employee names for a given department.",
        "broken_sql": """
            SELECT name FROM users WHERE department = '\" + dept + \"'
        """.strip(),
        "expected_row_count": 4,
        "expected_columns": ["name"],
        "hint": "String concatenation of user input into SQL = SQL injection. The fix is parameterized queries.",
        "bugs": [
            "SQL injection vulnerability: user input `dept` is directly concatenated into the query string",
            "Fix: Use parameterized query: SELECT name FROM users WHERE department = ? with parameters=(dept,)",
            "For this environment, rewrite as: SELECT name FROM users WHERE department = 'Engineering'",
        ],
    },
    {
        "id": "sq009",
        "difficulty": "hard",
        "description": "Rewrite this inefficient N+1 style subquery pattern into a single efficient JOIN query. Get user names and their most recent order's product name and amount.",
        "broken_sql": """
            SELECT
                u.name,
                (SELECT product FROM orders WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) AS last_product,
                (SELECT amount FROM orders WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) AS last_amount
            FROM users u
        """.strip(),
        "expected_row_count": 8,
        "expected_columns": ["name", "last_product", "last_amount"],
        "hint": "Two correlated subqueries hit the orders table twice per user. Use a CTE or subquery with ROW_NUMBER() or a ranked join instead.",
        "bugs": [
            "N+1 query pattern: two correlated subqueries each scan orders once per user = O(n) full scans",
            "Fix: Use a single subquery that gets the latest order per user, then LEFT JOIN it",
        ],
    },
]

CHALLENGE_MAP: Dict[str, Dict] = {c["id"]: c for c in CHALLENGES}

# Correct reference SQL for each challenge (used internally for grading)
REFERENCE_SQL: Dict[str, str] = {
    "sq001": "SELECT name, salary FROM users WHERE department = 'Engineering' ORDER BY salary DESC",
    "sq002": "SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id",
    "sq003": "SELECT SUM(amount) AS total_revenue FROM orders WHERE status = 'completed'",
    "sq004": """
        SELECT u.name, COALESCE(SUM(o.amount), 0) AS total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed'
        GROUP BY u.id, u.name
    """,
    "sq005": """
        SELECT name, salary FROM users
        WHERE department = 'Engineering'
        AND salary > (SELECT AVG(salary) FROM users WHERE department = 'Engineering')
    """,
    "sq006": """
        SELECT product, SUM(amount) AS revenue
        FROM orders WHERE status = 'completed'
        GROUP BY product ORDER BY revenue DESC LIMIT 3
    """,
    "sq007": """
        SELECT department, COUNT(*) AS employee_count, AVG(salary) AS avg_salary, MAX(salary) AS max_salary
        FROM users GROUP BY department HAVING COUNT(*) > 1 ORDER BY avg_salary DESC
    """,
    "sq008": "SELECT name FROM users WHERE department = 'Engineering'",
    "sq009": """
        SELECT u.name, latest.product AS last_product, latest.amount AS last_amount
        FROM users u
        LEFT JOIN (
            SELECT user_id, product, amount,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
            FROM orders
        ) latest ON latest.user_id = u.id AND latest.rn = 1
    """,
}

# =========== Task Config ===========
TASK_CONFIGS = {
    "easy":   {"challenge_ids": ["sq001", "sq002", "sq003"], "max_steps": 3},
    "medium": {"challenge_ids": ["sq004", "sq005", "sq006"], "max_steps": 3},
    "hard":   {"challenge_ids": ["sq007", "sq008", "sq009"], "max_steps": 3},
}

SCHEMA_INFO = textwrap.dedent("""
    TABLE users(id, name, email, department, salary, hire_date, manager_id)
      - department: 'Engineering' | 'Marketing' | 'HR'
      - salary: REAL
      - manager_id: FK → users.id (nullable)

    TABLE orders(id, user_id, product, amount, status, created_at)
      - status: 'pending' | 'completed' | 'cancelled'
      - user_id: FK → users.id

    TABLE products(id, name, category, price, stock)
      - category: 'Electronics' | 'Furniture'
""").strip()

INSTRUCTIONS = {
    "easy": (
        "EASY TASK — Fix SQL Syntax Errors\n"
        "Each challenge gives you a broken SQL query with typos or missing keywords.\n"
        "Fix the SQL so it runs correctly and returns the expected results.\n"
        "Set fixed_sql to your corrected query."
    ),
    "medium": (
        "MEDIUM TASK — Fix Logic Bugs\n"
        "Each query runs without error but produces WRONG results due to logic bugs:\n"
        "wrong JOIN type, wrong column in ORDER BY, missing GROUP BY, wrong subquery scope.\n"
        "Fix the SQL to return the correct, expected result set."
    ),
    "hard": (
        "HARD TASK — Fix, Optimize & Secure\n"
        "Each query has logic bugs AND performance/security issues:\n"
        "SQL injection vulnerabilities, N+1 correlated subqueries, missing aliases.\n"
        "Fix ALL issues. For SQL injection: rewrite using safe parameterized form.\n"
        "For N+1 queries: rewrite as a single efficient JOIN. List all detected_issues."
    ),
}


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class SQLDebuggerEnv:
    """OpenEnv-compliant SQL Debugger & Optimizer environment."""

    def __init__(self, task: str = "easy"):
        if task not in TASK_CONFIGS:
            raise ValueError(f"Unknown task '{task}'. Choose: {list(TASK_CONFIGS)}")
        self.task = task
        self._cfg = TASK_CONFIGS[task]
        self._challenges: List[SQLChallenge] = []
        self._step = 0
        self._done = False
        self._history: List[Dict] = []
        self._results: Dict[str, Dict] = {}
        self._db: Optional[sqlite3.Connection] = None
        self.reset()

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> Observation:
        self._db = make_db()
        self._challenges = [
            SQLChallenge(**CHALLENGE_MAP[cid])
            for cid in self._cfg["challenge_ids"]
        ]
        self._step = 0
        self._done = False
        self._history = []
        self._results = {}
        return self._make_observation(0)

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict]:
        if self._done:
            raise RuntimeError("Episode done. Call reset().")

        self._step += 1
        challenge = self._find_challenge(action.challenge_id)
        idx = self._challenge_index(action.challenge_id)

        if challenge is None or idx is None:
            reward = -0.1
            info = {"error": "invalid challenge_id", "breakdown": {}}
        else:
            breakdown = self._grade(challenge, action)
            reward = max(0.0, min(1.0, sum(breakdown.values())))
            info = {"breakdown": breakdown, "step": self._step}
            self._results[action.challenge_id] = {
                "action": action.model_dump(),
                "reward": reward,
                "breakdown": breakdown,
            }

        self._history.append({
            "step": self._step,
            "challenge_id": action.challenge_id,
            "reward": reward,
            "info": info,
        })

        next_idx = min(idx + 1 if idx is not None else 0, len(self._challenges) - 1)
        self._done = (
            self._step >= self._cfg["max_steps"]
            or len(self._results) >= len(self._challenges)
        )

        obs = self._make_observation(next_idx if not self._done else idx)
        return obs, round(reward, 4), self._done, info

    def state(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "step": self._step,
            "done": self._done,
            "challenges_total": len(self._challenges),
            "challenges_solved": len(self._results),
            "history": self._history,
        }

    def close(self):
        if self._db:
            self._db.close()

    def episode_score(self) -> float:
        if not self._results:
            return 0.0
        total = sum(r["reward"] for r in self._results.values())
        return round(total / len(self._challenges), 4)

    # ------------------------------------------------------------------
    # Grading (deterministic — runs real SQL)
    # ------------------------------------------------------------------

    def _grade(self, challenge: SQLChallenge, action: Action) -> Dict[str, float]:
        bd: Dict[str, float] = {}
        fixed_sql = action.fixed_sql.strip()

        # 1. Syntax check — does the fixed SQL run at all?
        rows, error = run_query(self._db, fixed_sql)
        if error:
            bd["syntax_error"] = 0.0
            bd["parse_penalty"] = -0.05
            return bd
        bd["syntax_ok"] = 0.20

        # 2. Row count match
        ref_rows, _ = run_query(self._db, REFERENCE_SQL[challenge.id])
        if len(rows) == len(ref_rows):
            bd["row_count_correct"] = 0.25
        elif abs(len(rows) - len(ref_rows)) <= 1:
            bd["row_count_close"] = 0.10

        # 3. Column names match
        if rows and ref_rows:
            pred_cols = set(rows[0].keys())
            ref_cols = set(ref_rows[0].keys())
            col_overlap = len(pred_cols & ref_cols) / max(len(ref_cols), 1)
            bd["columns"] = round(col_overlap * 0.15, 4)

        # 4. Data correctness — compare sorted string representations
        if rows and ref_rows and len(rows) == len(ref_rows):
            pred_str = sorted(str(sorted(r.items())) for r in rows)
            ref_str  = sorted(str(sorted(r.items())) for r in ref_rows)
            if pred_str == ref_str:
                bd["data_exact"] = 0.30
            else:
                # Partial: at least first-column values match
                pred_first = sorted(str(list(r.values())[0]) for r in rows)
                ref_first  = sorted(str(list(r.values())[0]) for r in ref_rows)
                if pred_first == ref_first:
                    bd["data_partial"] = 0.15

        # 5. Security grading (hard task: injection)
        if challenge.id == "sq008":
            sql_lower = fixed_sql.lower()
            injection_pattern = "dept"
            if injection_pattern not in fixed_sql and "concat" not in sql_lower:
                bd["injection_removed"] = 0.10
            # Reward parameterized hint in explanation
            if action.explanation and any(
                kw in action.explanation.lower()
                for kw in ["parameterized", "prepared", "placeholder", "?", "injection"]
            ):
                bd["security_explanation"] = 0.05

        # 6. Optimization grading (hard task: N+1)
        if challenge.id == "sq009":
            sql_lower = fixed_sql.lower()
            # Penalize correlated subquery pattern still present
            if "select" in sql_lower[sql_lower.find("select")+6:]:  # nested SELECT
                subq_count = sql_lower.count("select")
                if subq_count <= 2:  # CTE or single subquery = OK
                    bd["optimization_ok"] = 0.05
                else:
                    bd["n_plus_1_penalty"] = -0.10
            if "join" in sql_lower:
                bd["uses_join"] = 0.05

        # 7. Explanation quality bonus
        if action.explanation and len(action.explanation.split()) >= 8:
            bd["explanation_bonus"] = 0.05

        # 8. Bug detection quality (hard task)
        if self.task == "hard" and action.detected_issues:
            bd["issues_detected"] = min(0.05, len(action.detected_issues) * 0.02)

        return bd

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_challenge(self, cid: str) -> Optional[SQLChallenge]:
        for c in self._challenges:
            if c.id == cid:
                return c
        return None

    def _challenge_index(self, cid: str) -> Optional[int]:
        for i, c in enumerate(self._challenges):
            if c.id == cid:
                return i
        return None

    def _make_observation(self, idx: int) -> Observation:
        challenge = self._challenges[min(idx, len(self._challenges) - 1)]
        return Observation(
            challenge=challenge,
            schema_info=SCHEMA_INFO,
            current_step=self._step,
            max_steps=self._cfg["max_steps"],
            task=self.task,
            previous_attempts=[
                h for h in self._history
                if h["challenge_id"] == challenge.id
            ],
            instructions=INSTRUCTIONS[self.task],
        )