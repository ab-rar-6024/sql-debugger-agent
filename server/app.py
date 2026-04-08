"""
SQL Debugger & Optimizer — FastAPI Server for HF Spaces
"""
from __future__ import annotations
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from sql_debugger_env import Action, SQLDebuggerEnv

app = FastAPI(
    title="SQL Debugger & Optimizer — OpenEnv",
    description="Real-world SQL debugging environment for RL agent evaluation.",
    version="1.0.0",
)

_sessions: Dict[str, SQLDebuggerEnv] = {}


class ResetRequest(BaseModel):
    task: str = "easy"
    session_id: Optional[str] = None


class StepRequest(BaseModel):
    session_id: str
    action: Dict[str, Any]


# ✅ HEALTH CHECK
@app.get("/health")
def health():
    return {"status": "ok"}


# ✅ RESET
@app.post("/reset")
def reset(req: Optional[ResetRequest] = Body(default=None)):
    task = req.task if req else "easy"
    session_id = req.session_id if req else str(uuid.uuid4())

    env = SQLDebuggerEnv(task=task)
    _sessions[session_id] = env
    obs = env.reset()

    return {
        "session_id": session_id,
        "observation": obs.model_dump()
    }


# ✅ STEP
@app.post("/step")
def step(req: StepRequest):
    env = _sessions.get(req.session_id)
    if not env:
        raise HTTPException(status_code=404, detail="Session not found.")

    action = Action(**req.action)
    obs, reward, done, info = env.step(action)

    return {
        "observation": obs.model_dump(),
        "reward": reward,
        "done": done,
        "info": info
    }


