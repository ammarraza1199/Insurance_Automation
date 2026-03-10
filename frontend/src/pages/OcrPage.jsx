import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, CheckCircle, AlertCircle, Loader, ScanLine, Tag } from 'lucide-react';

const BASE = 'http://localhost:8000';

export default function OcrPage() {
    const [file, setFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState(null);

    useEffect(() => {
        axios.get(`${BASE}/stats`).then(r => setStats(r.data)).catch(() => { });
    }, [result]);   // refresh after each upload

    const handleDrop = (e) => {
        e.preventDefault(); setIsDragging(false);
        if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
    };

    const processFile = async () => {
        if (!file) return;
        setIsUploading(true); setError(null); setResult(null);
        const fd = new FormData();
        fd.append('file', file);
        try {
            const res = await axios.post(`${BASE}/upload`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
            setResult(res.data);
        } catch {
            setError('OCR extraction failed. Make sure the FastAPI backend is running and the file is a valid image or PDF.');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <h1>OCR Processing</h1>
                <p>Upload medical documents to extract patient demographics and ICD-10 diagnosis codes automatically.</p>
            </div>

            {/* Mini KPIs */}
            {stats && (
                <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 28 }}>
                    {[
                        { label: 'Total Uploads', value: stats.total_documents, color: 'var(--primary)', icon: ScanLine },
                        { label: 'OCR Successful', value: stats.ocr_success, color: 'var(--secondary)', icon: CheckCircle },
                        { label: 'ICD-10 Mapped', value: stats.icd_mapped, color: 'var(--warning)', icon: Tag },
                    ].map(({ label, value, color, icon: Icon }) => (
                        <div className="kpi-card" key={label} style={{ '--kpi-color': color, '--kpi-bg': `${color}18` }}>
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
            )}

            <div className="content-grid-2">
                {/* Upload Panel */}
                <div className="glass-panel">
                    <h2 style={{ marginBottom: 8 }}>Upload Document</h2>
                    <p style={{ marginBottom: 24 }}>Accepts PNG, JPG, JPEG, or PDF.</p>

                    {!file ? (
                        <label
                            className={`upload-dropzone ${isDragging ? 'active' : ''}`}
                            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                            onDragLeave={() => setIsDragging(false)}
                            onDrop={handleDrop}
                        >
                            <input type="file" style={{ display: 'none' }} onChange={e => e.target.files?.[0] && setFile(e.target.files[0])} accept=".png,.jpg,.jpeg,.pdf" />
                            <UploadCloud size={48} className="upload-icon" />
                            <div>
                                <h3 style={{ marginBottom: 8 }}>Click or drag file here</h3>
                                <p>Supports single document upload. Max 20 MB.</p>
                            </div>
                        </label>
                    ) : (
                        <div style={{ padding: 20, background: 'rgba(0,0,0,0.2)', borderRadius: 10, border: '1px solid var(--border)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 18 }}>
                                <FileText size={30} color="var(--primary)" />
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 500 }}>{file.name}</div>
                                    <p style={{ fontSize: '0.82rem' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                                <button className="btn btn-secondary" onClick={() => { setFile(null); setResult(null); setError(null); }}>Remove</button>
                            </div>
                            <button className="btn btn-primary" style={{ width: '100%' }} onClick={processFile} disabled={isUploading}>
                                {isUploading ? <><Loader size={16} className="spinner" /> Processing…</> : 'Run OCR Extraction'}
                            </button>
                        </div>
                    )}

                    {error && (
                        <div style={{ marginTop: 18, padding: 14, background: 'rgba(239,68,68,0.08)', color: 'var(--danger)', borderRadius: 8, display: 'flex', gap: 10, fontSize: '0.88rem' }}>
                            <AlertCircle size={18} style={{ flexShrink: 0 }} /> {error}
                        </div>
                    )}
                </div>

                {/* Result Panel */}
                <div className="glass-panel">
                    <h2 style={{ marginBottom: 8 }}>Extraction Results</h2>
                    <p style={{ marginBottom: 24 }}>Patient demographics and ICD-10 codes appear here after processing.</p>

                    {!result ? (
                        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.1)', borderRadius: 10 }}>
                            Upload a document to see extraction results.
                        </div>
                    ) : (
                        <div className="fade-in">
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--secondary)', marginBottom: 18, fontWeight: 600 }}>
                                <CheckCircle size={18} /> Extraction Successful
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                                {[
                                    { label: 'Patient Name', value: result.data.patient_info.name },
                                    { label: 'Date of Birth', value: result.data.patient_info.dob },
                                ].map(({ label, value }) => (
                                    <div key={label} style={{ background: 'rgba(0,0,0,0.2)', padding: 14, borderRadius: 8 }}>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 6 }}>{label}</div>
                                        <div style={{ fontWeight: 500 }}>{value}</div>
                                    </div>
                                ))}
                            </div>

                            <div style={{ background: 'rgba(0,0,0,0.2)', padding: 14, borderRadius: 8 }}>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 10 }}>ICD-10 Codes</div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                    {result.data.icd10_codes.length > 0
                                        ? result.data.icd10_codes.map(c => <span key={c} className="badge">{c}</span>)
                                        : <span style={{ color: 'var(--text-secondary)', fontSize: '0.87rem' }}>No ICD-10 codes detected in document.</span>}
                                </div>
                            </div>

                            <hr className="divider" />
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                Record ID: <code style={{ fontFamily: 'monospace', color: 'var(--primary)' }}>{result.record_id}</code>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
