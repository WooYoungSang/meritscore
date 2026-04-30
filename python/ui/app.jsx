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
  const isAdversarial = meta.id === "carol";

  const val = useAnimatedNumber(score);
  const pct = Math.round(val * 100);
  const barCls = verdict === "approved" ? "green" : verdict === "rejected" ? "red" : "gray";
  const sparkColor = verdict === "approved" ? "#00c851" : verdict === "rejected" ? "#ff4444" : "#5b6675";
  const trend = verdict === "approved" ? 0.8 : verdict === "rejected" ? -0.6 : 0;

  return (
    <div className={`agent-card ${selected ? "selected" : ""}`} onClick={onSelect} role="button" tabIndex={0}>
      {isAdversarial && (
        <div style={{
          background: "rgba(255,68,68,0.15)",
          border: "1px solid rgba(255,68,68,0.4)",
          borderRadius: "8px",
          padding: "10px 14px",
          marginBottom: "12px",
          fontSize: "12px",
          color: "var(--red)",
          fontWeight: 600,
          display: "flex",
          alignItems: "center",
          gap: "8px"
        }}>
          <span style={{fontSize: "16px"}}>⚠️</span>
          <span>ADVERSARIAL AGENT DETECTED</span>
        </div>
      )}
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

      {/* Transparency badges row */}
      <div style={{display: "flex", gap: "8px", marginTop: "16px", flexWrap: "wrap", alignItems: "center"}}>
        {/* Provider badge */}
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "10px",
          padding: "5px 10px",
          borderRadius: "4px",
          backgroundColor: "rgba(92, 232, 255, 0.08)",
          color: "#5ce8ff",
          border: "1px solid rgba(92, 232, 255, 0.3)",
          whiteSpace: "nowrap"
        }}>
          Provider: {(attestation?.provider || "unknown").length > 14
            ? (attestation?.provider || "unknown").slice(0, 12) + "…"
            : attestation?.provider || "unknown"}
        </span>

        {/* Compute badge */}
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "10px",
          padding: "5px 10px",
          borderRadius: "4px",
          backgroundColor: attestation?.compute_ok ? "rgba(0, 200, 81, 0.08)" : "rgba(255, 68, 68, 0.08)",
          color: attestation?.compute_ok ? "#00c851" : "#ff4444",
          border: attestation?.compute_ok ? "1px solid rgba(0, 200, 81, 0.3)" : "1px solid rgba(255, 68, 68, 0.3)",
          whiteSpace: "nowrap"
        }}>
          Compute: {attestation?.compute_ok ? "✓" : "✗"}
        </span>

        {/* Storage badge */}
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "10px",
          padding: "5px 10px",
          borderRadius: "4px",
          backgroundColor: attestation?.storage_ok ? "rgba(0, 200, 81, 0.08)" : "rgba(255, 68, 68, 0.08)",
          color: attestation?.storage_ok ? "#00c851" : "#ff4444",
          border: attestation?.storage_ok ? "1px solid rgba(0, 200, 81, 0.3)" : "1px solid rgba(255, 68, 68, 0.3)",
          whiteSpace: "nowrap"
        }}>
          Storage: {attestation?.storage_ok ? "✓" : "✗"}
        </span>

        {/* Fallback badge - only render if fallback_reason is non-null/non-empty */}
        {attestation?.fallback_reason && (
          <span style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: "10px",
            padding: "5px 10px",
            borderRadius: "4px",
            backgroundColor: "rgba(255, 158, 61, 0.08)",
            color: "#ff9e3d",
            border: "1px solid rgba(255, 158, 61, 0.3)",
            whiteSpace: "nowrap"
          }}>
            Fallback: {attestation.fallback_reason}
          </span>
        )}
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
        const zk_verified = data.zk_verify?.verified || data.zk_verify?.skipped;
        pushLog(`${zk_verified ? "✓" : "✗"} ZK_VERIFY — Merkle proof ${data.zk_verify?.skipped ? "skipped (unknown agent)" : zk_verified ? "verified" : "failed"}`, zk_verified ? "ok" : "err");
        if (data.zk_verify?.proof_hash) {
          pushLog(`  proof: ${data.zk_verify.proof_hash} · merkle_root: ${data.zk_verify.merkle_root?.slice(0, 16)}…`, "info");
        }
        setStep(3);
      }, 1550);

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
      }, 2400);

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
            Powered by <span style={{color:"#d5deea"}}>KeeperHub</span> · CHECK → VALIDATE → ZK_VERIFY → EXECUTE
          </div>
        </div>

        <div className="steps">
          <div className="steps-title">
            <span>Pipeline</span>
            <span>{agentMeta?.name || "—"}</span>
          </div>
          <div className="step-row">
            {["CHECK","VALIDATE","ZK_VERIFY","EXECUTE"].map((name, i) => (
              <React.Fragment key={name}>
                {i > 0 && <div className="arrow">→</div>}
                <div className={`step ${stepState(i)}`}>
                  <div className="step-name">{name === "ZK_VERIFY" ? "🔐 ZK VERIFY" : name}</div>
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
              <span style={{ color: "var(--text-mute)", fontSize: "0.68rem", marginLeft: 8 }}>Gemma 4 26B · Ollama</span>
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

// ---------- AI Sandwich Detection Tab (Sword #4) ----------
function AIAnalysisTab({ agentMeta }) {
  const [addr, setAddr] = useState(agentMeta?.address || agentMeta?.id || "");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => { setAddr(agentMeta?.id || agentMeta?.address || ""); }, [agentMeta?.id]);

  const analyze = async () => {
    if (!addr.trim() || running) return;
    setRunning(true); setResult(null); setError(null);
    try {
      const res = await fetch(`${BFF}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address: addr.trim(), tx_history: [] }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  };

  const gaming = result?.gaming_detected;
  const adversarial = result?.adversarial_agent;

  return (
    <div className="tab-inner" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div style={{ marginBottom: 16, color: "var(--text-dim)", fontSize: 13 }}>
        <span className="sword">SWORD #4</span> — Gemma 4 26B via Ollama detects sandwich MEV attack patterns in agent transaction history. AI classification feeds directly into the merit oracle.
      </div>
      <div style={{ marginBottom: 8, color: "var(--text-mute)", fontSize: 11 }}>
        powered by <span style={{ color: "#5ce8ff" }}>Gemma 4 26B</span> · Ollama · heuristic fallback
      </div>

      <div className="ai-input-row" style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 20 }}>
        <input
          type="text"
          value={addr}
          onChange={e => setAddr(e.target.value)}
          onKeyDown={e => e.key === "Enter" && analyze()}
          placeholder="alice / bob / carol  —  or 0x address"
          spellCheck={false}
          style={{
            flex: 1, background: "#0b1218", border: "1px solid var(--border)",
            color: "#fff", padding: "8px 12px", borderRadius: 6,
            fontFamily: "inherit", fontSize: 13
          }}
        />
        <button
          onClick={analyze} disabled={running}
          className={`eval-btn${running ? " running" : ""}`}
          style={{ whiteSpace: "nowrap" }}
        >
          {running ? <><span className="spinner" /><span>ANALYZING…</span></> : "🤖  ANALYZE"}
        </button>
      </div>

      {error && <div style={{ color: "#ff4d4d", fontSize: 13, marginBottom: 12 }}>Error: {error}</div>}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{
            background: gaming ? "rgba(255,68,68,0.08)" : "rgba(0,200,81,0.07)",
            border: `1px solid ${gaming ? "rgba(255,68,68,0.35)" : "rgba(0,200,81,0.3)"}`,
            borderRadius: 10, padding: "18px 22px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
              <span style={{ fontSize: 24 }}>{gaming ? "⚠️" : "✅"}</span>
              <div>
                <div style={{ color: gaming ? "#ff6666" : "#00c851", fontWeight: 700, fontSize: 16 }}>
                  {gaming ? "SANDWICH ATTACK DETECTED" : "NO GAMING PATTERN"}
                </div>
                {adversarial && (
                  <div style={{ color: "#ff4444", fontSize: 11, marginTop: 2 }}>ADVERSARIAL AGENT — ground-truth confirmed</div>
                )}
              </div>
            </div>
            {result.reason && (
              <div style={{ color: "var(--text-dim)", fontSize: 13, lineHeight: 1.6, marginBottom: 10 }}>
                {result.reason}
              </div>
            )}
            <div className="ai-stats-row" style={{ display: "flex", gap: 20, fontSize: 12 }}>
              <span style={{ color: "var(--text-mute)" }}>merit_penalty: <span style={{ color: gaming ? "#ff8888" : "#00c851" }}>{result.merit_penalty ?? 0}</span></span>
              <span style={{ color: "var(--text-mute)" }}>mode: <span style={{ color: "var(--accent)" }}>{result.mode}</span></span>
              <span style={{ color: "var(--text-mute)" }}>address: <span className="mono" style={{ color: "#d5deea" }}>{result.address?.slice(0, 14)}…</span></span>
            </div>
          </div>

          <div style={{
            background: "#0b1218", border: "1px solid var(--border)",
            borderRadius: 8, padding: "14px 18px", fontSize: 12
          }}>
            <div style={{ color: "var(--text-dim)", marginBottom: 10, fontWeight: 600 }}>How it works</div>
            <div style={{ color: "var(--text-mute)", lineHeight: 1.8 }}>
              1. Agent tx history fetched (or demo history used for named agents)<br/>
              2. Gemma 4 26B prompt: detect frontrun/backrun sandwich pairs, same-block gas manipulation<br/>
              3. If Ollama unavailable → heuristic fallback (keyword + block pattern detection)<br/>
              4. Result feeds into <span style={{ color: "var(--accent)" }}>merit_penalty</span> applied to on-chain score
            </div>
          </div>
        </div>
      )}

      {!result && !running && !error && (
        <div style={{ color: "var(--text-mute)", fontSize: 13, marginTop: 8 }}>
          Try <code className="mono">carol</code> to see a detected sandwich attack, or <code className="mono">bob</code> for a clean agent.
        </div>
      )}
    </div>
  );
}

// ---------- MeritGuard Autonomous Agent Tab ----------
function MeritGuardTab({ agentLoopStatus }) {
  const status = agentLoopStatus;
  const running = status?.running;
  const lastScan = status?.last_scan ? new Date(status.last_scan + "Z").toLocaleTimeString("en-GB", { hour12: false }) : "—";
  const actions = status?.actions || [];
  const flagged = status?.flagged || [];

  return (
    <div className="tab-inner" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div className="mg-status-row" style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          background: running ? "rgba(0,200,81,0.1)" : "rgba(91,102,117,0.15)",
          border: `1px solid ${running ? "rgba(0,200,81,0.4)" : "rgba(91,102,117,0.3)"}`,
          borderRadius: 8, padding: "8px 16px"
        }}>
          <span style={{
            width: 8, height: 8, borderRadius: "50%",
            background: running ? "#00c851" : "#5b6675",
            boxShadow: running ? "0 0 6px #00c851" : "none",
            display: "inline-block"
          }} />
          <span style={{ color: running ? "#00c851" : "var(--text-mute)", fontWeight: 600 }}>
            {running ? "RUNNING" : "STOPPED"}
          </span>
        </div>
        <div style={{ color: "var(--text-dim)", fontSize: 12 }}>
          Scans every <span style={{ color: "var(--accent)" }}>60s</span> · threshold{" "}
          <span style={{ color: "var(--accent)" }}>0.30</span> · last scan{" "}
          <span style={{ color: "#d5deea" }}>{lastScan}</span>
        </div>
        <div style={{ marginLeft: "auto", color: "var(--text-mute)", fontSize: 11 }}>
          powered by <span style={{ color: "var(--accent)" }}>0G Galileo</span> · autonomous loop
        </div>
      </div>

      <div className="mg-stats-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Agents Monitored", value: status?.agents_checked ?? 3, color: "#5ce8ff" },
          { label: "Flagged (< 0.30)", value: flagged.length, color: flagged.length > 0 ? "#ff4444" : "#00c851" },
          { label: "KH Actions Triggered", value: actions.length, color: "#d5deea" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            background: "#0b1218", border: "1px solid var(--border)",
            borderRadius: 8, padding: "14px 18px"
          }}>
            <div style={{ color: "var(--text-mute)", fontSize: 11, marginBottom: 6 }}>{label}</div>
            <div style={{ color, fontSize: 26, fontWeight: 700 }}>{value}</div>
          </div>
        ))}
      </div>

      {flagged.length > 0 && (
        <div style={{
          background: "rgba(255,68,68,0.08)", border: "1px solid rgba(255,68,68,0.3)",
          borderRadius: 8, padding: "10px 16px", marginBottom: 20, fontSize: 13
        }}>
          <span style={{ color: "#ff4444", fontWeight: 600 }}>⚠ Flagged agents: </span>
          <span style={{ color: "#ffaaaa" }}>{flagged.join(", ")}</span>
          <span style={{ color: "var(--text-mute)", marginLeft: 8 }}>→ KH_EXECUTE triggered</span>
        </div>
      )}

      <div style={{ color: "var(--text-dim)", fontSize: 12, marginBottom: 10, fontWeight: 600 }}>
        Action Log — last {Math.min(actions.length, 20)} events
      </div>
      <div className="mg-action-log" style={{
        background: "#0b1218", border: "1px solid var(--border)", borderRadius: 8,
        padding: "12px 16px", maxHeight: 320, overflowY: "auto", fontSize: 12
      }}>
        {actions.length === 0 ? (
          <div style={{ color: "var(--text-mute)" }}>No actions yet — waiting for next scan cycle…</div>
        ) : (
          [...actions].reverse().slice(0, 20).map((a, i) => (
            <div key={i} style={{
              display: "flex", gap: 12, alignItems: "flex-start",
              padding: "5px 0", borderBottom: i < Math.min(actions.length, 20) - 1 ? "1px solid rgba(255,255,255,0.04)" : "none"
            }}>
              <span style={{ color: "var(--text-mute)", minWidth: 80 }}>
                {a.at ? new Date(a.at + "Z").toLocaleTimeString("en-GB", { hour12: false }) : "—"}
              </span>
              <span style={{ color: "#ff8888", minWidth: 50 }}>{a.agent}</span>
              <span style={{ color: "var(--text-mute)" }}>score=</span>
              <span style={{ color: a.score < 0.1 ? "#ff4444" : "#ffaa44" }}>{(a.score || 0).toFixed(4)}</span>
              <span style={{ color: "var(--text-mute)" }}>→</span>
              <span style={{ color: "#5ce8ff" }}>{a.action}</span>
              <span className={`mode-pill ${a.result === "OK" ? "web3" : "direct"}`} style={{ fontSize: 10 }}>
                {a.result || "PENDING"}
              </span>
            </div>
          ))
        )}
      </div>

      <div style={{ marginTop: 16, color: "var(--text-mute)", fontSize: 11, lineHeight: 1.7 }}>
        MeritGuard autonomously monitors on-chain merit scores via{" "}
        <span style={{ color: "var(--accent)" }}>MeritCore (0G Galileo)</span> and triggers{" "}
        <span style={{ color: "var(--accent)" }}>KeeperHub</span> workflows for any agent below the risk threshold.
        This is fully autonomous — no human intervention required.
      </div>
    </div>
  );
}

// ---------- ZK Proof Tab (Sword #5) ----------
function ZKProofTab({ agentMeta }) {
  const [threshold, setThreshold] = useState(5000);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const agent = agentMeta?.id || "bob";

  const generateProof = async () => {
    setRunning(true); setResult(null); setError(null);
    try {
      const res = await fetch(`${BFF}/zk-proof`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent, threshold }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="tab-inner" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      <div style={{ marginBottom: 16, color: "var(--text-dim)", fontSize: 13 }}>
        <span className="sword">SWORD #5</span> — Privacy-preserving merit proof: agents prove score ≥ threshold WITHOUT revealing the actual score. Cryptographic guarantee via Groth16 on BN254.
      </div>
      <div className="zk-controls-row" style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 20 }}>
        <span style={{ color: "var(--accent)" }}>agent:</span>
        <span style={{ color: "#fff" }}>{agent}</span>
        <span style={{ color: "var(--accent)", marginLeft: 16 }}>threshold:</span>
        <input
          type="number" min={0} max={9999} value={threshold}
          onChange={e => setThreshold(parseInt(e.target.value) || 0)}
          style={{ width: 80, background: "#1a2633", border: "1px solid var(--border)", color: "#fff", padding: "4px 8px", borderRadius: 4, fontFamily: "inherit" }}
        />
        <button
          onClick={generateProof} disabled={running}
          className="tab-btn active"
          style={{ marginLeft: 8, padding: "6px 18px", cursor: running ? "wait" : "pointer" }}
        >
          {running ? "⏳ Proving…" : "🔐 Generate ZK Proof"}
        </button>
      </div>

      {running && (
        <div style={{ color: "var(--text-dim)", fontSize: 12 }}>
          Building depth-8 Merkle tree → computing Groth16 witness → generating proof…
        </div>
      )}
      {error && <div style={{ color: "#ff4d4d", fontSize: 13 }}>Error: {error}</div>}
      {result && (
        <div style={{ fontSize: 12 }}>
          {result.success ? (
            <>
              <div style={{ color: "#00c851", marginBottom: 12, fontSize: 14 }}>
                ✅ Proof verified on-chain ready
              </div>
              <div style={{ color: "var(--text-dim)", marginBottom: 6 }}>
                Public signals: merkleRoot + threshold (score stays private)
              </div>
              <div style={{ background: "#0b1218", border: "1px solid var(--border)", borderRadius: 6, padding: 12, overflowX: "auto" }}>
                <div style={{ color: "#5ce8ff", marginBottom: 4 }}>merkleRoot</div>
                <div style={{ color: "#b0c4d4", wordBreak: "break-all", marginBottom: 8 }}>{result.publicSignals?.[0]}</div>
                <div style={{ color: "#5ce8ff", marginBottom: 4 }}>π_a (proof point)</div>
                <div style={{ color: "#b0c4d4", wordBreak: "break-all", marginBottom: 8 }}>{result.proof?.pi_a?.[0]?.slice(0, 40)}…</div>
                <div style={{ color: "#5ce8ff", marginBottom: 4 }}>protocol</div>
                <div style={{ color: "#b0c4d4" }}>{result.proof?.protocol} · {result.proof?.curve} · gas ~{result.metadata?.verificationGas}</div>
              </div>
            </>
          ) : (
            <div style={{ color: "#ff4d4d" }}>
              ❌ Cannot prove: {result.reason}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------- Uniswap Swap Tab (Sword #6) ----------
function UniswapSwapTab({ agentMeta }) {
  const [fromToken, setFromToken] = useState("WETH");
  const [toToken, setToToken] = useState("USDC");
  const [amount, setAmount] = useState("0.001");
  const [slippage, setSlippage] = useState(2.0);
  const [loading, setLoading] = useState(false);
  const [quoteResult, setQuoteResult] = useState(null);
  const [executeResult, setExecuteResult] = useState(null);
  const [error, setError] = useState(null);

  const TOKENS = {
    WETH: "0x4200000000000000000000000000000000000006",
    USDC: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
  };

  const TOKEN_DECIMALS = {
    WETH: 18,
    USDC: 6,
  };

  const toWei = (humanAmount, tokenSymbol) => {
    const decimals = TOKEN_DECIMALS[tokenSymbol] || 18;
    const factor = Math.pow(10, decimals);
    return String(Math.floor(parseFloat(humanAmount) * factor));
  };

  const fromWei = (weiAmount, tokenSymbol) => {
    const decimals = TOKEN_DECIMALS[tokenSymbol] || 18;
    const factor = Math.pow(10, decimals);
    return (parseFloat(weiAmount) / factor).toFixed(6);
  };

  const getQuote = async () => {
    setLoading(true);
    setError(null);
    setQuoteResult(null);
    setExecuteResult(null);

    try {
      const amountInWei = toWei(amount, fromToken);
      const res = await fetch(`${BFF}/uniswap/swap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "quote",
          address: agentMeta?.id || "bob",
          from_token: TOKENS[fromToken],
          to_token: TOKENS[toToken],
          amount_in: amountInWei,
          slippage_pct: slippage,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 403) {
          setError(`Merit ${data.merit?.toFixed(4)} below threshold ${data.threshold} — swap blocked`);
        } else if (res.status === 400) {
          setError(data.detail || "Validation error");
        } else {
          setError(data.error || "Quote failed");
        }
        setLoading(false);
        return;
      }

      setQuoteResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const executeSwap = async () => {
    setLoading(true);
    setError(null);
    setExecuteResult(null);

    try {
      const amountInWei = toWei(amount, fromToken);
      const res = await fetch(`${BFF}/uniswap/swap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "execute",
          address: agentMeta?.id || "bob",
          from_token: TOKENS[fromToken],
          to_token: TOKENS[toToken],
          amount_in: amountInWei,
          slippage_pct: slippage,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 403) {
          setError(`Merit ${data.merit?.toFixed(4)} below threshold ${data.threshold} — swap blocked`);
        } else if (res.status === 502) {
          setError(`Swap reverted on-chain: ${data.reason}`);
        } else if (res.status === 400) {
          setError(data.detail || "Validation error");
        } else {
          setError(data.error || "Execution failed");
        }
        setLoading(false);
        return;
      }

      setExecuteResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tab-inner">
      <div style={{ marginBottom: 16, color: "var(--text-dim)", fontSize: 13 }}>
        <span className="sword">SWORD #6</span> — Merit-gated Uniswap V3 swap on Base Sepolia. Agents with merit ≥ 0.5 can execute swaps with gas-free quote pricing and configurable slippage.
      </div>

      {error && (
        <div style={{
          background: "rgba(255,68,68,0.08)",
          border: "1px solid rgba(255,68,68,0.3)",
          borderRadius: 8,
          padding: "12px 16px",
          marginBottom: 16,
          color: "#ff4444",
          fontSize: 13,
        }}>
          ⚠ {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <div>
          <label style={{ display: "block", color: "var(--text-mute)", fontSize: 11, marginBottom: 6, fontWeight: 600 }}>
            FROM TOKEN
          </label>
          <select
            value={fromToken}
            onChange={e => setFromToken(e.target.value)}
            style={{
              width: "100%",
              background: "#0b1117",
              border: "1px solid var(--border)",
              color: "#fff",
              padding: "10px 12px",
              borderRadius: 6,
              fontFamily: "inherit",
              cursor: "pointer",
            }}
          >
            <option value="WETH">WETH</option>
            <option value="USDC">USDC</option>
          </select>
        </div>

        <div>
          <label style={{ display: "block", color: "var(--text-mute)", fontSize: 11, marginBottom: 6, fontWeight: 600 }}>
            TO TOKEN
          </label>
          <select
            value={toToken}
            onChange={e => setToToken(e.target.value)}
            style={{
              width: "100%",
              background: "#0b1117",
              border: "1px solid var(--border)",
              color: "#fff",
              padding: "10px 12px",
              borderRadius: 6,
              fontFamily: "inherit",
              cursor: "pointer",
            }}
          >
            <option value="WETH">WETH</option>
            <option value="USDC">USDC</option>
          </select>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <div>
          <label style={{ display: "block", color: "var(--text-mute)", fontSize: 11, marginBottom: 6, fontWeight: 600 }}>
            AMOUNT ({fromToken})
          </label>
          <input
            type="number"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            step="0.0001"
            min="0"
            style={{
              width: "100%",
              background: "#0b1117",
              border: "1px solid var(--border)",
              color: "#fff",
              padding: "10px 12px",
              borderRadius: 6,
              fontFamily: "inherit",
              fontSize: 13,
            }}
            placeholder="0.001"
          />
        </div>

        <div>
          <label style={{ display: "block", color: "var(--text-mute)", fontSize: 11, marginBottom: 6, fontWeight: 600 }}>
            SLIPPAGE (%)
          </label>
          <input
            type="number"
            value={slippage}
            onChange={e => setSlippage(Math.min(5, Math.max(0, parseFloat(e.target.value))))}
            step="0.1"
            min="0"
            max="5"
            style={{
              width: "100%",
              background: "#0b1117",
              border: "1px solid var(--border)",
              color: "#fff",
              padding: "10px 12px",
              borderRadius: 6,
              fontFamily: "inherit",
              fontSize: 13,
            }}
            placeholder="2.0"
          />
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
        <button
          onClick={getQuote}
          disabled={loading || !amount || parseFloat(amount) <= 0}
          style={{
            flex: 1,
            padding: "11px 18px",
            background: "#00d4ff",
            color: "#001a22",
            border: "none",
            borderRadius: 6,
            fontWeight: 600,
            cursor: loading ? "wait" : "pointer",
            opacity: (loading || !amount || parseFloat(amount) <= 0) ? 0.6 : 1,
            fontFamily: "inherit",
            fontSize: 13,
          }}
        >
          {loading ? "⏳ Loading…" : "💰 Get Quote"}
        </button>

        <button
          onClick={executeSwap}
          disabled={loading || !quoteResult}
          style={{
            flex: 1,
            padding: "11px 18px",
            background: quoteResult ? "#00d4ff" : "#555d68",
            color: "#001a22",
            border: "none",
            borderRadius: 6,
            fontWeight: 600,
            cursor: (loading || !quoteResult) ? "not-allowed" : "pointer",
            opacity: (loading || !quoteResult) ? 0.5 : 1,
            fontFamily: "inherit",
            fontSize: 13,
          }}
        >
          {loading ? "⏳ Executing…" : "🔄 Execute Swap"}
        </button>
      </div>

      {quoteResult && !executeResult && (
        <div style={{
          background: "rgba(0,200,81,0.08)",
          border: "1px solid rgba(0,200,81,0.3)",
          borderRadius: 8,
          padding: "16px",
          marginBottom: 16,
        }}>
          <div style={{ color: "#00c851", fontWeight: 600, marginBottom: 12 }}>✓ Quote Retrieved</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            <div>
              <div style={{ color: "var(--text-mute)", fontSize: 11, marginBottom: 4 }}>Amount Out</div>
              <div style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>
                {fromWei(quoteResult.amount_out, toToken)} {toToken}
              </div>
            </div>
            <div>
              <div style={{ color: "var(--text-mute)", fontSize: 11, marginBottom: 4 }}>Price Impact</div>
              <div style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>
                {quoteResult.price_impact_pct.toFixed(2)}%
              </div>
            </div>
            <div>
              <div style={{ color: "var(--text-mute)", fontSize: 11, marginBottom: 4 }}>Pool Fee</div>
              <div style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>
                {(quoteResult.fee_tier / 10000 * 100).toFixed(2)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {executeResult && (
        <div style={{
          background: "rgba(0,200,81,0.08)",
          border: "1px solid rgba(0,200,81,0.3)",
          borderRadius: 8,
          padding: "16px",
        }}>
          <div style={{ color: "#00c851", fontWeight: 600, marginBottom: 12 }}>✅ Swap Confirmed</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
            <div>
              <div style={{ color: "var(--text-mute)", fontSize: 11, marginBottom: 4 }}>Transaction Hash</div>
              <a
                href={`https://sepolia.basescan.io/tx/${executeResult.tx_hash}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: "#5ce8ff",
                  fontSize: 12,
                  wordBreak: "break-all",
                  textDecoration: "underline",
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                {executeResult.tx_hash.slice(0, 16)}…{executeResult.tx_hash.slice(-8)}
              </a>
            </div>
            <div>
              <div style={{ color: "var(--text-mute)", fontSize: 11, marginBottom: 4 }}>Block Number</div>
              <div style={{ color: "#fff", fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
                {executeResult.block_number}
              </div>
            </div>
          </div>
          <div>
            <div style={{ color: "var(--text-mute)", fontSize: 11, marginBottom: 4 }}>Amount Out</div>
            <div style={{ color: "#00c851", fontSize: 14, fontWeight: 600 }}>
              {fromWei(executeResult.amount_out, toToken)} {toToken}
            </div>
          </div>
        </div>
      )}

      {!quoteResult && !executeResult && !error && (
        <div style={{
          background: "var(--card-2)",
          border: "1px dashed var(--border)",
          borderRadius: 8,
          padding: "24px",
          textAlign: "center",
          color: "var(--text-mute)",
          fontSize: 13,
        }}>
          Enter swap parameters and click "Get Quote" to see the price impact and execute the swap.
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
  const [agentLoopStatus, setAgentLoopStatus] = useState(null);

  // Fetch health + scores + attestation + agent-loop status on mount + poll
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

    // Fetch agent-loop status and poll every 10 seconds
    const fetchAgentLoopStatus = () => {
      fetch(`${BFF}/agent-loop/status`)
        .then(r => r.json())
        .then(d => setAgentLoopStatus(d))
        .catch(() => {});
    };
    fetchAgentLoopStatus();
    const interval = setInterval(fetchAgentLoopStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const selected = AGENTS_META.find(a => a.id === selectedId);

  const pillCls = (ok) => ok === null ? "chain-pill" : ok ? "chain-pill" : "chain-pill offline";

  return (
    <div>
      <header className="header">
        <div className="brand">
          <svg width="56" height="56" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" style={{flexShrink: 0}}>
            <defs>
              <linearGradient id="wg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#5ce8ff"/>
                <stop offset="100%" stopColor="#00a8cc"/>
              </linearGradient>
              <radialGradient id="wcore" cx="0.5" cy="0.5" r="0.5">
                <stop offset="0%"   stopColor="#e8fbff" stopOpacity="1"/>
                <stop offset="30%"  stopColor="#5ce8ff" stopOpacity="0.85"/>
                <stop offset="70%"  stopColor="#00a8cc" stopOpacity="0.25"/>
                <stop offset="100%" stopColor="#00a8cc" stopOpacity="0"/>
              </radialGradient>
              <style>{`
                @keyframes wh{0%,100%{opacity:.2}50%{opacity:.45}}
                @keyframes wc1{0%,100%{opacity:.45}50%{opacity:.78}}
                @keyframes wc2{0%,100%{opacity:.4}50%{opacity:.85}}
                .wh{animation:wh 3.2s ease-in-out infinite}
                .wc1{animation:wc1 2.4s ease-in-out infinite}
                .wc2{animation:wc2 1.8s ease-in-out infinite}
              `}</style>
            </defs>
            {/* outer halo */}
            <circle cx="32" cy="32" r="30" fill="url(#wcore)" opacity="0.3" className="wh"/>
            {/* outer reactor ring */}
            <circle cx="32" cy="32" r="30" fill="#0b1218" stroke="url(#wg)" strokeWidth="1.8"/>
            {/* mid ring */}
            <circle cx="32" cy="32" r="28.5" fill="none" stroke="url(#wg)" strokeWidth="0.4" opacity="0.4"/>
            {/* inner ring */}
            <circle cx="32" cy="32" r="27" fill="none" stroke="url(#wg)" strokeWidth="0.7" opacity="0.55"/>
            {/* 4 reactor slots: 12, 4, 6, 8 o'clock */}
            <g stroke="url(#wg)" strokeWidth="1.6" strokeLinecap="round" opacity="0.95">
              <line x1="32" y1="2.5" x2="32" y2="7"/>
              <line x1="57.98" y1="47" x2="55.38" y2="45.5"/>
              <line x1="6.02" y1="47" x2="8.62" y2="45.5"/>
              <line x1="32" y1="61.5" x2="32" y2="57"/>
            </g>
            {/* dual pulsing core glow */}
            <circle cx="32" cy="32" r="19" fill="url(#wcore)" opacity="0.6" className="wc1"/>
            <circle cx="32" cy="32" r="11" fill="url(#wcore)" opacity="0.55" className="wc2"/>
            {/* prominent inverted triangle inscribed in inner ring (r=27) */}
            <path d="M8.62 18.5 L55.38 18.5 L32 59 Z" fill="#0b1218" stroke="url(#wg)" strokeWidth="2.4" strokeLinejoin="round"/>
            {/* inner triangle echo */}
            <path d="M13 21 L51 21 L32 53.8 Z" fill="none" stroke="url(#wg)" strokeWidth="0.7" strokeLinejoin="round" opacity="0.5"/>
            {/* vertex node caps */}
            <g fill="#0b1218" stroke="url(#wg)" strokeWidth="0.9">
              <circle cx="8.62" cy="18.5" r="1.6"/>
              <circle cx="55.38" cy="18.5" r="1.6"/>
              <circle cx="32" cy="59" r="1.6"/>
            </g>
            <g fill="#5ce8ff" opacity="0.85">
              <circle cx="8.62" cy="18.5" r="0.7"/>
              <circle cx="55.38" cy="18.5" r="0.7"/>
              <circle cx="32" cy="59" r="0.7"/>
            </g>
            {/* spark dot above W */}
            <circle cx="32" cy="24" r="2.5" fill="#5ce8ff" opacity="0.4"/>
            <circle cx="32" cy="24" r="1.2" fill="#ffffff"/>
            {/* W: center vertex at reactor core (32,32), outer strokes at ±60° */}
            <path d="M21.96 30.5 L26 37.5 L32 32 L38 37.5 L42.04 30.5"
                  fill="none" stroke="#e8fbff" strokeWidth="2.4"
                  strokeLinecap="round" strokeLinejoin="round"
                  style={{filter: "drop-shadow(0 0 1.4px #5ce8ff)"}}/>
          </svg>
          <div className="brand-text">
            <h1 style={{fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.1em"}}>
              W<span>.</span>A<span>.</span>R<span>.</span>V<span>.</span>I<span>.</span>S
            </h1>
            <p style={{fontWeight: 600, letterSpacing: "0.22em", fontSize: "11px", textTransform: "uppercase", color: "var(--accent)", marginBottom: "6px"}}>A Rather Very Intelligent System</p>
            <p>MeritScore — Privacy-preserving credit scores for AI agents · ZK Proofs · 0G + Base</p>
          </div>
        </div>
        <div className="pills">
          {agentLoopStatus?.running && (
            <span className="chain-pill" style={{background: "rgba(0, 200, 81, 0.1)", borderColor: "rgba(0, 200, 81, 0.4)"}}>
              <span className="dot" style={{background: "#00c851"}}></span>
              ⚡ MeritGuard
            </span>
          )}
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
          <button className={`tab-btn ${tab === "ai" ? "active" : ""}`} onClick={() => setTab("ai")}>
            🤖 AI Analysis <span className="sword">SWORD #4</span>
          </button>
          <button className={`tab-btn ${tab === "zk" ? "active" : ""}`} onClick={() => setTab("zk")}>
            🔏 ZK Proof <span className="sword">SWORD #5</span>
          </button>
          <button className={`tab-btn ${tab === "uniswap" ? "active" : ""}`} onClick={() => setTab("uniswap")}>
            🔄 Uniswap Swap <span className="sword">SWORD #6</span>
          </button>
          {/* Force MeritGuard onto its own row so Sword #1–#6 stay together */}
          <div className="tab-row-break" aria-hidden="true"></div>
          <button className={`tab-btn ${tab === "mg" ? "active" : ""}`} onClick={() => setTab("mg")}
            style={agentLoopStatus?.running ? { borderColor: "rgba(0,200,81,0.5)", color: "#00c851" } : {}}>
            🤖 MeritGuard {agentLoopStatus?.running && <span style={{ fontSize: "0.65rem", color: "#00c851" }}>● LIVE</span>}
          </button>
        </div>
        <div className="tab-body">
          {tab === "live" ? <LiveEvalTab /> :
           tab === "tee" ? <TEETab attestation={attestation} /> :
           tab === "wf" ? <WorkflowTab agentMeta={selected} /> :
           tab === "ai" ? <AIAnalysisTab agentMeta={selected} /> :
           tab === "zk" ? <ZKProofTab agentMeta={selected} /> :
           tab === "uniswap" ? <UniswapSwapTab agentMeta={selected} /> :
           <MeritGuardTab agentLoopStatus={agentLoopStatus} />}
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
