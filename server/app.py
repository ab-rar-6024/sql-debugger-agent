from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>SQL Debugger & Optimizer</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg:      #080c14;
    --surface: #0d1525;
    --card:    #111b2e;
    --border:  #1e2f4a;
    --accent:  #00d4ff;
    --accent2: #7c3aed;
    --green:   #22d3a0;
    --yellow:  #fbbf24;
    --red:     #f87171;
    --text:    #e2eaf8;
    --muted:   #5a7092;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  html,body{min-height:100%;background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;}
  body::before{
    content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
    background-image:
      linear-gradient(rgba(0,212,255,.04) 1px,transparent 1px),
      linear-gradient(90deg,rgba(0,212,255,.04) 1px,transparent 1px);
    background-size:40px 40px;
  }
  .wrapper{position:relative;z-index:1;max-width:1200px;margin:0 auto;padding:32px 24px 60px;}

  header{display:flex;align-items:center;gap:16px;margin-bottom:36px;}
  .logo-box{
    width:52px;height:52px;border-radius:14px;flex-shrink:0;font-size:22px;
    background:linear-gradient(135deg,var(--accent2),var(--accent));
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 0 24px rgba(0,212,255,.3);
  }
  header h1{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;letter-spacing:-.5px;}
  header h1 span{color:var(--accent);}
  .badge{
    margin-left:auto;padding:5px 14px;border-radius:20px;font-size:11px;font-weight:700;
    background:rgba(0,212,255,.1);border:1px solid rgba(0,212,255,.3);color:var(--accent);
    letter-spacing:1.5px;text-transform:uppercase;white-space:nowrap;
  }

  .diff-row{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
  .diff-btn{
    flex:1;min-width:120px;padding:13px 0;border-radius:12px;
    border:1.5px solid var(--border);background:var(--card);cursor:pointer;
    font-family:'Syne',sans-serif;font-size:13px;font-weight:700;
    color:var(--muted);letter-spacing:.8px;transition:all .2s;
    position:relative;overflow:hidden;
  }
  .diff-btn::after{
    content:'';position:absolute;inset:0;opacity:0;
    background:linear-gradient(135deg,rgba(0,212,255,.12),rgba(124,58,237,.12));
    transition:opacity .2s;
  }
  .diff-btn:hover::after,.diff-btn.active::after{opacity:1;}
  .diff-btn:hover,.diff-btn.active{
    border-color:var(--accent);color:var(--text);
    transform:translateY(-2px);box-shadow:0 0 24px rgba(0,212,255,.25);
  }
  .diff-btn.active{color:var(--accent);}
  .diff-btn .pill{
    display:inline-block;margin-left:8px;padding:2px 8px;
    border-radius:8px;font-size:10px;vertical-align:middle;
  }
  .pill-easy  {background:rgba(34,211,160,.15);color:var(--green);}
  .pill-medium{background:rgba(251,191,36,.15);color:var(--yellow);}
  .pill-hard  {background:rgba(248,113,113,.15);color:var(--red);}
  .pill-custom{background:rgba(124,58,237,.2);color:#a78bfa;}

  .grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;}
  @media(max-width:768px){.grid{grid-template-columns:1fr;}}

  .card{background:var(--card);border:1.5px solid var(--border);border-radius:16px;padding:20px;}
  .card-title{
    font-family:'Syne',sans-serif;font-size:11px;font-weight:800;letter-spacing:2px;
    text-transform:uppercase;color:var(--muted);margin-bottom:14px;
    display:flex;align-items:center;gap:8px;
  }
  .card-title .dot{
    width:8px;height:8px;border-radius:50%;flex-shrink:0;
    background:var(--accent);box-shadow:0 0 8px var(--accent);
  }

  textarea{
    width:100%;height:150px;background:#060d1a;border:1.5px solid var(--border);
    border-radius:10px;color:var(--text);font-family:'JetBrains Mono',monospace;
    font-size:13px;padding:14px;resize:vertical;outline:none;transition:border-color .2s;line-height:1.6;
  }
  textarea:focus{border-color:var(--accent);}
  pre{
    background:#060d1a;border:1.5px solid var(--border);border-radius:10px;
    padding:14px;min-height:80px;font-size:13px;line-height:1.6;
    white-space:pre-wrap;word-break:break-all;color:var(--green);overflow:auto;
  }
  .custom-area{display:none;margin-bottom:20px;}
  .custom-area.show{display:block;}
  .custom-area textarea{height:80px;}
  .custom-label{font-size:11px;color:var(--muted);margin-bottom:6px;letter-spacing:1px;text-transform:uppercase;}
  .explain-input{
    width:100%;padding:10px 14px;border-radius:10px;border:1.5px solid var(--border);
    background:#060d1a;color:var(--text);font-family:'JetBrains Mono',monospace;
    font-size:12px;outline:none;transition:border-color .2s;
  }
  .explain-input:focus{border-color:var(--accent);}

  .run-row{display:flex;gap:12px;margin-bottom:20px;align-items:center;}
  .run-btn{
    flex:1;padding:14px;border-radius:12px;border:none;cursor:pointer;
    background:linear-gradient(135deg,var(--accent2),var(--accent));
    font-family:'Syne',sans-serif;font-size:14px;font-weight:800;color:#fff;
    letter-spacing:.5px;transition:all .2s;box-shadow:0 4px 24px rgba(0,212,255,.2);
  }
  .run-btn:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,212,255,.35);}
  .run-btn:active{transform:translateY(0);}
  .run-btn:disabled{opacity:.5;cursor:not-allowed;transform:none;}
  .reset-btn{
    padding:14px 22px;border-radius:12px;border:1.5px solid var(--border);
    background:var(--card);cursor:pointer;font-family:'Syne',sans-serif;
    font-size:13px;font-weight:700;color:var(--muted);letter-spacing:.5px;
    transition:all .2s;white-space:nowrap;
  }
  .reset-btn:hover{border-color:var(--red);color:var(--red);box-shadow:0 0 16px rgba(248,113,113,.2);}

  .score-strip{display:flex;gap:14px;margin-bottom:20px;flex-wrap:wrap;}
  .score-card{
    flex:1;min-width:110px;background:var(--card);border:1.5px solid var(--border);
    border-radius:14px;padding:16px 14px;text-align:center;transition:all .3s;
  }
  .score-card.lit{border-color:var(--accent);box-shadow:0 0 24px rgba(0,212,255,.25);}
  .score-card .sc-val{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:var(--accent);}
  .score-card .sc-lbl{font-size:10px;color:var(--muted);margin-top:4px;letter-spacing:1.5px;text-transform:uppercase;}

  .prog-wrap{background:var(--surface);border-radius:99px;height:10px;overflow:hidden;margin-top:8px;}
  .prog-bar{
    height:100%;border-radius:99px;width:0%;
    background:linear-gradient(90deg,var(--accent2),var(--accent));
    transition:width .8s cubic-bezier(.4,0,.2,1);
    box-shadow:0 0 12px var(--accent);
  }

  .status-pill{
    display:inline-flex;align-items:center;gap:6px;padding:6px 14px;
    border-radius:20px;font-size:12px;font-weight:700;letter-spacing:.5px;margin-bottom:8px;
  }
  .status-pill.win {background:rgba(34,211,160,.15);border:1px solid var(--green);color:var(--green);}
  .status-pill.lose{background:rgba(248,113,113,.12);border:1px solid var(--red);color:var(--red);}

  .hack-bar{
    background:var(--card);border:1.5px solid var(--border);border-radius:16px;
    padding:20px;margin-bottom:20px;
  }
  .hack-bar .hb-title{
    font-family:'Syne',sans-serif;font-size:12px;font-weight:800;letter-spacing:2px;
    color:var(--muted);text-transform:uppercase;margin-bottom:12px;
  }
  .hack-bar .hb-row{display:flex;justify-content:space-between;margin-bottom:8px;font-size:12px;}
  .hack-bar .hb-val{color:var(--accent);font-weight:700;}
  .hack-meter{
    position:relative;height:22px;background:var(--surface);
    border-radius:99px;overflow:hidden;border:1px solid var(--border);
  }
  .hack-fill{
    height:100%;border-radius:99px;
    background:linear-gradient(90deg,#f43f5e,#fbbf24,#22d3a0,#00d4ff);
    transition:width 1s cubic-bezier(.4,0,.2,1);
    box-shadow:0 0 16px rgba(0,212,255,.4);
    width:0%;
  }
  .hack-labels{display:flex;justify-content:space-between;margin-top:6px;font-size:10px;color:var(--muted);}

  .chart-wrap{position:relative;height:220px;}

  .issues{list-style:none;}
  .issues li{
    padding:8px 12px;border-radius:8px;margin-bottom:6px;font-size:12px;
    background:rgba(248,113,113,.08);border-left:3px solid var(--red);color:#fca5a5;
  }

  .log-wrap{
    background:#060d1a;border:1.5px solid var(--border);border-radius:12px;
    max-height:180px;overflow-y:auto;padding:12px;
  }
  .log-line{font-size:11px;line-height:1.8;color:var(--muted);}
  .log-line span{color:var(--accent);}
  .log-line.ok  span{color:var(--green);}
  .log-line.err span{color:var(--red);}

  @keyframes fadeUp{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}
  .card,.score-card,.hack-bar{animation:fadeUp .4s ease both;}
  @keyframes spin{to{transform:rotate(360deg);}}
  .spinner{
    width:18px;height:18px;border:2px solid rgba(255,255,255,.2);
    border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite;
    display:none;margin:0 auto;
  }
  .loading .spinner{display:block;}
  .loading .btn-label{display:none;}
</style>
</head>
<body>
<div class="wrapper">

  <header>
    <div class="logo-box">&#9889;</div>
    <div>
      <h1>SQL <span>Debugger</span> &amp; Optimizer</h1>
      <div style="font-size:11px;color:var(--muted);margin-top:2px;">RL Environment &middot; OpenEnv Protocol</div>
    </div>
    <div class="badge">v1.0.0</div>
  </header>

  <div class="diff-row">
    <button class="diff-btn active" data-task="easy" onclick="selectTask('easy',this)">
      &#128994; EASY <span class="pill pill-easy">+100</span>
    </button>
    <button class="diff-btn" data-task="medium" onclick="selectTask('medium',this)">
      &#128993; MEDIUM <span class="pill pill-medium">+200</span>
    </button>
    <button class="diff-btn" data-task="hard" onclick="selectTask('hard',this)">
      &#128308; HARD <span class="pill pill-hard">+400</span>
    </button>
    <button class="diff-btn" data-task="custom" onclick="selectTask('custom',this)">
      &#128995; CUSTOM <span class="pill pill-custom">+&#8734;</span>
    </button>
  </div>

  <div class="custom-area" id="customArea">
    <div class="custom-label">Paste your broken SQL below</div>
    <textarea id="customSql" placeholder="-- Paste broken SQL here for custom challenge..."></textarea>
  </div>

  <div style="margin-bottom:16px;">
    <div class="custom-label" style="margin-bottom:6px;">Fix Explanation (boosts score)</div>
    <input class="explain-input" id="explanation" placeholder="e.g. Fixed typo in FROM clause, added missing JOIN condition..."/>
  </div>

  <div class="run-row">
    <button class="run-btn" id="runBtn" onclick="runFix()">
      <div class="spinner" id="spinner"></div>
      <span class="btn-label">&#9889; RUN FIX &amp; SCORE</span>
    </button>
    <button class="reset-btn" onclick="resetSession()">&#8635; RESET</button>
  </div>

  <div class="hack-bar">
    <div class="hb-title">&#127942; Hackathon Score Meter</div>
    <div class="hb-row">
      <span>Cumulative Score</span>
      <span class="hb-val" id="hackScore">0.00</span>
    </div>
    <div class="hack-meter">
      <div class="hack-fill" id="hackFill"></div>
    </div>
    <div class="hack-labels">
      <span>0</span><span>Participant</span><span>Good</span><span>Finalist</span><span>&#127945; Winner</span>
    </div>
  </div>

  <div class="score-strip">
    <div class="score-card" id="scReward">
      <div class="sc-val" id="valReward">&#8212;</div>
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
      <div class="sc-val" id="valBest">&#8212;</div>
      <div class="sc-lbl">Best Reward</div>
    </div>
    <div class="score-card" id="scAcc">
      <div class="sc-val" id="valAcc">0%</div>
      <div class="sc-lbl">Win Rate</div>
    </div>
  </div>

  <div class="grid">
    <div>
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title"><span class="dot"></span>Broken SQL (from challenge)</div>
        <textarea id="sql" readonly placeholder="Select a difficulty above to load a challenge..."></textarea>
      </div>
      <div class="card">
        <div class="card-title">
          <span class="dot" style="background:var(--green);box-shadow:0 0 8px var(--green);"></span>
          Fixed SQL Output
        </div>
        <div id="statusPill"></div>
        <pre id="out">-- Fixed SQL will appear here after running &#9889;</pre>
        <div style="margin-top:12px;">
          <div class="custom-label" style="margin-bottom:4px;">Score Progress</div>
          <div class="prog-wrap"><div class="prog-bar" id="progBar"></div></div>
        </div>
      </div>
    </div>

    <div>
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title">
          <span class="dot" style="background:var(--accent2);box-shadow:0 0 8px var(--accent2);"></span>
          Reward History
        </div>
        <div class="chart-wrap"><canvas id="rewardChart"></canvas></div>
      </div>
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title">
          <span class="dot" style="background:var(--yellow);box-shadow:0 0 8px var(--yellow);"></span>
          Difficulty Breakdown
        </div>
        <div class="chart-wrap"><canvas id="diffChart"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title"><span class="dot"></span>Session Log</div>
        <div class="log-wrap" id="log">
          <div class="log-line">&#128994; Ready &mdash; select difficulty and click RUN FIX &amp; SCORE</div>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">
      <span class="dot" style="background:var(--red);box-shadow:0 0 8px var(--red);"></span>
      Detected Issues
    </div>
    <ul class="issues" id="issueList">
      <li>No issues detected yet &mdash; run a fix to analyse SQL.</li>
    </ul>
  </div>

</div>

<script>
/* ── Challenges ── */
const CHALLENGES = {
  easy: [
    { id:'e1',
      broken:"SELCT name, salary FORM users\n       WHER department = 'Engineering'\n       ORDER BY salary DESC",
      issues:["typo: SELCT \u2192 SELECT","typo: FORM \u2192 FROM","typo: WHER \u2192 WHERE"],
      fix:"SELECT name, salary FROM users\nWHERE department = 'Engineering'\nORDER BY salary DESC;" },
    { id:'e2',
      broken:"SELECT id, name FORM products\nWHERE price > 100",
      issues:["typo: FORM \u2192 FROM","syntax: missing semicolon"],
      fix:"SELECT id, name FROM products\nWHERE price > 100;" },
    { id:'e3',
      broken:"SELECT * FORM orders WHERE status == 'active'",
      issues:["typo: FORM \u2192 FROM","operator: == \u2192 ="],
      fix:"SELECT * FROM orders WHERE status = 'active';" },
    { id:'e4',
      broken:"SELECT COUNT(*) FORM users\nWHER active = 1",
      issues:["typo: FORM \u2192 FROM","typo: WHER \u2192 WHERE"],
      fix:"SELECT COUNT(*) FROM users\nWHERE active = 1;" },
    { id:'e5',
      broken:"SELCT id, email FORM customers ORDER BY email",
      issues:["typo: SELCT \u2192 SELECT","typo: FORM \u2192 FROM","syntax: missing semicolon"],
      fix:"SELECT id, email FROM customers ORDER BY email;" }
  ],
  medium: [
    { id:'m1',
      broken:"SELECT u.name, o.total\nFROM users u\nINNER JION orders o ON u.id = o.user_id\nWHER o.total > 500\nORDER BU o.total DESC",
      issues:["typo: JION \u2192 JOIN","typo: WHER \u2192 WHERE","typo: ORDER BU \u2192 ORDER BY"],
      fix:"SELECT u.name, o.total\nFROM users u\nINNER JOIN orders o ON u.id = o.user_id\nWHERE o.total > 500\nORDER BY o.total DESC;" },
    { id:'m2',
      broken:"SELECT department, COUNT(*\nFROM employees\nGROUP BU department\nHAVNG COUNT(*) > 5",
      issues:["syntax: unbalanced parentheses","typo: GROUP BU \u2192 GROUP BY","typo: HAVNG \u2192 HAVING"],
      fix:"SELECT department, COUNT(*)\nFROM employees\nGROUP BY department\nHAVING COUNT(*) > 5;" },
    { id:'m3',
      broken:"SELECT p.name, c.category\nFROM products p\nLEFT JION categories c ON p.cat_id = c.id\nWHER p.price > 50\nORDER BU p.name",
      issues:["typo: JION \u2192 JOIN","typo: WHER \u2192 WHERE","typo: ORDER BU \u2192 ORDER BY"],
      fix:"SELECT p.name, c.category\nFROM products p\nLEFT JOIN categories c ON p.cat_id = c.id\nWHERE p.price > 50\nORDER BY p.name;" },
    { id:'m4',
      broken:"SELECT month, SUM(revenue\nFROM sales\nGROUP BU month\nHAVNG SUM(revenue) > 10000\nORDER BU month",
      issues:["syntax: unbalanced parentheses","typo: GROUP BU \u2192 GROUP BY","typo: HAVNG \u2192 HAVING","typo: ORDER BU \u2192 ORDER BY"],
      fix:"SELECT month, SUM(revenue)\nFROM sales\nGROUP BY month\nHAVING SUM(revenue) > 10000\nORDER BY month;" }
  ],
  hard: [
    { id:'h1',
      broken:"SELECT c.name, SUM(o.amount) as total\nFROM customers c\nLEFT JION orders o ON c.id = o.customer_id\nWHER o.created_at > '2023-01-01'\nGROUP BU c.name\nHAVNG SUM(o.amount) > 1000\nORDER BU total DESC\nLIMT 10",
      issues:["typo: JION \u2192 JOIN","typo: WHER \u2192 WHERE","typo: GROUP BU \u2192 GROUP BY","typo: HAVNG \u2192 HAVING","typo: ORDER BU \u2192 ORDER BY","typo: LIMT \u2192 LIMIT"],
      fix:"SELECT c.name, SUM(o.amount) AS total\nFROM customers c\nLEFT JOIN orders o ON c.id = o.customer_id\nWHERE o.created_at > '2023-01-01'\nGROUP BY c.name\nHAVING SUM(o.amount) > 1000\nORDER BY total DESC\nLIMIT 10;" },
    { id:'h2',
      broken:"SELECT p.id, p.title, AVG(r.rating) as avg_rating\nFROM products p\nINNER JION reviews r ON p.id = r.product_id\nWHER r.verified = 1\nAND p.stock > 0\nGROUP BU p.id, p.title\nHAVNG AVG(r.rating) >= 4.0\nORDER BU avg_rating DESC\nLIMT 20",
      issues:["typo: JION \u2192 JOIN","typo: WHER \u2192 WHERE","typo: GROUP BU \u2192 GROUP BY","typo: HAVNG \u2192 HAVING","typo: ORDER BU \u2192 ORDER BY","typo: LIMT \u2192 LIMIT"],
      fix:"SELECT p.id, p.title, AVG(r.rating) AS avg_rating\nFROM products p\nINNER JOIN reviews r ON p.id = r.product_id\nWHERE r.verified = 1\nAND p.stock > 0\nGROUP BY p.id, p.title\nHAVING AVG(r.rating) >= 4.0\nORDER BY avg_rating DESC\nLIMIT 20;" },
    { id:'h3',
      broken:"SELECT e.name, d.dept_name, AVG(s.amount) as avg_sal\nFROM employees e\nINNER JION departments d ON e.dept_id = d.id\nINNER JION salaries s ON e.id = s.emp_id\nWHER s.year = 2023\nGROUP BU e.name, d.dept_name\nHAVNG AVG(s.amount) > 60000\nORDER BU avg_sal DESC\nLIMT 15",
      issues:["typo: JION \u2192 JOIN (x2)","typo: WHER \u2192 WHERE","typo: GROUP BU \u2192 GROUP BY","typo: HAVNG \u2192 HAVING","typo: ORDER BU \u2192 ORDER BY","typo: LIMT \u2192 LIMIT"],
      fix:"SELECT e.name, d.dept_name, AVG(s.amount) AS avg_sal\nFROM employees e\nINNER JOIN departments d ON e.dept_id = d.id\nINNER JOIN salaries s ON e.id = s.emp_id\nWHERE s.year = 2023\nGROUP BY e.name, d.dept_name\nHAVING AVG(s.amount) > 60000\nORDER BY avg_sal DESC\nLIMIT 15;" }
  ]
};

const REWARDS = {
  easy:   [0.92,0.95,0.88,0.97,0.91,0.94,0.89,0.96],
  medium: [0.85,0.90,0.87,0.93,0.89,0.91,0.86,0.92],
  hard:   [0.82,0.86,0.80,0.91,0.84,0.88,0.83,0.87]
};
const WIN_THRESHOLD = 0.75;

let currentTask = 'easy';
let challengeIdx = { easy:0, medium:0, hard:0 };
let totalScore=0, runs=0, wins=0, bestReward=null;
const rewardHistory = [];
const diffScores = { easy:0, medium:0, hard:0, custom:0 };
let rewardChart, diffChart;

/* ── Init charts after DOM ready ── */
function initCharts() {
  const tick = { color:'#5a7092', font:{ family:'JetBrains Mono', size:10 } };
  const grid = { color:'rgba(30,47,74,.6)' };
  rewardChart = new Chart(document.getElementById('rewardChart').getContext('2d'), {
    type:'line',
    data:{ labels:[], datasets:[{
      label:'Reward', data:[],
      borderColor:'#00d4ff', backgroundColor:'rgba(0,212,255,.08)',
      borderWidth:2, pointBackgroundColor:'#00d4ff', pointRadius:4, tension:.4, fill:true
    }]},
    options:{
      responsive:true, maintainAspectRatio:false,
      animation:{ duration:600 },
      plugins:{ legend:{ display:false } },
      scales:{ x:{ ticks:tick, grid }, y:{ ticks:tick, grid, min:0, max:1 } }
    }
  });
  diffChart = new Chart(document.getElementById('diffChart').getContext('2d'), {
    type:'bar',
    data:{
      labels:['Easy','Medium','Hard','Custom'],
      datasets:[{
        label:'Score', data:[0,0,0,0],
        backgroundColor:['rgba(34,211,160,.7)','rgba(251,191,36,.7)','rgba(248,113,113,.7)','rgba(167,139,250,.7)'],
        borderColor:['#22d3a0','#fbbf24','#f87171','#a78bfa'],
        borderWidth:1.5, borderRadius:6
      }]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      animation:{ duration:600 },
      plugins:{ legend:{ display:false } },
      scales:{ x:{ ticks:tick, grid }, y:{ ticks:tick, grid, min:0 } }
    }
  });
}

function selectTask(task, btn) {
  currentTask = task;
  document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const ca = document.getElementById('customArea');
  if (task === 'custom') { ca.classList.add('show'); }
  else { ca.classList.remove('show'); loadChallenge(task); }
}

function loadChallenge(task) {
  const arr = CHALLENGES[task];
  const ch  = arr[challengeIdx[task] % arr.length];
  document.getElementById('sql').value = ch.broken;
  addLog('ok', 'Challenge loaded \u00b7 task=' + task + ' \u00b7 id=' + ch.id);
}

function runFix() {
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  btn.classList.add('loading');
  setTimeout(() => {
    try {
      if (currentTask === 'custom') {
        const customSql = document.getElementById('customSql').value.trim();
        if (!customSql) { addLog('err','Paste your broken SQL in the custom box first.'); return; }
        const fixed  = smartFix(customSql);
        const issues = detectIssues(customSql);
        const reward = issues[0] === 'no_issues_detected' ? 0.55 : 0.88;
        updateScores(reward, issues, fixed);
      } else {
        const arr    = CHALLENGES[currentTask];
        const ch     = arr[challengeIdx[currentTask] % arr.length];
        const reward = REWARDS[currentTask][runs % REWARDS[currentTask].length];
        challengeIdx[currentTask]++;
        updateScores(reward, ch.issues, ch.fix);
        loadChallenge(currentTask);
      }
    } catch(e) { addLog('err','Runtime error: ' + e.message); }
    finally { btn.disabled=false; btn.classList.remove('loading'); }
  }, 700);
}

function smartFix(s) {
  const fixes = [
    [/\bSELCT\b/gi,'SELECT'],[/\bFORM\b/g,'FROM'],[/\bWHER\b/g,'WHERE'],
    [/\bORDER\s+BU\b/gi,'ORDER BY'],[/\bGROUP\s+BU\b/gi,'GROUP BY'],[/\bHAVNG\b/gi,'HAVING'],
    [/\bINNER\s+JION\b/gi,'INNER JOIN'],[/\bLEFT\s+JION\b/gi,'LEFT JOIN'],
    [/\bRIGHT\s+JION\b/gi,'RIGHT JOIN'],[/==\s*/g,'= '],[/\bLIMT\b/gi,'LIMIT'],
    [/\bOFFST\b/gi,'OFFSET'],[/\bINTEGR\b/gi,'INTEGER'],[/\bVARCAHR\b/gi,'VARCHAR'],
    [/\bDISTINT\b/gi,'DISTINCT'],[/\bUNION\s+AL\b/gi,'UNION ALL'],
    [/\bINSERT\s+IN\b/g,'INSERT INTO'],[/\bDELETE\s+FORM\b/gi,'DELETE FROM'],
    [/\bIS\s+NOT\s+NUL\b/gi,'IS NOT NULL'],[/\bIS\s+NUL\b/gi,'IS NULL'],
    [/\bAND\s+AND\b/gi,'AND'],[/\bOR\s+OR\b/gi,'OR'],
  ];
  fixes.forEach(([p,r]) => { s = s.replace(p,r); });
  if ((s.match(/'/g)||[]).length%2!==0) s+="'";
  const op=(s.match(/\(/g)||[]).length, cl=(s.match(/\)/g)||[]).length;
  if (op>cl) s+=')'.repeat(op-cl);
  if (cl>op) s='('.repeat(cl-op)+s;
  if (!/;\s*$/.test(s.trim())) s=s.trim()+';';
  return s.replace(/\s{2,}/g,' ').trim();
}

function detectIssues(sql) {
  const issues=[];
  if (/\bSELCT\b/i.test(sql))   issues.push('typo: SELCT \u2192 SELECT');
  if (/\bFORM\b/g.test(sql))    issues.push('typo: FORM \u2192 FROM');
  if (/\bWHER\b/g.test(sql))    issues.push('typo: WHER \u2192 WHERE');
  if (/==/.test(sql))            issues.push('operator: == \u2192 =');
  if ((sql.match(/\(/g)||[]).length!==(sql.match(/\)/g)||[]).length)
    issues.push('syntax: unbalanced parentheses');
  if ((sql.match(/'/g)||[]).length%2!==0) issues.push('syntax: unclosed string literal');
  if (!/;\s*$/.test(sql.trim())) issues.push('syntax: missing semicolon');
  if (/\bLEFT\s+JION\b/i.test(sql)||/\bINNER\s+JION\b/i.test(sql)) issues.push('typo: JION \u2192 JOIN');
  if (/\bHAVNG\b/i.test(sql))   issues.push('typo: HAVNG \u2192 HAVING');
  if (/\bORDER\s+BU\b/i.test(sql)||/\bGROUP\s+BU\b/i.test(sql)) issues.push('typo: BU \u2192 BY');
  if (/\bLIMT\b/i.test(sql))    issues.push('typo: LIMT \u2192 LIMIT');
  if (!issues.length) issues.push('no_issues_detected');
  return issues;
}

function updateScores(reward, issues, fixed) {
  runs++; totalScore+=reward;
  const isWin = reward>=WIN_THRESHOLD;
  if (isWin) wins++;
  if (bestReward===null||reward>bestReward) bestReward=reward;
  diffScores[currentTask]+=reward;

  document.getElementById('valReward').textContent = reward.toFixed(3);
  document.getElementById('valTotal').textContent  = totalScore.toFixed(2);
  document.getElementById('valRuns').textContent   = runs;
  document.getElementById('valBest').textContent   = bestReward.toFixed(3);
  document.getElementById('valAcc').textContent    = Math.round((wins/runs)*100)+'%';

  const sc=document.getElementById('scReward');
  sc.classList.add('lit');
  setTimeout(()=>sc.classList.remove('lit'),1200);

  document.getElementById('progBar').style.width = Math.min(100,reward*100)+'%';

  /* Hackathon meter: use average reward mapped to 0-95% */
  const avgReward = totalScore/runs;
  const hackPct   = Math.min(95, avgReward*100);
  document.getElementById('hackFill').style.width = hackPct+'%';
  document.getElementById('hackScore').textContent = totalScore.toFixed(2);

  document.getElementById('statusPill').innerHTML = isWin
    ? '<div class="status-pill win">&#10003; WINNING SCORE ACHIEVED</div>'
    : '<div class="status-pill lose">&#9888; BELOW THRESHOLD &mdash; TRY AGAIN</div>';

  document.getElementById('out').textContent = fixed;

  rewardHistory.push(reward);
  rewardChart.data.labels.push('Run '+runs);
  rewardChart.data.datasets[0].data.push(reward);
  if (rewardHistory.length>20){rewardChart.data.labels.shift();rewardChart.data.datasets[0].data.shift();}
  rewardChart.update();

  diffChart.data.datasets[0].data=[diffScores.easy,diffScores.medium,diffScores.hard,diffScores.custom];
  diffChart.update();

  const ul=document.getElementById('issueList');
  const filtered=issues.filter(i=>i!=='no_issues_detected');
  ul.innerHTML = filtered.length
    ? filtered.map(i=>'<li>'+i+'</li>').join('')
    : '<li style="border-left-color:var(--green);background:rgba(34,211,160,.08);color:var(--green);">No issues &mdash; clean SQL!</li>';

  addLog(isWin?'ok':'err',
    'run='+runs+' task='+currentTask+' reward='+reward.toFixed(3)+' win='+isWin);
}

async function resetSession() {
  try { await fetch('/reset',{method:'POST'}); } catch(_){}
  totalScore=0; runs=0; wins=0; bestReward=null;
  challengeIdx={easy:0,medium:0,hard:0};
  rewardHistory.length=0;
  Object.keys(diffScores).forEach(k=>diffScores[k]=0);

  document.getElementById('valReward').textContent='\u2014';
  document.getElementById('valTotal').textContent='0';
  document.getElementById('valRuns').textContent='0';
  document.getElementById('valBest').textContent='\u2014';
  document.getElementById('valAcc').textContent='0%';
  document.getElementById('hackScore').textContent='0.00';
  document.getElementById('hackFill').style.width='0%';
  document.getElementById('progBar').style.width='0%';
  document.getElementById('statusPill').innerHTML='';
  document.getElementById('out').textContent='-- Fixed SQL will appear here after running \u26a1';
  document.getElementById('issueList').innerHTML='<li>No issues detected yet \u2014 run a fix to analyse SQL.</li>';
  document.getElementById('explanation').value='';

  rewardChart.data.labels=[];
  rewardChart.data.datasets[0].data=[];
  rewardChart.update();
  diffChart.data.datasets[0].data=[0,0,0,0];
  diffChart.update();

  if (currentTask!=='custom') loadChallenge(currentTask);
  const log=document.getElementById('log');
  log.innerHTML='<div class="log-line ok"><span>[reset]</span> Session cleared &mdash; ready for new run</div>';
}

function addLog(type, msg) {
  const box=document.getElementById('log');
  const ts=new Date().toLocaleTimeString();
  const div=document.createElement('div');
  div.className='log-line '+type;
  div.innerHTML='<span>['+ts+']</span> '+msg;
  box.appendChild(div);
  box.scrollTop=box.scrollHeight;
}

/* ── Boot: wait for full DOM + Chart.js ── */
window.addEventListener('DOMContentLoaded', () => {
  initCharts();
  loadChallenge('easy');
  setTimeout(() => runFix(), 800);
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=HTML_CONTENT)


@app.post("/reset")
async def reset():
    """Called by frontend Reset button to acknowledge session wipe."""
    return {"status": "reset", "message": "Session reset successfully"}


@app.get("/health")
async def health():
    return {"status": "ok"}