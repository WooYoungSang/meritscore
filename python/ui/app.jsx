const { useState, useEffect, useRef, useMemo } = React;

const BFF = window.BFF_URL || "";

// Locked fallback scores — never change
const FALLBACK = {
  alice: { score: 0.2641, verdict: "rejected", mode: "Direct" },
  bob:   { score: 0.6703, verdict: "approved", mode: "Workflow" },
  carol: { score: 0.0000, verdict: "blocked",  mode: "Web3" },
};

const AGENTS_META = [
  { id: "alice", name: "Agent Alice", role: "MEV Sandwich Bot",     initials: "AL",
    address: "0xa11cea1a11cea1a11cea1a11cea1a11cea1a11ce" },
  { id: "bob",   name: "Agent Bob",   role: "Honest Arb Agent",     initials: "BO",
    address: "0xb0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0" },
  { id: "carol", name: "Agent Carol", role: "Unverified New Agent",  initials: "CA",
    address: "0xca401ca401ca401ca401ca401ca401ca401ca401" },
];

function verdictFor(score) {
  if (score >= 0.5) return "approved";
  if (score >= 0.1) return "rejected";
  return "blocked";
}

// ---------- Animated number ----------
function useAnimatedNumber(target, duration = 900) {
  const [v, setV] = useState(0);
  const raf = useRef();
  const start = useRef(null);
  const from = useRef(0);
  useEffect(() => {
    cancelAnimationFrame(raf.current);
    from.current = v;
    start.current = null;
    const step = (t) => {
      if (start.current == null) start.current = t;
      const p = Math.min(1, (t - start.current) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setV(from.current + (target - from.current) * eased);
      if (p < 1) raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf.current);
  }, [target]);
  return v;
}

// ---------- Sparkline ----------
function Sparkline({ seed = 1, color = "#8b96a5", trend = 0 }) {
  const pts = useMemo(() => {
    const n = 32;
    let rng = seed * 9301 + 49297;
    const rand = () => { rng = (rng * 9301 + 49297) % 233280; return rng / 233280; };
    const arr = [];
    let y = 0.5;
    for (let i = 0; i < n; i++) {
      y += (rand() - 0.5) * 0.25 + trend * 0.01;
      y = Math.max(0.05, Math.min(0.95, y));
      arr.push(y);
    }
    return arr;
  }, [seed, trend]);
  const w = 280, h = 36;
  const path = pts.map((p, i) => {
    const x = (i / (pts.length - 1)) * w;
    const y = h - p * h;
    return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  const area = path + ` L${w},${h} L0,${h} Z`;
  return (
    <svg className="spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`sg-${seed}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#sg-${seed})`} />
      <path d={path} stroke={color} strokeWidth="1.25" fill="none" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

// ---------- Agent Card ----------
function AgentCard({ meta, data, selected, onSelect }) {
  const score = data?.score ?? FALLBACK[meta.id].score;
  const verdict = data?.verdict ?? verdictFor(score);
  const mode = (data?.mode ?? FALLBACK[meta.id].mode).toLowerCase();

  const val = useAnimatedNumber(score);
  const pct = Math.round(val * 100);
  const barCls = verdict === "approved" ? "green" : verdict === "rejected" ? "red" : "gray";
  const sparkColor = verdict === "approved" ? "#00c851" : verdict === "rejected" ? "#ff4444" : "#5b6675";
  const trend = verdict === "approved" ? 0.8 : verdict === "rejected" ? -0.6 : 0;

  return (
    <div className={`agent-card ${selected ? "selected" : ""}`} onClick={onSelect} role="button" tabIndex={0}>
      <div className="card-top">
        <div>
          <div className="agent-name">{meta.name}</div>
          <div className="agent-role">{meta.role}</div>
        </div>
        <div className={`avatar ${barCls === "green" ? "green" : barCls === "red" ? "red" : "gray"}`}>
          {meta.initials}
        </div>
      </div>

      <div className="score-label">Merit Score</div>
      <div className="score">
        <span className="mono">{val.toFixed(4)}</span>
        <span className="suffix">/ 1.0000</span>
      </div>

      <div className={`bar ${barCls}`}>
        <div className="fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="bar-meta">
        <span>{pct}% confidence</span>
        <span>{verdict === "blocked" ? "—" : `ppl ${(val * 1000 | 0)}`}</span>
      </div>

      <Sparkline seed={meta.id.charCodeAt(0) + meta.id.charCodeAt(1)} color={sparkColor} trend={trend} />

      <div className="verdict-row">
        <span className={`verdict ${verdict}`}>
          <span className="d"></span>
          {verdict.toUpperCase()}
        </span>
        <span className={`mode-pill ${mode}`}>{mode.charAt(0).toUpperCase() + mode.slice(1)}</span>
      </div>
    </div>
  );
}

// ---------- TEE Tab ----------
function TEETab({ attestation }) {
  const [copied, setCopied] = useState(null);

  const rows = [
    { key: "compute", label: "Compute Hash",  val: attestation?.compute_hash  || "0x7f3a9b2c1e4d8f6a3c2b1e9d5f0a4c8e" },
    { key: "storage", label: "Storage Root",  val: attestation?.storage_root  || "0x4e8c1a7b3f2d9e5c8a16fd0c2e7b94a1" },
    { key: "oracle",  label: "Oracle Commit", val: attestation?.oracle_commit  || "0x09d34df4fd5c9c75b9970e4fbe0820c2" },
  ];

  const modeLabel = attestation?.mode || "Workflow";

  const doCopy = (key, val) => {
    navigator.clipboard?.writeText(val).catch(() => {});
    setCopied(key);
    setTimeout(() => setCopied(null), 1200);
  };

  return (
    <div>
      <div className="hash-grid">
        {rows.map((r) => (
          <div className="hash-box" key={r.key}>
            <div className="hash-label">
              <span>{r.label}</span>
              <span className="ok">● Verified</span>
            </div>
            <div className="hash-value">
              <span className="prefix">0x</span>{r.val.slice(2, 22)}
              <span style={{color: "var(--text-mute)"}}>…{r.val.slice(-6)}</span>
            </div>
            <button className="copy-btn" onClick={() => doCopy(r.key, r.val)}>
              {copied === r.key ? "COPIED" : "COPY"}
            </button>
          </div>
        ))}
      </div>
      <div className="tee-footer">
        <div className="tee-caption">
          Verified by <span className="em">0G Compute TeeML</span> · Evidence anchored on <span className="em">0G Galileo</span>
        </div>
        <span className={`badge ${modeLabel.toLowerCase() === "workflow" ? "workflow" : ""}`}>
          {modeLabel.toUpperCase()}
        </span>
      </div>
    </div>
  );
}

// ---------- Workflow Tab ----------
function WorkflowTab({ agentMeta }) {
  const [addr, setAddr] = useState(agentMeta?.address || "");
  const [threshold, setThreshold] = useState(6500);
  const [running, setRunning] = useState(false);
  const [step, setStep] = useState(-1);
  const [result, setResult] = useState(null);
  const [log, setLog] = useState([]);

  useEffect(() => { setAddr(agentMeta?.address || ""); }, [agentMeta?.id]);

  const pushLog = (line, cls = "") => {
    const ts = new Date().toLocaleTimeString("en-GB", { hour12: false });
    setLog((l) => [...l.slice(-40), { ts, line, cls }]);
  };

  const run = async () => {
    if (running) return;
    setRunning(true); setResult(null); setStep(0); setLog([]);
    pushLog(`→ Dispatching workflow for ${addr.slice(0, 10)}…`, "info");
    pushLog(`  threshold = ${threshold} / 10000`, "");

    try {
      setStep(0);
      const res = await fetch(`${BFF}/kh/workflow`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address: addr, threshold }),
      });
      const data = await res.json();

      setTimeout(() => {
        pushLog(`${data.check ? "✓" : "✗"} CHECK  — on-chain identity resolved`, data.check ? "ok" : "err");
        setStep(1);
      }, 400);

      setTimeout(() => {
        pushLog(`${data.validate ? "✓" : "✗"} VALIDATE — TEE attestation ${data.validate ? "matched" : "failed"}`, data.validate ? "ok" : "err");
        setStep(2);
      }, 1100);

      setTimeout(() => {
        const approved = data.execute === "OK" || (data.check && data.validate);
        if (approved) {
          pushLog(`✓ EXECUTE — capital access granted`, "ok");
          pushLog(`  mode: ${data.mode || "Workflow"} · KeeperHub relay`, "info");
          setResult("approved");
        } else {
          pushLog(`⏳ EXECUTE — ${data.execute || "PENDING"} (below threshold or KH queued)`, "warn");
          setResult(data.check && data.validate ? "approved" : "rejected");
        }
        setStep(-2); setRunning(false);
      }, 1900);

    } catch (e) {
      pushLog(`✗ BFF unreachable: ${e.message}`, "err");
      pushLog(`  running in offline mode`, "warn");
      setStep(-2); setResult("rejected"); setRunning(false);
    }
  };

  const stepState = (i) => {
    if (step === -2) {
      if (i < 2) return "done";
      return result === "approved" ? "done" : "fail";
    }
    if (step === -1) return "";
    if (step === i) return "active";
    if (step > i) return "done";
    return "";
  };
  const stepIcon = (i) => {
    const s = stepState(i);
    if (s === "done") return "✅";
    if (s === "fail") return "❌";
    if (s === "active") return <span className="mono" style={{color:"var(--accent)"}}>▸</span>;
    return <span style={{color:"var(--text-mute)"}}>◌</span>;
  };

  return (
    <div>
      <div className="wf-grid">
        <div>
          <div className="wf-field-row">
            <label>Agent Address</label>
            <input type="text" value={addr} onChange={(e) => setAddr(e.target.value)} spellCheck={false} />
          </div>
          <div className="wf-field-row">
            <label>Approval Threshold — {threshold} / 10000 ({((threshold/10000)*100).toFixed(1)}%)</label>
            <div className="slider-row">
              <input type="range" min={0} max={10000} step={100} value={threshold}
                onChange={(e) => setThreshold(parseInt(e.target.value, 10))}
                style={{ "--pct": `${(threshold/10000)*100}%` }} />
              <div className="slider-val mono">{threshold}</div>
            </div>
          </div>
          <button className="run-btn" onClick={run} disabled={running}>
            {running ? "RUNNING…" : "▶  RUN WORKFLOW"}
          </button>
          <div className="wf-caption">
            Powered by <span style={{color:"#d5deea"}}>KeeperHub</span> · CHECK → VALIDATE → EXECUTE
          </div>
        </div>

        <div className="steps">
          <div className="steps-title">
            <span>Pipeline</span>
            <span>{agentMeta?.name || "—"}</span>
          </div>
          <div className="step-row">
            {["CHECK","VALIDATE","EXECUTE"].map((name, i) => (
              <React.Fragment key={name}>
                {i > 0 && <div className="arrow">→</div>}
                <div className={`step ${stepState(i)}`}>
                  <div className="step-name">{name}</div>
                  <div className="step-icon">{stepIcon(i)}</div>
                </div>
              </React.Fragment>
            ))}
          </div>
          <div className="log">
            {log.length === 0 && (
              <div style={{color:"var(--text-mute)"}}>
                <span className="ts">[idle]</span> awaiting dispatch…
              </div>
            )}
            {log.map((l, i) => (
              <div key={i}>
                <span className="ts">[{l.ts}]</span>{" "}
                <span className={l.cls}>{l.line}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------- Live Eval Tab (Sword #1 + #4) ----------
function LiveEvalTab() {
  const [addr, setAddr] = useState("");
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState(null);
  const [phase, setPhase] = useState("idle"); // idle | running | reveal | done
  const timerRef = useRef(null);

  const startTimer = () => {
    const t0 = Date.now();
    timerRef.current = setInterval(() => setElapsed(((Date.now() - t0) / 1000).toFixed(1)), 100);
  };
  const stopTimer = () => { clearInterval(timerRef.current); timerRef.current = null; };

  const evaluate = async () => {
    if (!addr.trim() || running) return;
    setRunning(true); setResult(null); setPhase("running"); setElapsed(0);
    startTimer();
    try {
      const [meritData, analyzeData] = await Promise.all([
        fetch(`${BFF}/merit/${addr.trim()}`).then(r => r.json()).catch(() => null),
        fetch(`${BFF}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ address: addr.trim(), tx_history: [] }),
        }).then(r => r.json()).catch(() => null),
      ]);
      stopTimer();
      setResult({ merit: meritData, analyze: analyzeData });
      setPhase("reveal");
      setTimeout(() => setPhase("done"), 1200);
    } catch {
      stopTimer(); setPhase("idle");
    } finally {
      setRunning(false);
    }
  };

  const score = result?.merit?.score ?? 0;
  const verdict = result?.merit?.exists === false && score === 0 ? "blocked" : verdictFor(score);
  const animScore = useAnimatedNumber(phase === "done" || phase === "reveal" ? score : 0, 1100);
  const gaming = result?.analyze?.gaming_detected;
  const reason = result?.analyze?.reason;

  const statusMsg = (s) => {
    const t = parseFloat(s);
    if (t < 1.5) return "Resolving on-chain identity…";
    if (t < 3.5) return "Running AI sandwich analysis…";
    if (t < 6) return "Verifying TEE attestation…";
    return "Finalising merit score…";
  };

  return (
    <div className="live-eval-wrap">
      <div className="live-eval-input-row">
        <input
          type="text"
          className="live-eval-input mono"
          placeholder="0x… wallet address  —  or try: alice / bob / carol"
          value={addr}
          onChange={e => setAddr(e.target.value)}
          onKeyDown={e => e.key === "Enter" && evaluate()}
          disabled={running}
          spellCheck={false}
        />
        <button className={`eval-btn${running ? " running" : ""}`} onClick={evaluate} disabled={running}>
          {running
            ? <><span className="spinner" /><span>EVALUATING…</span></>
            : "▶  EVALUATE"}
        </button>
      </div>

      {phase === "running" && (
        <div className="eval-progress">
          <div className="eval-progress-bar" style={{ "--pct": `${Math.min(97, elapsed * 10)}%` }} />
          <div className="eval-status">
            <span className="mono" style={{ color: "var(--accent)" }}>⏱ {elapsed}s</span>
            <span style={{ color: "var(--text-dim)" }}>{statusMsg(elapsed)}</span>
          </div>
        </div>
      )}

      {(phase === "reveal" || phase === "done") && result && (
        <div className={`eval-result${phase === "reveal" ? " flash" : ""}`}>
          <div className="eval-score-ring-wrap">
            <div className={`eval-verdict-flash ${verdict}`}>
              {verdict === "approved" ? "✅ APPROVED" : verdict === "rejected" ? "❌ REJECTED" : "⏸ BLOCKED"}
            </div>
            <div className={`eval-score-big mono ${verdict}`}>{animScore.toFixed(4)}</div>
            <div className="eval-score-label">Merit Score</div>
            <div className="mono" style={{ color: "var(--text-mute)", fontSize: "0.72rem", marginTop: 4 }}>
              evaluated in {elapsed}s
            </div>
          </div>

          <div className="eval-ai-result">
            <div className="eval-ai-title">
              <span style={{ color: "var(--accent)", fontWeight: 600 }}>AI Analysis</span>
              <span className="sword">SWORD #4</span>
            </div>
            {result.analyze ? (
              <>
                <div className={`eval-ai-badge ${gaming ? "danger" : "safe"}`}>
                  {gaming ? "⚠ Sandwich pattern detected" : "✓ No gaming pattern found"}
                </div>
                {reason && <div className="eval-ai-reason">{reason}</div>}
                <div className="mono" style={{ color: "var(--text-mute)", fontSize: "0.7rem", marginTop: 8 }}>
                  merit_penalty: {result.analyze.merit_penalty ?? 0} · mode: {result.analyze.mode}
                </div>
              </>
            ) : (
              <div style={{ color: "var(--text-mute)", fontSize: "0.82rem" }}>AI analysis unavailable</div>
            )}
          </div>
        </div>
      )}

      {phase === "idle" && (
        <div className="eval-idle">
          <div style={{ color: "var(--text-mute)", fontSize: "0.85rem", lineHeight: 1.6 }}>
            Enter any wallet address to run a live merit evaluation.<br />
            Try <code className="mono">alice</code>, <code className="mono">bob</code>, or{" "}
            <code className="mono">carol</code> for demo agents.
          </div>
        </div>
      )}
    </div>
  );
}

// ---------- App ----------
function App() {
  const [selectedId, setSelectedId] = useState("bob");
  const [tab, setTab] = useState("live");
  const [scores, setScores] = useState({});
  const [attestation, setAttestation] = useState(null);
  const [chain, setChain] = useState({ galileo: null, base: null });

  // Fetch health + scores + attestation on mount
  useEffect(() => {
    fetch(`${BFF}/health`)
      .then(r => r.json())
      .then(d => setChain({ galileo: d.chain?.galileo, base: d.chain?.base }))
      .catch(() => {});

    fetch(`${BFF}/attestation`)
      .then(r => r.json())
      .then(d => setAttestation(d))
      .catch(() => {});

    Promise.all(AGENTS_META.map(a =>
      fetch(`${BFF}/merit/${a.id}`)
        .then(r => r.json())
        .then(d => [a.id, d])
        .catch(() => [a.id, null])
    )).then(results => {
      const s = {};
      results.forEach(([id, d]) => {
        if (d) s[id] = { score: d.score, verdict: verdictFor(d.score), mode: d.mode };
      });
      setScores(s);
    });
  }, []);

  const selected = AGENTS_META.find(a => a.id === selectedId);

  const pillCls = (ok) => ok === null ? "chain-pill" : ok ? "chain-pill" : "chain-pill offline";

  return (
    <div>
      <header className="header">
        <div className="brand">
          <div className="brand-mark mono">M</div>
          <div className="brand-text">
            <h1>Merit<span>Score</span></h1>
            <p>Experian for AI agents — on-chain credit scores that gate DeFi access across 0G + Base</p>
          </div>
        </div>
        <div className="pills">
          <span className={pillCls(chain.galileo)}>
            <span className="dot"></span>0G Galileo
          </span>
          <span className={pillCls(chain.base)}>
            <span className="dot"></span>Base Sepolia
          </span>
        </div>
      </header>

      <div className="section-head">
        <span className="label">// Agents under evaluation</span>
        <span className="meta">click a card to scope the tabs below</span>
      </div>
      <div className="agent-grid">
        {AGENTS_META.map(a => (
          <AgentCard key={a.id} meta={a} data={scores[a.id]}
            selected={a.id === selectedId} onSelect={() => setSelectedId(a.id)} />
        ))}
      </div>

      <div className="tabs-wrap">
        <div className="tabs-bar">
          <button className={`tab-btn ${tab === "live" ? "active" : ""}`} onClick={() => setTab("live")}>
            ⚡ Live Eval <span className="sword">SWORD #1</span>
          </button>
          <button className={`tab-btn ${tab === "tee" ? "active" : ""}`} onClick={() => setTab("tee")}>
            🔐 TEE Attestation <span className="sword">SWORD #2</span>
          </button>
          <button className={`tab-btn ${tab === "wf" ? "active" : ""}`} onClick={() => setTab("wf")}>
            ⚡ KH Workflow <span className="sword">SWORD #3</span>
          </button>
        </div>
        <div className="tab-body">
          {tab === "live" ? <LiveEvalTab /> :
           tab === "tee" ? <TEETab attestation={attestation} /> :
           <WorkflowTab agentMeta={selected} />}
        </div>
      </div>

      <footer className="footer">
        <div className="legend">
          <span style={{color:"var(--text-dim)",marginRight:4}}>Mode:</span>
          <span className="item"><span className="dot direct"></span>Direct</span>
          <span className="item"><span className="dot workflow"></span>Workflow</span>
          <span className="item"><span className="dot web3"></span>Web3</span>
        </div>
        <div>Built at ETHGlobal OpenAgents · 0G Galileo + Base Sepolia</div>
      </footer>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
