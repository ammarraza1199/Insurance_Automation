import React, { useState } from 'react';
import axios from 'axios';
import {
  Stethoscope, CheckCircle, XCircle, AlertCircle, Loader,
  Brain, ClipboardList, Hash, FileText
} from 'lucide-react';

const BASE = 'http://localhost:8000';

const STATUS_CONFIG = {
  Approved:      { color: 'var(--secondary)', bg: 'rgba(16,185,129,0.12)', icon: CheckCircle,  label: 'Approved' },
  Denied:        { color: 'var(--danger)',     bg: 'rgba(239,68,68,0.12)',  icon: XCircle,      label: 'Denied'   },
  'Manual Review': { color: 'var(--warning)', bg: 'rgba(245,158,11,0.12)', icon: AlertCircle,  label: 'Manual Review' },
};

function ConfidenceBar({ score }) {
  const pct   = Math.round(score * 100);
  const color = pct >= 70 ? 'var(--secondary)' : pct >= 40 ? 'var(--warning)' : 'var(--danger)';
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>AI Confidence</span>
        <strong style={{ fontSize: '0.9rem', color }}>{pct}%</strong>
      </div>
      <div className="progress-bar-track">
        <div className="progress-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export default function AuthorizationPage() {
  const [cptCode,       setCptCode]       = useState('');
  const [diagCodes,     setDiagCodes]     = useState('');   // comma-separated
  const [medSummary,    setMedSummary]    = useState('');
  const [sessionId,     setSessionId]     = useState('');
  const [result,        setResult]        = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState(null);
  const [history,       setHistory]       = useState([]);

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${BASE}/cpt-logs`);
      setHistory(res.data.slice(-10).reverse());
    } catch {}
  };

  const handleCheck = async () => {
    if (!cptCode.trim()) return;
    setLoading(true); setError(null); setResult(null);
    const diagList = diagCodes.split(',').map(d => d.trim()).filter(Boolean);
    try {
      const res = await axios.post(`${BASE}/authorization/check`, {
        cpt_code:        cptCode.trim(),
        diagnosis_codes: diagList,
        medical_summary: medSummary.trim(),
        session_id:      sessionId.trim() || undefined,
      });
      setResult(res.data);
      setHistory(prev => [res.data, ...prev].slice(0, 10));
    } catch (e) {
      setError('Authorization check failed. Ensure the backend is running and Ollama is active.');
    } finally {
      setLoading(false);
    }
  };

  const QUICK_EXAMPLES = [
    { cpt: '71250', diag: 'R05',  summary: 'Persistent cough for 3 weeks. Abnormal chest X-ray. Doctor recommends CT scan.' },
    { cpt: '27447', diag: 'M17.11', summary: 'Severe osteoarthritis of right knee. Patient failed conservative treatment.' },
    { cpt: '99214', diag: 'E11.9', summary: 'Established patient with Type 2 Diabetes for medication review and HbA1c check.' },
  ];

  const cfg = result ? (STATUS_CONFIG[result.authorization_status] || STATUS_CONFIG['Manual Review']) : null;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Authorization Check</h1>
        <p>Enter CPT code, diagnosis codes, and clinical summary. The AI will evaluate medical necessity and predict authorization outcome.</p>
      </div>

      <div className="content-grid-2">
        {/* ── Input Panel ───────────────────────────────────────────────── */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 22 }}>
            <div style={{ background: 'var(--primary)', padding: 9, borderRadius: 10, display: 'flex' }}>
              <Brain color="white" size={20} />
            </div>
            <div>
              <h2 style={{ margin: 0 }}>AI Authorization Check</h2>
              <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Powered by local LLM (Ollama)</p>
            </div>
          </div>

          {/* Quick examples */}
          <div style={{ marginBottom: 18 }}>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Quick Examples</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {QUICK_EXAMPLES.map(ex => (
                <button key={ex.cpt} className="btn btn-secondary"
                  style={{ padding: '5px 12px', fontSize: '0.8rem' }}
                  onClick={() => { setCptCode(ex.cpt); setDiagCodes(ex.diag); setMedSummary(ex.summary); }}>
                  {ex.cpt}
                </button>
              ))}
            </div>
          </div>

          <div className="input-group">
            <label className="input-label"><Hash size={13} /> CPT Code *</label>
            <input className="input-field" placeholder="e.g. 71250" value={cptCode}
              onChange={e => setCptCode(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleCheck()} />
          </div>

          <div className="input-group">
            <label className="input-label"><ClipboardList size={13} /> Diagnosis Codes (comma-separated)</label>
            <input className="input-field" placeholder="e.g. R05, J18.9, E11.9" value={diagCodes}
              onChange={e => setDiagCodes(e.target.value)} />
          </div>

          <div className="input-group">
            <label className="input-label"><FileText size={13} /> Patient Medical Summary *</label>
            <textarea className="input-field" rows={4}
              placeholder="Describe the patient's clinical situation, symptoms, and rationale for the procedure…"
              value={medSummary} onChange={e => setMedSummary(e.target.value)}
              style={{ resize: 'vertical', fontFamily: 'inherit' }} />
          </div>

          <div className="input-group">
            <label className="input-label">Session ID (optional — links to IV session)</label>
            <input className="input-field" placeholder="Paste session_id from Insurance Verification page"
              value={sessionId} onChange={e => setSessionId(e.target.value)} />
          </div>

          {error && (
            <div style={{ marginBottom: 16, padding: '12px 14px', background: 'rgba(239,68,68,0.08)', color: 'var(--danger)', borderRadius: 8, fontSize: '0.85rem', display: 'flex', gap: 10 }}>
              <AlertCircle size={16} style={{ flexShrink: 0 }} /> {error}
            </div>
          )}

          <button className="btn btn-primary" style={{ width: '100%' }}
            onClick={handleCheck} disabled={loading || !cptCode.trim() || !medSummary.trim()}>
            {loading
              ? <><Loader size={16} className="spinner" /> Querying AI Model…</>
              : <><Brain size={16} /> Check Authorization</>}
          </button>
        </div>

        {/* ── Result Panel ──────────────────────────────────────────────── */}
        <div className="glass-panel">
          <h2 style={{ marginBottom: 20 }}>Authorization Decision</h2>
          {!result ? (
            <div style={{ padding: '48px 20px', textAlign: 'center', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.1)', borderRadius: 10 }}>
              <Stethoscope size={36} style={{ marginBottom: 12, opacity: 0.4 }} />
              <p>Fill in the form and click "Check Authorization" to get an AI-powered decision.</p>
            </div>
          ) : (
            <div className="fade-in">
              {/* Status badge */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 14, padding: '18px 20px', borderRadius: 12,
                background: cfg.bg, marginBottom: 20, border: `1px solid ${cfg.color}30`
              }}>
                {React.createElement(cfg.icon, { size: 28, color: cfg.color })}
                <div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 700, color: cfg.color }}>{cfg.label}</div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>CPT {result.cpt_code}</div>
                </div>
              </div>

              {/* Confidence bar */}
              <div style={{ marginBottom: 20 }}>
                <ConfidenceBar score={result.confidence_score} />
              </div>

              {/* Reason */}
              <div style={{ background: 'rgba(0,0,0,0.15)', borderRadius: 10, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>AI Clinical Reasoning</div>
                <p style={{ margin: 0, lineHeight: 1.7, fontSize: '0.9rem' }}>{result.reason}</p>
              </div>

              {/* Meta */}
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Source: <code style={{ color: 'var(--primary)' }}>{result.source}</code>
                {result.confidence_score < 0.6 && (
                  <div style={{ marginTop: 8, color: 'var(--warning)', display: 'flex', gap: 6, alignItems: 'center' }}>
                    <AlertCircle size={13} /> Low confidence — consider manual clinical review.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recent history */}
          {history.length > 0 && (
            <div style={{ marginTop: 28 }}>
              <h3 style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: 10, textTransform: 'uppercase' }}>Recent Checks</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {history.slice(0, 5).map((h, i) => {
                  const c = STATUS_CONFIG[h.authorization_status] || STATUS_CONFIG['Manual Review'];
                  return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'rgba(0,0,0,0.1)', borderRadius: 8, fontSize: '0.85rem' }}>
                      {React.createElement(c.icon, { size: 14, color: c.color })}
                      <code style={{ color: 'var(--primary)' }}>{h.cpt_code || h.cpt_code}</code>
                      <span style={{ color: c.color, marginLeft: 'auto' }}>{h.authorization_status}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
