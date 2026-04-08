"""
inference.py — SQL Debugger & Optimizer Agent
===============================================
Runs an LLM against all 3 tasks. Emits mandatory [START]/[STEP]/[END] logs.

Env vars:
    API_BASE_URL   LLM endpoint  (default: https://router.huggingface.co/v1)
    MODEL_NAME     Model name    (default: Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN       API key
"""
from __future__ import annotations
import json, os, textwrap
from typing import Dict, List, Optional
from openai import OpenAI
from sql_debugger_env import Action, SQLDebuggerEnv

API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK    = "sql-debugger-agent"
TASKS        = ["easy", "medium", "hard"]

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert SQL debugger and optimizer.
    You will be given a broken SQL query, the database schema, and a description
    of what the query SHOULD do. Your job is to fix ALL bugs.

    Always respond with ONLY a JSON object — no markdown, no explanation outside JSON:
    {
        "challenge_id": "<id>",
        "fixed_sql": "<your corrected SQL query>",
        "explanation": "<brief explanation of what was wrong>",
        "detected_issues": ["issue1", "issue2"]
    }

    Common bug types to look for:
    - Syntax typos (SELCT, FORM, WHER)
    - Missing GROUP BY when using aggregate functions with non-aggregate columns
    - Wrong JOIN type (INNER vs LEFT)
    - Wrong column in ORDER BY (ordering by raw column instead of aggregate alias)
    - Subquery referencing wrong scope (AVG of all rows instead of filtered group)
    - SQL injection (string concatenation of user input — fix with parameterized form)
    - N+1 correlated subqueries (rewrite as JOIN with subquery or CTE)

    Output ONLY the JSON. Nothing else.
""").strip()


def build_prompt(obs_dict: dict) -> str:
    c = obs_dict["challenge"]
    return textwrap.dedent(f"""
        TASK: {obs_dict['task']}
        INSTRUCTIONS: {obs_dict['instructions']}

        DATABASE SCHEMA:
        {obs_dict['schema_info']}

        CHALLENGE ID: {c['id']}
        GOAL: {c['description']}
        DIFFICULTY: {c['difficulty']}

        KNOWN BUGS (hints):
        {chr(10).join('- ' + b for b in c['bugs'])}

        HINT: {c['hint']}

        BROKEN SQL TO FIX:
        {c['broken_sql']}

        Output only JSON with keys: challenge_id, fixed_sql, explanation, detected_issues
    """).strip()


def run_task(task_name: str) -> dict:
    env = SQLDebuggerEnv(task=task_name)
    obs_obj = env.reset()
    obs = obs_obj.model_dump()

    step_num = 0
    rewards: List[float] = []
    done = False
    last_error = None

    print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

    while not done:
        prompt = build_prompt(obs)
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=600,
                temperature=0.1,
            )
            raw = resp.choices[0].message.content or ""
            raw = raw.strip().strip("```json").strip("```").strip()
            action_dict = json.loads(raw)
            action = Action(**action_dict)
            last_error = None
        except Exception as e:
            last_error = str(e)[:100]
            cid = obs["challenge"]["id"]
            action = Action(
                challenge_id=cid,
                fixed_sql=obs["challenge"]["broken_sql"],
                explanation="parse error fallback",
                detected_issues=[],
            )

        obs_obj, reward, done, info = env.step(action)
        obs = obs_obj.model_dump()
        step_num += 1
        rewards.append(reward)

        action_str = f"fix(id={action.challenge_id},issues={len(action.detected_issues)})"
        print(
            f"[STEP] step={step_num} action={action_str} "
            f"reward={reward:.2f} done={str(done).lower()} "
            f"error={last_error if last_error else 'null'}",
            flush=True,
        )

    score = env.episode_score()
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(score >= 0.5).lower()} steps={step_num} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )
    env.close()
    return {"task": task_name, "score": score, "steps": step_num}


def main():
    print(f"# SQL Debugger & Optimizer — Baseline Inference", flush=True)
    print(f"# Model: {MODEL_NAME}  API: {API_BASE_URL}\n", flush=True)
    results = []
    for task in TASKS:
        result = run_task(task)
        results.append(result)
        print(f"# Task '{task}' → score: {result['score']:.4f}\n", flush=True)

    avg = sum(r["score"] for r in results) / len(results)
    print("# === FINAL SUMMARY ===", flush=True)
    for r in results:
        print(f"#   {r['task']:8s}: {r['score']:.4f}", flush=True)
    print(f"#   AVERAGE : {avg:.4f}", flush=True)


if __name__ == "__main__":
    main()