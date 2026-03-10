import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, Search, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

const BASE = 'http://localhost:8000';

export default function PatientsPage() {
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    const fetchRecords = () => {
        setLoading(true);
        axios.get(`${BASE}/sessions`)
            .then(r => setRecords(r.data))
            .catch(() => setRecords([]))
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchRecords(); }, []);

    const filtered = records.filter(rec => {
        const q = search.toLowerCase();
        return (
            rec.patient_info?.name?.toLowerCase().includes(q) ||
            rec._id?.toLowerCase().includes(q) ||
            rec.icd10_codes?.some(c => c.toLowerCase().includes(q)) ||
            rec.cpt_codes?.some(c => c.code?.toLowerCase().includes(q)) ||
            rec.filename?.toLowerCase().includes(q)
        );
    });

    const total    = records.length;
    const active   = records.filter(r => r.benefits?.coverage_status === 'Active').length;
    const withAuth = records.filter(r => r.authorization?.authorization_status).length;
    const highRisk = records.filter(r => r.denial_risk?.risk_level === 'HIGH').length;

    return (
        <div className="fade-in">
            <div className="page-header">
                <h1>Patient Database</h1>
                <p>Browse, search and filter all processed patient records by Name, ICD-10 code, or CPT code.</p>
            </div>

            {/* KPI Row */}
            <div className="kpi-grid" style={{ marginBottom: 28 }}>
                {[
                    { label: 'Total Patients',  value: total,    color: 'var(--primary)',   icon: Users },
                    { label: 'Active Coverage',  value: active,   color: 'var(--secondary)', icon: CheckCircle },
                    { label: 'Authorized',        value: withAuth, color: 'var(--warning)',   icon: CheckCircle },
                    { label: 'High Denial Risk',  value: highRisk, color: '#f87171',          icon: XCircle },
                ].map(({ label, value, color, icon: Icon }) => (
                    <div className="kpi-card" key={label} style={{ '--kpi-color': color }}>
                        <div className="kpi-card-header">
                            <div className="kpi-icon-wrap" style={{ background: `${color}18` }}>
                                <Icon size={18} color={color} />
                            </div>
                        </div>
                        <p className="kpi-label">{label}</p>
                        <div className="kpi-value">{value}</div>
                    </div>
                ))}
            </div>

            <div className="glass-panel">
                {/* Toolbar */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                    <h2 style={{ margin: 0 }}>All Records <span style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 400 }}>({filtered.length} shown)</span></h2>
                    <div style={{ display: 'flex', gap: 10, flex: 1, justifyContent: 'flex-end', alignItems: 'center', maxWidth: 460 }}>
                        <div style={{ position: 'relative', flex: 1 }}>
                            <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                            <input
                                className="input-field"
                                style={{ paddingLeft: 36, margin: 0 }}
                                placeholder="Search name, ICD, CPT, file…"
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                            />
                        </div>
                        <button className="btn btn-secondary" onClick={fetchRecords} style={{ padding: '10px 14px' }}>
                            <RefreshCw size={16} />
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-secondary)' }}>
                        <RefreshCw size={28} className="spinner" style={{ marginBottom: 12 }} />
                <p>Loading patient records…</p>
                    </div>
                ) : filtered.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.1)', borderRadius: 10 }}>
                        No records match your search.
                    </div>
                ) : (
                    <div className="data-table-wrap">
                        <table className="data-table">
                            <thead>
                                <tr>
                                 <th>Patient Name</th>
                                    <th>Payer</th>
                                    <th>Coverage</th>
                                    <th>Authorization</th>
                                    <th>Risk</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map(rec => (
                                    <tr key={rec._id}>
                                        <td style={{ fontWeight: 500 }}>{rec.card_data?.member_name || <span style={{ color: 'var(--text-secondary)' }}>Unknown</span>}</td>
                                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.87rem' }}>{rec.card_data?.payer_name || '—'}</td>
                                        <td>
                                            <span className={`status-chip ${rec.benefits?.coverage_status === 'Active' ? 'success' : 'failure'}`}>
                                                {rec.benefits?.coverage_status === 'Active' ? <CheckCircle size={12} /> : <XCircle size={12} />}
                                                {rec.benefits?.coverage_status || 'Unknown'}
                                            </span>
                                        </td>
                                        <td style={{ fontSize: '0.87rem' }}>{rec.authorization?.authorization_status || '—'}</td>
                                        <td style={{ fontSize: '0.87rem' }}>
                                            <span className={`status-chip ${rec.denial_risk?.risk_level === 'HIGH' ? 'failure' : rec.denial_risk?.risk_level === 'MEDIUM' ? 'warning' : 'success'}`}>
                                                {rec.denial_risk?.risk_level || '—'}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
