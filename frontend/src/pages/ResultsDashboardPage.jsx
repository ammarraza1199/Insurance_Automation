import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Shield, DollarSign, CheckCircle, XCircle, AlertCircle, Activity,
  Download, Loader, RefreshCw, TrendingUp, Search
} from 'lucide-react';

const BASE = 'http://localhost:8000';

const AUTH_CONFIG = {
  Approved:      { color: 'var(--secondary)', cls: 'success' },
  Denied:        { color: 'var(--danger)',     cls: 'failure' },
  'Manual Review': { color: 'var(--warning)', cls: 'warning' },
};

const RISK_CONFIG = {
  LOW:    { color: 'var(--secondary)', cls: 'success' },
  MEDIUM: { color: 'var(--warning)',   cls: 'warning' },
  HIGH:   { color: 'var(--danger)',    cls: 'failure' },
};

function MetricCard({ label, value, sub, color, icon: Icon }) {
  return (
    <div className="kpi-card fade-in" style={{ '--kpi-color': color, '--kpi-bg': `${color}18` }}>
      <div className="kpi-card-header">
        <div className="kpi-icon-wrap" style={{ background: `${color}18` }}>
          <Icon size={20} color={color} />
        </div>
      </div>
      <p className="kpi-label">{label}</p>
      <div className="kpi-value">{value ?? '—'}</div>
      {sub && <p className="kpi-sub">{sub}</p>}
    </div>
  );
}