# ✅ ROOT UI
@app.get("/", response_class=HTMLResponse)
def ui():
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>SQL Debugger & Optimizer</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg:       #080c14;
    --surface:  #0d1525;
    --card:     #111b2e;
    --border:   #1e2f4a;
    --accent:   #00d4ff;
    --accent2:  #7c3aed;
    --green:    #22d3a0;
    --yellow:   #fbbf24;
    --red:      #f87171;
    --text:     #e2eaf8;
    --muted:    #5a7092;
    --glow:     0 0 24px rgba(0,212,255,.25);
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  html,body{height:100%;background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;}

  /* ── Background grid ── */
  body::before{
    content:'';position:fixed;inset:0;z-index:0;
    background-image:
      linear-gradient(rgba(0,212,255,.04) 1px,transparent 1px),
      linear-gradient(90deg,rgba(0,212,255,.04) 1px,transparent 1px);
    background-size:40px 40px;
    pointer-events:none;
  }

  .wrapper{position:relative;z-index:1;max-width:1200px;margin:0 auto;padding:32px 24px 60px;}

  /* ── Header ── */
  header{display:flex;align-items:center;gap:16px;margin-bottom:36px;}
  .logo-box{
    width:52px;height:52px;border-radius:14px;
    background:linear-gradient(135deg,var(--accent2),var(--accent));
    display:flex;align-items:center;justify-content:center;font-size:22px;
    box-shadow:var(--glow);
  }
  header h1{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;letter-spacing:-.5px;}
  header h1 span{color:var(--accent);}
  .badge{
    margin-left:auto;padding:5px 14px;border-radius:20px;font-size:11px;font-weight:700;
    background:rgba(0,212,255,.1);border:1px solid rgba(0,212,255,.3);color:var(--accent);
    letter-spacing:1.5px;text-transform:uppercase;
  }

  /* ── Difficulty row ── */
  .diff-row{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
  .diff-btn{
    flex:1;min-width:120px;padding:13px 0;border-radius:12px;border:1.5px solid var(--border);
    background:var(--card);cursor:pointer;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;
    color:var(--muted);letter-spacing:.8px;transition:all .2s;position:relative;overflow:hidden;
  }
  .diff-btn::after{
    content:'';position:absolute;inset:0;opacity:0;
    background:linear-gradient(135deg,rgba(0,212,255,.12),rgba(124,58,237,.12));
    transition:opacity .2s;
  }
  .diff-btn:hover::after,.diff-btn.active::after{opacity:1;}
  .diff-btn:hover,.diff-btn.active{border-color:var(--accent);color:var(--text);transform:translateY(-2px);box-shadow:var(--glow);}
  .diff-btn.active{color:var(--accent);}
  .diff-btn .pill{
    display:inline-block;margin-left:8px;padding:2px 8px;border-radius:8px;font-size:10px;
    vertical-align:middle;
  }
  .pill-easy{background:rgba(34,211,160,.15);color:var(--green);}
  .pill-medium{background:rgba(251,191,36,.15);color:var(--yellow);}
  .pill-hard{background:rgba(248,113,113,.15);color:var(--red);}
  .pill-custom{background:rgba(124,58,237,.2);color:#a78bfa;}

  /* ── Main grid ── */
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;}
  @media(max-width:768px){.grid{grid-template-columns:1fr;}}

  /* ── Card ── */
  .card{
    background:var(--card);border:1.5px solid var(--border);border-radius:16px;
    padding:20px;
  }
  .card-title{
    font-family:'Syne',sans-serif;font-size:11px;font-weight:800;letter-spacing:2px;
    text-transform:uppercase;color:var(--muted);margin-bottom:14px;display:flex;align-items:center;gap:8px;
  }
  .card-title .dot{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 8px var(--accent);}

  /* ── Textarea / pre ── */
  textarea{
    width:100%;height:150px;background:#060d1a;border:1.5px solid var(--border);
    border-radius:10px;color:var(--text);font-family:'JetBrains Mono',monospace;
    font-size:13px;padding:14px;resize:vertical;outline:none;transition:border-color .2s;
    line-height:1.6;
  }
  textarea:focus{border-color:var(--accent);}
  pre{
    background:#060d1a;border:1.5px solid var(--border);border-radius:10px;
    padding:14px;min-height:80px;font-size:13px;line-height:1.6;white-space:pre-wrap;
    word-break:break-all;color:var(--green);overflow:auto;
  }

  /* ── Custom SQL ── */
  .custom-area{display:none;margin-bottom:20px;}
  .custom-area.show{display:block;}
  .custom-area textarea{height:80px;}
  .custom-label{font-size:11px;color:var(--muted);margin-bottom:6px;letter-spacing:1px;}

  /* ── Run button ── */
  .run-row{display:flex;gap:12px;margin-bottom:20px;align-items:center;}
  .run-btn{
    flex:1;padding:14px;border-radius:12px;border:none;cursor:pointer;
    background:linear-gradient(135deg,var(--accent2),var(--accent));
    font-family:'Syne',sans-serif;font-size:14px;font-weight:800;color:#fff;
    letter-spacing:.5px;transition:all .2s;box-shadow:0 4px 24px rgba(0,212,255,.2);
  }
  .run-btn:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,212,255,.35);}
  .run-btn:active{transform:translateY(0);}

  /* ── Score strip ── */
  .score-strip{
    display:flex;gap:14px;margin-bottom:20px;flex-wrap:wrap;
  }
  .score-card{
    flex:1;min-width:110px;background:var(--card);border:1.5px solid var(--border);
    border-radius:14px;padding:16px 14px;text-align:center;transition:all .3s;
  }
  .score-card.lit{border-color:var(--accent);box-shadow:var(--glow);}
  .score-card .sc-val{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:var(--accent);}
  .score-card .sc-lbl{font-size:10px;color:var(--muted);margin-top:4px;letter-spacing:1.5px;text-transform:uppercase;}

  /* ── Progress bar ── */
  .prog-wrap{background:var(--surface);border-radius:99px;height:10px;overflow:hidden;margin-top:8px;}
  .prog-bar{
    height:100%;border-radius:99px;width:0%;
    background:linear-gradient(90deg,var(--accent2),var(--accent));
    transition:width .8s cubic-bezier(.4,0,.2,1);
    box-shadow:0 0 12px var(--accent);
  }

  /* ── Status badge ── */
  .status-pill{
    display:inline-flex;align-items:center;gap:6px;padding:6px 14px;
    border-radius:20px;font-size:12px;font-weight:700;letter-spacing:.5px;
    margin-bottom:8px;
  }
  .status-pill.win{background:rgba(34,211,160,.15);border:1px solid var(--green);color:var(--green);}
  .status-pill.lose{background:rgba(248,113,113,.12);border:1px solid var(--red);color:var(--red);}
  .status-pill.neutral{background:rgba(91,112,146,.12);border:1px solid var(--muted);color:var(--muted);}

  /* ── Chart ── */
  .chart-wrap{position:relative;height:220px;}

  /* ── Issues list ── */
  .issues{list-style:none;}
  .issues li{
    padding:8px 12px;border-radius:8px;margin-bottom:6px;font-size:12px;
    background:rgba(248,113,113,.08);border-left:3px solid var(--red);color:#fca5a5;
  }

  /* ── Log ── */
  .log-wrap{
    background:#060d1a;border:1.5px solid var(--border);border-radius:12px;
    max-height:180px;overflow-y:auto;padding:12px;
  }
  .log-line{font-size:11px;line-height:1.8;color:var(--muted);}
  .log-line span{color:var(--accent);}
  .log-line.ok span{color:var(--green);}
  .log-line.err span{color:var(--red);}

  /* ── Explanation ── */
  .explain-input{
    width:100%;padding:10px 14px;border-radius:10px;border:1.5px solid var(--border);
    background:#060d1a;color:var(--text);font-family:'JetBrains Mono',monospace;font-size:12px;
    outline:none;transition:border-color .2s;
  }
  .explain-input:focus{border-color:var(--accent);}

  /* ── Hackathon meter ── */
  .hack-bar{
    background:var(--card);border:1.5px solid var(--border);border-radius:16px;
    padding:20px;margin-bottom:20px;
  }
  .hack-bar .hb-title{font-family:'Syne',sans-serif;font-size:12px;font-weight:800;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:12px;}
  .hack-bar .hb-row{display:flex;justify-content:space-between;margin-bottom:8px;font-size:12px;}
  .hack-bar .hb-val{color:var(--accent);font-weight:700;}
  .hack-meter{position:relative;height:22px;background:var(--surface);border-radius:99px;overflow:hidden;}
  .hack-fill{
    height:100%;border-radius:99px;width:0%;
    background:linear-gradient(90deg,#f43f5e,#fbbf24,#22d3a0,#00d4ff);
    transition:width 1s cubic-bezier(.4,0,.2,1);
    box-shadow:0 0 16px rgba(0,212,255,.4);
  }
  .hack-labels{display:flex;justify-content:space-between;margin-top:6px;font-size:10px;color:var(--muted);}

  /* ── Animations ── */
  @keyframes fadeUp{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}
  .card,.score-card,.hack-bar{animation:fadeUp .4s ease both;}

  /* ── Spinner ── */
  @keyframes spin{to{transform:rotate(360deg);}}
  .spinner{width:18px;height:18px;border:2px solid rgba(255,255,255,.2);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite;display:none;}
  .loading .spinner{display:block;}
  .loading .btn-label{display:none;}
</style>
</head>
<body>
<div class="wrapper">

  <!-- Header -->
  <header>
    <div class="logo-box">⚡</div>
    <div>
      <h1>SQL <span>Debugger</span> & Optimizer</h1>
      <div style="font-size:11px;color:var(--muted);margin-top:2px;">RL Environment · OpenEnv Protocol</div>
    </div>
    <div class="badge">v1.0.0</div>
  </header>

  <!-- Difficulty Buttons -->
  <div class="diff-row">
    <button class="diff-btn active" data-task="easy" onclick="selectTask('easy',this)">
      🟢 EASY <span class="pill pill-easy">+100</span>
    </button>
    <button class="diff-btn" data-task="medium" onclick="selectTask('medium',this)">
      🟡 MEDIUM <span class="pill pill-medium">+200</span>
    </button>
    <button class="diff-btn" data-task="hard" onclick="selectTask('hard',this)">
      🔴 HARD <span class="pill pill-hard">+400</span>
    </button>
    <button class="diff-btn" data-task="custom" onclick="selectTask('custom',this)">
      🟣 CUSTOM <span class="pill pill-custom">+∞</span>
    </button>
  </div>

  <!-- Custom SQL entry -->
  <div class="custom-area" id="customArea">
    <div class="custom-label">PASTE YOUR BROKEN SQL BELOW</div>
    <textarea id="customSql" placeholder="-- Paste broken SQL here for custom challenge..."></textarea>
  </div>

  <!-- Explanation -->
  <div style="margin-bottom:16px;">
    <div class="custom-label" style="margin-bottom:6px;">FIX EXPLANATION (boosts score)</div>
    <input class="explain-input" id="explanation" placeholder="e.g. Fixed typo in FROM clause, added missing JOIN condition..."/>
  </div>

  <!-- Run -->
  <div class="run-row">
    <button class="run-btn" id="runBtn" onclick="runFix()">
      <div class="spinner" id="spinner"></div>
      <span class="btn-label">⚡ RUN FIX &amp; SCORE</span>
    </button>
  </div>

  <!-- Hackathon Meter -->
  <div class="hack-bar">
    <div class="hb-title">🏆 Hackathon Score Meter</div>
    <div class="hb-row">
      <span>Cumulative Score</span><span class="hb-val" id="hackScore">0</span>
    </div>
    <div class="hack-meter"><div class="hack-fill" id="hackFill"></div></div>
    <div class="hack-labels">
      <span>0</span><span>Participant</span><span>Good</span><span>Finalist</span><span>🥇 Winner</span>
    </div>
  </div>

  <!-- Score Strip -->
  <div class="score-strip">
    <div class="score-card" id="scReward">
      <div class="sc-val" id="valReward">—</div>
      <div class="sc-lbl">Last Reward</div>
    </div>
    <div class="score-card" id="scTotal">
      <div class="sc-val" id="valTotal">0</div>
      <div class="sc-lbl">Total Score</div>
    </div>
    <div class="score-card" id="scRuns">
      <div class="sc-val" id="valRuns">0</div>
      <div class="sc-lbl">Runs</div>
    </div>
    <div class="score-card" id="scBest">
      <div class="sc-val" id="valBest">—</div>
      <div class="sc-lbl">Best Reward</div>
    </div>
    <div class="score-card" id="scAcc">
      <div class="sc-val" id="valAcc">0%</div>
      <div class="sc-lbl">Win Rate</div>
    </div>
  </div>

  <!-- Main Grid -->
  <div class="grid">
    <!-- Left: SQL panels -->
    <div>
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title"><span class="dot"></span>BROKEN SQL (from challenge)</div>
        <textarea id="sql" placeholder="Click a difficulty button above to load a challenge..."></textarea>
      </div>
      <div class="card">
        <div class="card-title"><span class="dot" style="background:var(--green);box-shadow:0 0 8px var(--green);"></span>FIXED SQL OUTPUT</div>
        <div id="statusPill"></div>
        <pre id="out">-- Fixed SQL will appear here after running ⚡</pre>
        <div style="margin-top:12px;">
          <div class="custom-label" style="margin-bottom:4px;">SCORE PROGRESS</div>
          <div class="prog-wrap"><div class="prog-bar" id="progBar"></div></div>
        </div>
      </div>
    </div>

    <!-- Right: Charts & logs -->
    <div>
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title"><span class="dot" style="background:var(--accent2);box-shadow:0 0 8px var(--accent2);"></span>REWARD HISTORY</div>
        <div class="chart-wrap"><canvas id="rewardChart"></canvas></div>
      </div>
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title"><span class="dot" style="background:var(--yellow);box-shadow:0 0 8px var(--yellow);"></span>DIFFICULTY BREAKDOWN</div>
        <div class="chart-wrap"><canvas id="diffChart"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title"><span class="dot"></span>SESSION LOG</div>
        <div class="log-wrap" id="log">
          <div class="log-line">Waiting for first run…</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Issues -->
  <div class="card">
    <div class="card-title"><span class="dot" style="background:var(--red);box-shadow:0 0 8px var(--red);"></span>DETECTED ISSUES</div>
    <ul class="issues" id="issueList">
      <li>No issues detected yet — run a fix to analyse SQL.</li>
    </ul>
  </div>

</div>

<script>
/* ─── State ─── */
let sid = null, challenge = null;
let currentTask = 'easy';
let totalScore = 0, runs = 0, wins = 0, bestReward = null;
const rewardHistory = [];
const diffScores = { easy:0, medium:0, hard:0, custom:0 };

const THRESHOLDS = { easy:0.6, medium:0.6, hard:0.6, custom:0.5 };

/* ─── Charts ─── */
const chartDefaults = {
  color: '#e2eaf8',
  plugins:{ legend:{ labels:{ color:'#5a7092', font:{ family:'JetBrains Mono', size:10 } } } },
  scales:{
    x:{ ticks:{ color:'#5a7092', font:{ family:'JetBrains Mono', size:10 } }, grid:{ color:'rgba(30,47,74,.6)' } },
    y:{ ticks:{ color:'#5a7092', font:{ family:'JetBrains Mono', size:10 } }, grid:{ color:'rgba(30,47,74,.6)' } }
  }
};

const rewardCtx = document.getElementById('rewardChart').getContext('2d');
const rewardChart = new Chart(rewardCtx, {
  type: 'line',
  data:{
    labels:[],
    datasets:[{
      label:'Reward',
      data:[],
      borderColor:'#00d4ff',
      backgroundColor:'rgba(0,212,255,.08)',
      borderWidth:2,
      pointBackgroundColor:'#00d4ff',
      pointRadius:4,
      tension:.4,
      fill:true
    }]
  },
  options:{ ...chartDefaults, animation:{ duration:600 }, plugins:{ legend:{ display:false } } }
});

const diffCtx = document.getElementById('diffChart').getContext('2d');
const diffChart = new Chart(diffCtx, {
  type:'bar',
  data:{
    labels:['Easy','Medium','Hard','Custom'],
    datasets:[{
      label:'Score',
      data:[0,0,0,0],
      backgroundColor:['rgba(34,211,160,.7)','rgba(251,191,36,.7)','rgba(248,113,113,.7)','rgba(167,139,250,.7)'],
      borderColor:['#22d3a0','#fbbf24','#f87171','#a78bfa'],
      borderWidth:1.5,
      borderRadius:6
    }]
  },
  options:{ ...chartDefaults, animation:{ duration:600 }, plugins:{ legend:{ display:false } } }
});

/* ─── Select task ─── */
function selectTask(task, btn) {
  currentTask = task;
  document.querySelectorAll('.diff-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');

  const ca = document.getElementById('customArea');
  if(task==='custom') { ca.classList.add('show'); }
  else { ca.classList.remove('show'); }

  if(task !== 'custom') loadChallenge(task);
}

/* ─── Load challenge ─── */
async function loadChallenge(task) {
  try {
    const r = await fetch('/reset',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ task })
    });
    const d = await r.json();
    sid = d.session_id;
    challenge = d.observation.challenge;
    document.getElementById('sql').value = challenge.broken_sql || '-- No SQL provided';
    addLog('ok', `Challenge loaded · task=${task} · id=${challenge.id}`);
  } catch(e) {
    addLog('err', `Failed to load challenge: ${e.message}`);
  }
}

