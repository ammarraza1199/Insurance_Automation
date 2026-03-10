import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Stethoscope, Activity, RefreshCw, ListOrdered, Loader } from 'lucide-react';

const BASE = 'http://localhost:8000';

export default function CptPage() {
    const [cptCode, setCptCode] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);

    const fetchLogs = () => {
        axios.get(`${BASE}/cpt-logs`).then(r => setLogs(r.data)).catch(() => { });
        axios.get(`${BASE}/stats`).then(r => setStats(r.data)).catch(() => { });
    };

    useEffect(() => { fetchLogs(); }, []);

    const handleQuery = async () => {
        if (!cptCode.trim()) return;
        setLoading(true); setResult(null);
        try {
            const res = await axios.post(`${BASE}/cpt-description?cpt_code=${encodeURIComponent(cptCode)}`);
            setResult(res.data);
            fetchLogs();
        } catch {
            setResult({ error: true, description: 'Failed to get AI description. Make sure Ollama is running with a model loaded (e.g. ollama run llama3).' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <h1>AI CPT Lookup</h1>
                <p>Query the local open-source LLM to get medical descriptions for Procedural Terminology codes.</p>
            </div>

            {/* KPIs */}
            {stats && (
                <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 28 }}>
                    {[
                        { label: 'Total CPT Queries', value: stats.cpt_queries, color: 'var(--primary)', icon: Activity },
                        { label: 'Patients with CPT', value: stats.cpt_analyzed, color: 'var(--secondary)', icon: Stethoscope },
                        { label: 'Total Patients', value: stats.total_documents, color: '#a78bfa', icon: ListOrdered },
                    ].map(({ label, value, color, icon: Icon }) => (
                        <div className="kpi-card" key={label} style={{ '--kpi-color': color }}>
                            <div className="kpi-card-header">
                                <div className="kpi-icon-wrap" style={{ background: `${color}18` }}>
                                    <Icon size={18} color={color} />
                                </div>
                            </div>
                            <p className="kpi-label">{label}</p>
                            <div className="kpi-value">{value ?? '—'}</div>
                        </div>
                    ))}
                </div>
            )}

            <div className="content-grid-2">
                {/* Query Panel */}
                <div className="glass-panel">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
                        <div style={{ background: 'var(--primary)', padding: 8, borderRadius: 8, display: 'flex' }}>
                            <Stethoscope color="white" size={18} />
                        </div>
                        <h2 style={{ margin: 0 }}>Enter CPT Code</h2>
                    </div>

                    <div className="input-group">
                        <label className="input-label">CPT Code</label>
                        <input
                            className="input-field"
                            placeholder="e.g. 99213, 71046, 27447…"
                            value={cptCode}
                            onChange={e => setCptCode(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleQuery()}
                        />
                    </div>

                    <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleQuery} disabled={loading || !cptCode.trim()}>
                        {loading ? <><Loader size={16} className="spinner" /> Querying AI Model…</> : 'Get AI Description'}
                    </button>

                    {result && (
                        <div style={{ marginTop: 20 }}>
                            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 10 }}>
                                AI Response for <strong style={{ color: 'var(--primary)' }}>{result.cpt_code}</strong>
                            </div>
                            <div className="llm-output-box" style={{ color: result.error ? 'var(--danger)' : 'var(--text-primary)' }}>
                                {result.description}
                            </div>
                        </div>
                    )}
                </div>

                {/* Query History */}
                <div className="glass-panel">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                        <h2 style={{ margin: 0 }}>Query History</h2>
                        <button className="btn btn-secondary" onClick={fetchLogs} style={{ padding: '6px 12px', fontSize: '0.82rem' }}>
                            <RefreshCw size={14} /> Refresh
                        </button>
                    </div>

                    {logs.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.1)', borderRadius: 8 }}>
                            No CPT lookups recorded yet.
                        </div>
                    ) : (
                        <div className="data-table-wrap">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>CPT Code</th>
                                        <th>AI Description (excerpt)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.slice().reverse().map(log => (
                                        <tr key={log._id}>
                                            <td><span className="badge blue">{log.cpt_code}</span></td>
                                            <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                                {log.description ? log.description.slice(0, 90) + '…' : '—'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