export default function ResultsDashboardPage() {
  const [sessions,    setSessions]    = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [search,      setSearch]      = useState('');
  const [selected,    setSelected]    = useState(null);
  const [downloading, setDownloading] = useState(null);

  const fetchSessions = () => {
    setLoading(true);
    axios.get(`${BASE}/sessions`)
      .then(r => setSessions(r.data))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchSessions(); }, []);

  const filtered = sessions.filter(s => {
    const q = search.toLowerCase();
    return (
      s._id?.toLowerCase().includes(q) ||
      s.card_data?.member_name?.toLowerCase().includes(q) ||
      s.card_data?.payer_name?.toLowerCase().includes(q) ||
      s.card_data?.member_id?.toLowerCase().includes(q)
    );
  });

  const total     = sessions.length;
  const active    = sessions.filter(s => s.benefits?.coverage_status === 'Active').length;
  const approved  = sessions.filter(s => s.authorization?.authorization_status === 'Approved').length;
  const highRisk  = sessions.filter(s => s.denial_risk?.risk_level === 'HIGH').length;

  const downloadReport = async (sessionId) => {
    setDownloading(sessionId);
    try {
      const res = await axios.post(`${BASE}/generate-report`,
        new URLSearchParams({ session_id: sessionId }),
        { responseType: 'blob' }
      );
      const url  = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `insurance_report_${sessionId.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      alert('Report generation failed. Ensure reportlab is installed and Ollama is running.');
    } finally {
      setDownloading(null);
    }
  };

  const sel = selected ? sessions.find(s => s._id === selected) : null;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Results Dashboard</h1>
        <p>View all insurance verification sessions, eligibility results, and authorization decisions.</p>
      </div>

      {/* KPIs */}
      <div className="kpi-grid" style={{ marginBottom: 28 }}>
        <MetricCard label="Total Sessions"     value={total}    sub="All IV sessions"         color="var(--primary)"   icon={Activity}    />
        <MetricCard label="Active Coverage"    value={active}   sub={`${total > 0 ? Math.round(active/total*100) : 0}% of patients`} color="var(--secondary)" icon={CheckCircle} />
        <MetricCard label="Authorizations OK"  value={approved} sub="Approved by AI"          color="#a78bfa"          icon={Shield}       />
        <MetricCard label="High Denial Risk"   value={highRisk} sub="Need attention"          color="var(--danger)"    icon={AlertCircle}  />
      </div>

      <div className="content-grid-2" style={{ alignItems: 'start' }}>
        {/* ── Sessions Table ──── */}
        <div className="glass-panel" style={{ gridColumn: sel ? '1' : '1 / -1' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18, gap: 12, flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0 }}>Verification Sessions <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 400 }}>({filtered.length})</span></h2>
            <div style={{ display: 'flex', gap: 10, flex: 1, justifyContent: 'flex-end', maxWidth: 360 }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={15} style={{ position: 'absolute', left: 11, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                <input className="input-field" style={{ paddingLeft: 34, margin: 0 }}
                  placeholder="Search name, ID, payer…" value={search} onChange={e => setSearch(e.target.value)} />
              </div>
              <button className="btn btn-secondary" onClick={fetchSessions} style={{ padding: '10px 14px' }}>
                <RefreshCw size={16} />
              </button>
            </div>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-secondary)' }}>
              <Loader size={28} className="spinner" style={{ marginBottom: 12 }} />
              <p>Loading sessions…</p>
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.1)', borderRadius: 10 }}>
              No verification sessions found. Complete an Insurance Verification first.
            </div>
          ) : (
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Member Name</th>
                    <th>Payer</th>
                    <th>Coverage</th>
                    <th>Authorization</th>
                    <th>Risk</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(s => {
                    const authCfg = AUTH_CONFIG[s.authorization?.authorization_status] || null;
                    const riskCfg = RISK_CONFIG[s.denial_risk?.risk_level] || null;
                    const isActive = s.benefits?.coverage_status === 'Active';
                    return (
                      <tr key={s._id} style={{ cursor: 'pointer', background: selected === s._id ? 'rgba(99,102,241,0.08)' : '' }}
                        onClick={() => setSelected(selected === s._id ? null : s._id)}>
                        <td style={{ fontWeight: 500 }}>{s.card_data?.member_name || <span style={{ color: 'var(--text-secondary)' }}>Unknown</span>}</td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{s.card_data?.payer_name || '—'}</td>
                        <td><span className={`status-chip ${isActive ? 'success' : 'failure'}`}>{isActive ? <CheckCircle size={11} /> : <XCircle size={11} />} {s.benefits?.coverage_status || '—'}</span></td>
                        <td>{authCfg
                          ? <span className={`status-chip ${authCfg.cls}`}>{s.authorization.authorization_status}</span>
                          : <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>—</span>}</td>
                        <td>{riskCfg
                          ? <span className={`status-chip ${riskCfg.cls}`}>{s.denial_risk.risk_level}</span>
                          : <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>—</span>}</td>
                        <td onClick={e => e.stopPropagation()}>
                          <button className="btn btn-primary"
                            style={{ padding: '6px 14px', fontSize: '0.79rem' }}
                            onClick={() => downloadReport(s._id)}
                            disabled={downloading === s._id}>
                            {downloading === s._id
                              ? <Loader size={13} className="spinner" />
                              : <><Download size={13} /> Report</>}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ── Detail Panel ──── */}
        {sel && (
          <div className="glass-panel fade-in" style={{ position: 'sticky', top: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <h2 style={{ margin: 0 }}>Session Detail</h2>
              <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => setSelected(null)}>✕ Close</button>
            </div>

            {/* Coverage */}
            {sel.benefits && (
              <div style={{ marginBottom: 18 }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 8 }}>Benefits Summary</p>
                <div className="iv-field-grid">
                  {[
                    ['Coverage',         sel.benefits.coverage_status],
                    ['Plan Type',        sel.benefits.plan_type],
                    ['Copay',            `₹${(sel.benefits.copay||0).toLocaleString()}`],
                    ['Deductible Left',  `₹${(sel.benefits.deductible_remaining||0).toLocaleString()}`],
                    ['Coinsurance',      `${sel.benefits.coinsurance||0}%`],
                    ['OOP Max',          `₹${(sel.benefits.out_of_pocket_max||0).toLocaleString()}`],
                  ].map(([k, v]) => (
                    <div key={k} className="iv-field-item">
                      <div className="iv-field-label">{k}</div>
                      <div className="iv-field-value">{v || '—'}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Financial */}
            {sel.financial_estimation && (
              <div style={{ marginBottom: 18 }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 8 }}>Financial Estimation</p>
                <div className="iv-finance-summary">
                  <div className="iv-finance-card patient">
                    <div className="iv-finance-label">Patient Pays</div>
                    <div className="iv-finance-amount">₹{(sel.financial_estimation.patient_pay||0).toLocaleString()}</div>
                  </div>
                  <div className="iv-finance-card insurance">
                    <div className="iv-finance-label">Insurance Pays</div>
                    <div className="iv-finance-amount">₹{(sel.financial_estimation.insurance_pay||0).toLocaleString()}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Authorization */}
            {sel.authorization && (() => {
              const ac = AUTH_CONFIG[sel.authorization.authorization_status] || {};
              return (
                <div style={{ marginBottom: 18 }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 8 }}>Authorization</p>
                  <div style={{ padding: '12px 14px', background: `${ac.color}15`, borderRadius: 8, border: `1px solid ${ac.color}30` }}>
                    <div style={{ fontWeight: 700, color: ac.color, marginBottom: 6 }}>{sel.authorization.authorization_status}</div>
                    <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{sel.authorization.reason}</div>
                    <div className="progress-bar-track" style={{ marginTop: 10 }}>
                      <div className="progress-bar-fill" style={{ width: `${Math.round((sel.authorization.confidence_score||0)*100)}%`, background: ac.color }} />
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                      Confidence: {Math.round((sel.authorization.confidence_score||0)*100)}%
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Denial Risk */}
            {sel.denial_risk && (() => {
              const rc = RISK_CONFIG[sel.denial_risk.risk_level] || {};
              return (
                <div style={{ marginBottom: 18 }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 8 }}>Denial Risk</p>
                  <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 800, color: rc.color }}>{sel.denial_risk.risk_score}</div>
                    <div>
                      <span className={`status-chip ${rc.cls}`}>{sel.denial_risk.risk_level} RISK</span>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 4 }}>{sel.denial_risk.summary}</p>
                    </div>
                  </div>
                </div>
              );
            })()}

            <button className="btn btn-primary" style={{ width: '100%' }}
              onClick={() => downloadReport(sel._id)} disabled={downloading === sel._id}>
              {downloading === sel._id ? <Loader size={16} className="spinner" /> : <Download size={16} />}
              Download Full Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