/* ─── Run Fix ─── */
async function runFix() {
  const btn = document.getElementById('runBtn');
  btn.classList.add('loading');

  try {
    let brokenSql = document.getElementById('sql').value.trim();
    let customSql = document.getElementById('customSql').value.trim();
    const explanation = document.getElementById('explanation').value.trim() || 'auto fix';

    // For custom, auto-load a session first
    if(currentTask === 'custom') {
      if(!customSql) { addLog('err','Paste your broken SQL in the custom box.'); btn.classList.remove('loading'); return; }
      // Load a session for custom (use easy as base env)
      const rr = await fetch('/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:'easy'})});
      const rd = await rr.json();
      sid = rd.session_id;
      challenge = rd.observation.challenge;
      brokenSql = customSql;
      challenge.broken_sql = customSql;
    }

    if(!sid || !challenge) { addLog('err','Click a difficulty button first.'); btn.classList.remove('loading'); return; }

    /* ── Smart fixer ── */
    const fixed = smartFix(brokenSql);
    const issues = detectIssues(brokenSql);

    const resp = await fetch('/step',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        session_id: sid,
        action:{
          challenge_id: challenge.id,
          fixed_sql: fixed,
          explanation: explanation,
          detected_issues: issues
        }
      })
    });
    const data = await resp.json();
    const reward = data.reward ?? 0;

    /* ── Update UI ── */
    updateScores(reward, issues, fixed, data);

    /* ── Reload next challenge ── */
    if(currentTask !== 'custom') loadChallenge(currentTask);

  } catch(e) {
    addLog('err', `Error: ${e.message}`);
  } finally {
    btn.classList.remove('loading');
  }
}

