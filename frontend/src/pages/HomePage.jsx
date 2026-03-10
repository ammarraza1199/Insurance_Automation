import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ScanLine, CheckCircle, XCircle, Tag, Activity, TrendingUp, Loader } from 'lucide-react';

const BASE = 'http://localhost:8000';

function KpiCard({ label, value, sub, icon: Icon, color = 'var(--primary)', bg = 'rgba(99,102,241,0.1)', badge, badgeVariant }) {
    return (
        <div className="kpi-card fade-in" style={{ '--kpi-color': color, '--kpi-bg': bg }}>
            <div className="kpi-card-header">
                <div className="kpi-icon-wrap" style={{ background: bg }}>
                    <Icon size={20} color={color} />
                </div>
                {badge !== undefined && (
                    <span className={`kpi-badge ${badgeVariant || 'blue'}`}>{badge}</span>
                )}
            </div>
            <p className="kpi-label">{label}</p>
            <div className="kpi-value">{value}</div>
            {sub && <p className="kpi-sub">{sub}</p>}
        </div>
    );
}

export default function HomePage() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axios.get(`${BASE}/stats`)
            .then(r => setStats(r.data))
            .catch(() => setStats(null))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="fade-in">
            <div className="page-header">
                <h1>Overview Dashboard</h1>
                <p>Real-time performance indicators for all pipeline stages.</p>
            </div>

            {loading ? (
                <div style={{ display: 'flex', gap: 12, alignItems: 'center', color: 'var(--text-secondary)' }}>
                    <Loader size={20} className="spinner" /> Loading live stats…
                </div>
            ) : !stats ? (
                <div className="glass-panel" style={{ color: 'var(--danger)' }}>
                    ⚠ Could not reach backend. Make sure FastAPI is running on port 8000.
                </div>
            ) : (
                <>
                    {/* KPI ROW */}
                    <div className="kpi-grid">
                        <KpiCard
                            label="Total Documents"
                            value={stats.total_documents}
                            sub="All uploaded files"
                            icon={Activity}
                            color="var(--primary)"
                            bg="rgba(99,102,241,0.1)"
                        />
                        <KpiCard
                            label="OCR Successful"
                            value={stats.ocr_success}
                            sub={`${stats.success_rate}% success rate`}
                            icon={CheckCircle}
                            color="var(--secondary)"
                            bg="rgba(16,185,129,0.1)"
                            badge={`${stats.success_rate}%`}
                            badgeVariant="green"
                        />
                        <KpiCard
                            label="OCR Failed"
                            value={stats.ocr_failed}
                            sub="Documents with errors"
                            icon={XCircle}
                            color="var(--danger)"
                            bg="rgba(239,68,68,0.1)"
                            badge={stats.ocr_failed > 0 ? 'Needs attention' : 'All clear'}
                            badgeVariant={stats.ocr_failed > 0 ? 'red' : 'green'}
                        />
                        <KpiCard
                            label="ICD-10 Mapped"
                            value={stats.icd_mapped}
                            sub={`${stats.mapping_rate}% mapping rate`}
                            icon={Tag}
                            color="var(--warning)"
                            bg="rgba(245,158,11,0.1)"
                            badge={`${stats.mapping_rate}%`}
                            badgeVariant="amber"
                        />
                        <KpiCard
                            label="CPT AI Queries"
                            value={stats.cpt_queries}
                            sub="Total LLM lookups"
                            icon={Activity}
                            color="#a78bfa"
                            bg="rgba(167,139,250,0.1)"
                        />
                        <KpiCard
                            label="Patients with CPT"
                            value={stats.cpt_analyzed}
                            sub="Records fully analyzed"
                            icon={TrendingUp}
                            color="var(--secondary)"
                            bg="rgba(16,185,129,0.1)"
                        />
                    </div>

                    {/* Progress bars */}
                    <div className="glass-panel" style={{ marginBottom: 24 }}>
                        <h3 style={{ marginBottom: 20 }}>Pipeline Performance</h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                            {[
                                { label: 'OCR Success Rate', value: stats.success_rate, color: 'var(--secondary)' },
                                { label: 'ICD-10 Mapping Rate', value: stats.mapping_rate, color: 'var(--warning)' },
                                { label: 'CPT Coverage Rate', value: stats.total_documents > 0 ? Math.round(stats.cpt_analyzed / stats.total_documents * 100) : 0, color: 'var(--primary)' },
                            ].map(({ label, value, color }) => (
                                <div key={label}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                        <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>{label}</span>
                                        <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>{value}%</span>
                                    </div>
                                    <div className="progress-bar-track">
                                        <div className="progress-bar-fill" style={{ width: `${value}%`, background: color }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