/* ─── Smart SQL fixer (high-reward logic) ─── */
function smartFix(sql) {
  let s = sql;

  // Keyword typos
  const fixes = [
    [/\bSELCT\b/gi,'SELECT'],[/\bSELECT\b/gi,'SELECT'],
    [/\bFORM\b/g,'FROM'],[/\bFROM\b/gi,'FROM'],
    [/\bWHER\b/g,'WHERE'],[/\bWHERE\b/gi,'WHERE'],
    [/\bORDER\s+BU\b/gi,'ORDER BY'],[/\bGROUP\s+BU\b/gi,'GROUP BY'],
    [/\bHAVNG\b/gi,'HAVING'],[/\bHAVING\b/gi,'HAVING'],
    [/\bINNER\s+JION\b/gi,'INNER JOIN'],[/\bLEFT\s+JION\b/gi,'LEFT JOIN'],
    [/\bJOIN\s+ON\b/gi,'JOIN'],[/\bINSERT\s+IN\b/g,'INSERT INTO'],
    [/\bDELETE\s+FORM\b/gi,'DELETE FROM'],
    [/\bUPDATE\b/gi,'UPDATE'],[/\bSET\b/gi,'SET'],
    [/\bDISTINT\b/gi,'DISTINCT'],[/\bCOUNT\s*\(\s*\)/gi,'COUNT(*)'],
    [/\bNULL\b/gi,'NULL'],[/\bIS\s+NOT\s+NUL\b/gi,'IS NOT NULL'],
    [/\bIS\s+NUL\b/gi,'IS NULL'],
    [/\bLIMT\b/gi,'LIMIT'],[/\bOFFST\b/gi,'OFFSET'],
    [/\bUNION\s+AL\b/gi,'UNION ALL'],
    [/\bCREATE\s+TABL\b/gi,'CREATE TABLE'],
    [/\bALTER\s+TABL\b/gi,'ALTER TABLE'],
    [/\bDROP\s+TABL\b/gi,'DROP TABLE'],
    [/\bVARCAHR\b/gi,'VARCHAR'],[/\bINTEGR\b/gi,'INTEGER'],
    [/==\s*/g,'= '],[/\bAND\s+AND\b/gi,'AND'],
    [/\bOR\s+OR\b/gi,'OR'],[/\bNOT\s+NOT\b/gi,'NOT'],
    [/\bTRUNCATE\b/gi,'TRUNCATE'],[/\bTRANSACTION\b/gi,'TRANSACTION'],
  ];

  fixes.forEach(([pat,rep])=>{ s = s.replace(pat,rep); });

  // Unclosed quotes fix
  const sq = (s.match(/'/g)||[]).length;
  if(sq%2!==0) s += "'";

  // Unclosed parens fix
  const op=(s.match(/\(/g)||[]).length, cl=(s.match(/\)/g)||[]).length;
  if(op>cl) s += ')'.repeat(op-cl);
  if(cl>op) s = '('.repeat(cl-op) + s;

  // Missing semicolon
  if(!/;\s*$/.test(s.trim())) s = s.trim() + ';';

  // Normalise whitespace
  s = s.replace(/\s{2,}/g,' ').trim();

  return s;
}

/* ─── Detect issues ─── */
function detectIssues(sql) {
  const issues = [];
  if(/\bSELCT\b/i.test(sql)) issues.push('typo:SELCT→SELECT');
  if(/\bFORM\b/g.test(sql)) issues.push('typo:FORM→FROM');
  if(/\bWHER\b/g.test(sql)) issues.push('typo:WHER→WHERE');
  if(/==/.test(sql)) issues.push('operator:==→=');
  if((/\(/g.exec(sql)||[]).length !== (/\)/g.exec(sql)||[]).length) issues.push('syntax:unbalanced_parentheses');
  if((/'/g.exec(sql)||[]).length%2!==0) issues.push('syntax:unclosed_string_literal');
  if(!/;\s*$/.test(sql.trim())) issues.push('syntax:missing_semicolon');
  if(/\bLEFT\s+JION\b/i.test(sql)||/\bINNER\s+JION\b/i.test(sql)) issues.push('typo:JION→JOIN');
  if(/\bHAVNG\b/i.test(sql)) issues.push('typo:HAVNG→HAVING');
  if(/\bINTEGR\b/i.test(sql)) issues.push('typo:INTEGR→INTEGER');
  if(!issues.length) issues.push('no_issues_detected');
  return issues;
}

/* ─── Update all UI ─── */
function updateScores(reward, issues, fixed, data) {
  runs++;
  totalScore += reward;
  const isWin = reward >= (THRESHOLDS[currentTask] || 0.6);
  if(isWin) wins++;
  if(bestReward===null || reward > bestReward) bestReward = reward;

  diffScores[currentTask] += reward;

  /* Score cards */
  document.getElementById('valReward').textContent = reward.toFixed ? reward.toFixed(3) : reward;
  document.getElementById('valTotal').textContent = totalScore.toFixed(2);
  document.getElementById('valRuns').textContent = runs;
  document.getElementById('valBest').textContent = bestReward.toFixed ? bestReward.toFixed(3) : bestReward;
  document.getElementById('valAcc').textContent = Math.round((wins/runs)*100)+'%';

  document.getElementById('scReward').classList.add('lit');
  setTimeout(()=>document.getElementById('scReward').classList.remove('lit'),1200);

  /* Progress bar */
  const pct = Math.min(100, (reward/(THRESHOLDS[currentTask]||1))*100);
  document.getElementById('progBar').style.width = pct+'%';

  /* Hackathon meter */
  const hackPct = Math.min(100, (totalScore / (runs * 1)) * 100);
  document.getElementById('hackFill').style.width = hackPct+'%';
  document.getElementById('hackScore').textContent = totalScore.toFixed(2);

  /* Status pill */
  const pill = document.getElementById('statusPill');
  if(isWin){
    pill.innerHTML = '<div class="status-pill win">✅ WINNING SCORE ACHIEVED</div>';
  } else {
    pill.innerHTML = '<div class="status-pill lose">⚠ BELOW THRESHOLD — TRY AGAIN</div>';
  }

  /* Output */
  document.getElementById('out').textContent = fixed;

  /* Reward chart */
  rewardHistory.push(reward);
  rewardChart.data.labels.push(`Run ${runs}`);
  rewardChart.data.datasets[0].data.push(reward);
  if(rewardHistory.length > 20) {
    rewardChart.data.labels.shift();
    rewardChart.data.datasets[0].data.shift();
  }
  rewardChart.update();

  /* Diff chart */
  diffChart.data.datasets[0].data = [
    diffScores.easy, diffScores.medium, diffScores.hard, diffScores.custom
  ];
  diffChart.update();

  /* Issues list */
  const ul = document.getElementById('issueList');
  ul.innerHTML = issues.map(i=>`<li>${i.replace(/:/g,' → ')}</li>`).join('');

  /* Log */
  addLog(isWin?'ok':'err',
    `run=${runs} task=${currentTask} reward=${typeof reward==='number'?reward.toFixed(3):reward} done=${data.done||false}`);
}

/* ─── Log helper ─── */
function addLog(type, msg) {
  const box = document.getElementById('log');
  const ts = new Date().toLocaleTimeString();
  const div = document.createElement('div');
  div.className = `log-line ${type}`;
  div.innerHTML = `<span>[${ts}]</span> ${msg}`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  // Clear placeholder
  const first = box.querySelector('.log-line:not(.ok):not(.err)');
  if(first && box.children.length > 1) first.remove();
}

/* ─── Initial load ─── */
loadChallenge('easy');
</script>
</body>
</html>"""


def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=int(os.getenv("PORT", 7860)))


if __name__ == "__main__":
    main()