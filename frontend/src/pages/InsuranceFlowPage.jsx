import React, { useState, useRef } from 'react';
import axios from 'axios';
import {
  UploadCloud, FileText, CheckCircle, XCircle, Loader, ChevronRight,
  User, CreditCard, Shield, DollarSign, AlertTriangle, ArrowRight,
  Zap, RefreshCw
} from 'lucide-react';

const BASE = 'http://localhost:8000';

// ── Step metadata ─────────────────────────────────────────────────────────────
const STEPS = [
  { id: 1, label: 'Upload Card',        icon: UploadCloud,  key: 'upload'   },
  { id: 2, label: 'OCR Extraction',     icon: FileText,     key: 'ocr'      },
  { id: 3, label: 'EDI 270 Request',    icon: Zap,          key: 'edi270'   },
  { id: 4, label: '271 Response',       icon: Shield,       key: 'edi271'   },
  { id: 5, label: 'Benefits Analysis',  icon: CheckCircle,  key: 'benefits' },
  { id: 6, label: 'Financial Estimate', icon: DollarSign,   key: 'finance'  },
  { id: 7, label: 'Denial Risk',        icon: AlertTriangle,key: 'risk'     },
  { id: 8, label: 'AI Authorization',   icon: Shield,       key: 'auth'     },
];

// ── Small helpers ─────────────────────────────────────────────────────────────
function StepIndicator({ steps, activeStep, completedSteps }) {
  return (
    <div className="iv-step-bar">
      {steps.map((s, i) => {
        const done   = completedSteps.has(s.key);
        const active = activeStep === s.key;
        const Icon   = s.icon;
        return (
          <React.Fragment key={s.key}>
            <div className={`iv-step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
              <div className="iv-step-circle">
                {done ? <CheckCircle size={16} /> : <Icon size={16} />}
              </div>
              <span className="iv-step-label">{s.label}</span>
            </div>
            {i < steps.length - 1 && (
              <div className={`iv-step-connector ${done ? 'done' : ''}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function FieldGrid({ fields }) {
  return (
    <div className="iv-field-grid">
      {Object.entries(fields).map(([key, val]) => (
        <div key={key} className="iv-field-item">
          <div className="iv-field-label">{key.replace(/_/g, ' ')}</div>
          <div className="iv-field-value">{val || '—'}</div>
        </div>
      ))}
    </div>
  );
}

function StatusPill({ active }) {
  return (
    <span className={`status-chip ${active ? 'success' : 'failure'}`}>
      {active ? <><CheckCircle size={12} /> Active</> : <><XCircle size={12} /> Inactive</>}
    </span>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function InsuranceFlowPage() {
  const [sessionId,  setSessionId]  = useState(null);
  const [file,       setFile]       = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [activeStep, setActiveStep] = useState('upload');
  const [completed,  setCompleted]  = useState(new Set());
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);

  // Data state
  const [cardData,   setCardData]   = useState(null);
  const [edi270,     setEdi270]     = useState(null);
  const [edi271,     setEdi271]     = useState(null);
  const [benefits,   setBenefits]   = useState(null);
  const [procedureCost, setProcedureCost] = useState('');
  const [estimation, setEstimation] = useState(null);
  const [denialRisk,  setDenialRisk]  = useState(null);
  const [authResult,  setAuthResult]  = useState(null);
  const [cptCode,     setCptCode]     = useState('');
  const [diagCodes,   setDiagCodes]   = useState('');
  const [medSummary,  setMedSummary]  = useState('');

  const fileRef = useRef();

  const mark = (key) => setCompleted(prev => new Set([...prev, key]));
  const err  = (msg) => { setError(msg); setLoading(false); };

  const handleDrop = (e) => {
    e.preventDefault(); setIsDragging(false);
    if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
  };

  // ── Step 1: Upload Card ────────────────────────────────────────────────────
  const uploadCard = async () => {
    if (!file) return;
    setLoading(true); setError(null);
    setActiveStep('upload');
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await axios.post(`${BASE}/upload-card`, fd);
      setSessionId(res.data.session_id);
      mark('upload');
      setActiveStep('ocr');
      setLoading(false);
    } catch (e) { err('Card upload failed. Is the backend running?'); }
  };

  // ── Step 2: OCR Extraction ────────────────────────────────────────────────
  const runOcr = async () => {
    if (!sessionId) return;
    setLoading(true); setError(null);
    const fd = new FormData(); fd.append('session_id', sessionId);
    try {
      const res = await axios.post(`${BASE}/extract-card-data`, fd);
      setCardData(res.data.card_data);
      mark('ocr');
      setActiveStep('edi270');
      setLoading(false);
    } catch (e) { err('OCR extraction failed.'); }
  };

  // ── Step 3: Generate EDI 270 ──────────────────────────────────────────────
  const runEdi270 = async () => {
    setLoading(true); setError(null);
    const fd = new FormData(); fd.append('session_id', sessionId);
    try {
      const res = await axios.post(`${BASE}/generate-270`, fd);
      setEdi270(res.data.edi_270);
      mark('edi270');
      setActiveStep('edi271');
      setLoading(false);
    } catch (e) { err('EDI 270 generation failed.'); }
  };

  // ── Step 4: Simulate EDI 271 ──────────────────────────────────────────────
  const runEdi271 = async () => {
    setLoading(true); setError(null);
    const fd = new FormData(); fd.append('session_id', sessionId);
    try {
      const res = await axios.post(`${BASE}/simulate-271`, fd);
      setEdi271(res.data.edi_response);
      mark('edi271');
      setActiveStep('benefits');
      setLoading(false);
    } catch (e) { err('EDI 271 simulation failed.'); }
  };

  // ── Step 5: Benefits Analysis ─────────────────────────────────────────────
  const runBenefits = async () => {
    setLoading(true); setError(null);
    const fd = new FormData(); fd.append('session_id', sessionId);
    try {
      const res = await axios.post(`${BASE}/benefits-analysis`, fd);
      setBenefits(res.data.benefits);
      mark('benefits');
      setActiveStep('finance');
      setLoading(false);
    } catch (e) { err('Benefits analysis failed.'); }
  };

  // ── Step 6: Financial Estimation ──────────────────────────────────────────
  const runEstimation = async () => {
    const cost = parseFloat(procedureCost);
    if (!cost || isNaN(cost)) return err('Please enter a valid procedure cost.');
    setLoading(true); setError(null);
    try {
      const res = await axios.post(`${BASE}/estimate-cost`, { session_id: sessionId, procedure_cost: cost });
      setEstimation(res.data.financial_estimation);
      mark('finance');
      setActiveStep('risk');
      setLoading(false);
      // Auto-trigger denial risk immediately after financial estimation
      await runDenialRiskAuto(sessionId);
    } catch (e) { err('Financial estimation failed.'); }
  };

  // ── Step 7: Denial Risk (auto-runs after finance) ──────────────────────────
  const runDenialRiskAuto = async (sid) => {
    try {
      const res = await axios.get(`${BASE}/denial-risk/${sid}`);
      setDenialRisk(res.data.denial_risk);
      mark('risk');
      setActiveStep('auth');
    } catch (e) {
      console.warn('Denial risk auto-run failed:', e);
    }
  };

  const runDenialRisk = async () => {
    if (!sessionId) return;
    setLoading(true); setError(null);
    try {
      const res = await axios.get(`${BASE}/denial-risk/${sessionId}`);
      setDenialRisk(res.data.denial_risk);
      mark('risk');
      setActiveStep('auth');
      setLoading(false);
    } catch (e) { err('Denial risk scoring failed.'); }
  };

  // ── Step 8: AI Authorization ───────────────────────────────────────────────
  const runAuthorization = async () => {
    if (!sessionId || !cptCode) return err('Please enter a CPT code.');
    setLoading(true); setError(null);
    try {
      const res = await axios.post(`${BASE}/authorization/check`, {
        session_id:      sessionId,
        cpt_code:        cptCode,
        diagnosis_codes: diagCodes ? diagCodes.split(',').map(s => s.trim()) : [],
        medical_summary: medSummary,
      });
      setAuthResult(res.data);
      mark('auth');
      setActiveStep('done');
      setLoading(false);
    } catch (e) { err('Authorization check failed.'); }
  };

  // ── Reset ─────────────────────────────────────────────────────────────────
  const reset = () => {
    setSessionId(null); setFile(null); setActiveStep('upload');
    setCompleted(new Set()); setCardData(null); setEdi270(null);
    setEdi271(null); setBenefits(null); setEstimation(null);
    setDenialRisk(null); setAuthResult(null);
    setCptCode(''); setDiagCodes(''); setMedSummary('');
    setProcedureCost(''); setError(null);
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Insurance Verification</h1>
        <p>Upload an insurance card and walk through the complete eligibility verification pipeline.</p>
      </div>

      {/* Step bar */}
      <StepIndicator steps={STEPS} activeStep={activeStep} completedSteps={completed} />

      {error && (
        <div className="iv-error-banner">
          <AlertTriangle size={16} /> {error}
          <button onClick={() => setError(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}>✕</button>
        </div>
      )}

      <div className="iv-panels">

        {/* ── PANEL 1: Upload ───────────────────────────────────────────── */}
        <div className={`glass-panel iv-panel ${completed.has('upload') ? 'panel-done' : ''}`}>
          <div className="iv-panel-header">
            <div className="iv-panel-num">1</div>
            <h2>Upload Insurance Card</h2>
            {completed.has('upload') && <CheckCircle size={18} color="var(--secondary)" />}
          </div>

          {!completed.has('upload') ? (
            <>
              {!file ? (
                <label
                  className={`upload-dropzone ${isDragging ? 'active' : ''}`}
                  onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                >
                  <input type="file" style={{ display: 'none' }} ref={fileRef}
                    accept=".png,.jpg,.jpeg,.gif,.bmp,.webp"
                    onChange={e => e.target.files?.[0] && setFile(e.target.files[0])} />
                  <UploadCloud size={44} className="upload-icon" />
                  <h3>Drag & Drop Insurance Card Image</h3>
                  <p>PNG, JPG, JPEG, WEBP — front or back of card</p>
                </label>
              ) : (
                <div className="iv-file-preview">
                  <FileText size={28} color="var(--primary)" />
                  <div className="iv-file-info">
                    <strong>{file.name}</strong>
                    <span>{(file.size / 1024).toFixed(1)} KB</span>
                  </div>
                  <button className="btn btn-secondary" onClick={() => setFile(null)}>Remove</button>
                </div>
              )}
              <button className="btn btn-primary iv-action-btn" onClick={uploadCard} disabled={!file || loading}>
                {loading && activeStep === 'upload' ? <><Loader size={16} className="spinner" /> Uploading…</> : <>Upload Card <ArrowRight size={16} /></>}
              </button>
            </>
          ) : (
            <div className="iv-done-badge"><CheckCircle size={14} /> Card uploaded — Session ID: <code>{sessionId?.slice(0, 12)}…</code></div>
          )}
        </div>

        {/* ── PANEL 2: OCR ─────────────────────────────────────────────── */}
        <div className={`glass-panel iv-panel ${!completed.has('upload') ? 'panel-locked' : ''} ${completed.has('ocr') ? 'panel-done' : ''}`}>
          <div className="iv-panel-header">
            <div className="iv-panel-num">2</div>
            <h2>OCR Extraction</h2>
            {completed.has('ocr') && <CheckCircle size={18} color="var(--secondary)" />}
          </div>

          {completed.has('ocr') && cardData ? (
            <div>
              <FieldGrid fields={{
                'Member Name':   cardData.member_name,
                'Member ID':     cardData.member_id,
                'Group Number':  cardData.group_number,
                'Policy Number': cardData.policy_number,
                'Date of Birth': cardData.dob,
                'Payer / Insurer': cardData.payer_name,
                'Valid Through': cardData.valid_thru,
              }} />
            </div>
          ) : activeStep === 'ocr' || (completed.has('upload') && !completed.has('ocr')) ? (
            <>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>Click to extract insurance data from the card image using AI-powered OCR.</p>
              <button className="btn btn-primary iv-action-btn" onClick={runOcr} disabled={loading}>
                {loading && activeStep === 'ocr' ? <><Loader size={16} className="spinner" /> Extracting…</> : <>Run OCR Extraction <ArrowRight size={16} /></>}
              </button>
            </>
          ) : (
            <p className="iv-locked-msg">Complete previous step first.</p>
          )}
        </div>

        {/* ── PANEL 3: EDI 270 ──────────────────────────────────────────── */}
        <div className={`glass-panel iv-panel ${!completed.has('ocr') ? 'panel-locked' : ''} ${completed.has('edi270') ? 'panel-done' : ''}`}>
          <div className="iv-panel-header">
            <div className="iv-panel-num">3</div>
            <h2>EDI 270 Request</h2>
            {completed.has('edi270') && <CheckCircle size={18} color="var(--secondary)" />}
          </div>
          {completed.has('edi270') && edi270 ? (
            <pre className="iv-edi-box">{edi270.slice(0, 400)}…</pre>
          ) : activeStep === 'edi270' || (completed.has('ocr') && !completed.has('edi270')) ? (
            <>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>Generate ANSI X12 EDI 270 eligibility inquiry for this patient.</p>
              <button className="btn btn-primary iv-action-btn" onClick={runEdi270} disabled={loading}>
                {loading && activeStep === 'edi270' ? <><Loader size={16} className="spinner" /> Generating…</> : <>Generate EDI 270 <Zap size={16} /></>}
              </button>
            </>
          ) : (
            <p className="iv-locked-msg">Complete OCR step first.</p>
          )}
        </div>

        {/* ── PANEL 4: EDI 271 ──────────────────────────────────────────── */}
        <div className={`glass-panel iv-panel ${!completed.has('edi270') ? 'panel-locked' : ''} ${completed.has('edi271') ? 'panel-done' : ''}`}>
          <div className="iv-panel-header">
            <div className="iv-panel-num">4</div>
            <h2>Insurance Response (271)</h2>
            {completed.has('edi271') && <CheckCircle size={18} color="var(--secondary)" />}
          </div>
          {completed.has('edi271') && edi271 ? (
            <div>
              <div className="iv-coverage-badge" style={{ marginBottom: 12 }}>
                <StatusPill active={edi271.coverage_active} />
                <span style={{ marginLeft: 10, color: 'var(--text-secondary)', fontSize: '0.88rem' }}>{edi271.status_label}</span>
              </div>
              <FieldGrid fields={{
                'Copay':                 `₹${(edi271.copay || 0).toLocaleString()}`,
                'Deductible Total':      `₹${(edi271.deductible_total || 0).toLocaleString()}`,
                'Deductible Remaining':  `₹${(edi271.deductible_remaining || 0).toLocaleString()}`,
                'Coinsurance':           `${edi271.coinsurance || 0}%`,
                'Out-of-Pocket Max':     `₹${(edi271.out_of_pocket_max || 0).toLocaleString()}`,
              }} />
            </div>
          ) : activeStep === 'edi271' || (completed.has('edi270') && !completed.has('edi271')) ? (
            <>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>Simulate payer eligibility response (EDI 271) with benefit details.</p>
              <button className="btn btn-primary iv-action-btn" onClick={runEdi271} disabled={loading}>
                {loading && activeStep === 'edi271' ? <><Loader size={16} className="spinner" /> Simulating…</> : <>Simulate Payer Response <Shield size={16} /></>}
              </button>
            </>
          ) : (
            <p className="iv-locked-msg">Generate EDI 270 first.</p>
          )}
        </div>

        {/* ── PANEL 5: Benefits ──────────────────────────────────────────── */}
        <div className={`glass-panel iv-panel ${!completed.has('edi271') ? 'panel-locked' : ''} ${completed.has('benefits') ? 'panel-done' : ''}`}>
          <div className="iv-panel-header">
            <div className="iv-panel-num">5</div>
            <h2>Benefits Interpretation</h2>
            {completed.has('benefits') && <CheckCircle size={18} color="var(--secondary)" />}
          </div>
          {completed.has('benefits') && benefits ? (
            <>
              <div className="iv-coverage-badge" style={{ marginBottom: 12 }}>
                <StatusPill active={benefits.coverage_status === 'Active'} />
                <span style={{ marginLeft: 10, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{benefits.plan_type}</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.5 }}>{benefits.coverage_summary}</p>
            </>
          ) : activeStep === 'benefits' || (completed.has('edi271') && !completed.has('benefits')) ? (
            <>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>Interpret EDI 271 response into structured insurance benefits.</p>
              <button className="btn btn-primary iv-action-btn" onClick={runBenefits} disabled={loading}>
                {loading && activeStep === 'benefits' ? <><Loader size={16} className="spinner" /> Analyzing…</> : <>Analyze Benefits <CheckCircle size={16} /></>}
              </button>
            </>
          ) : (
            <p className="iv-locked-msg">Simulate 271 response first.</p>
          )}
        </div>

        {/* ── PANEL 6: Financial Estimation ─────────────────────────────── */}
        <div className={`glass-panel iv-panel ${!completed.has('benefits') ? 'panel-locked' : ''} ${completed.has('finance') ? 'panel-done' : ''}`}>
          <div className="iv-panel-header">
            <div className="iv-panel-num">6</div>
            <h2>Financial Estimation</h2>
            {completed.has('finance') && <CheckCircle size={18} color="var(--secondary)" />}
          </div>
          {completed.has('finance') && estimation ? (
            <div>
              <div className="iv-finance-summary">
                <div className="iv-finance-card patient">
                  <div className="iv-finance-label">Patient Pays</div>
                  <div className="iv-finance-amount">₹{(estimation.patient_pay || 0).toLocaleString()}</div>
                </div>
                <div className="iv-finance-card insurance">
                  <div className="iv-finance-label">Insurance Pays</div>
                  <div className="iv-finance-amount">₹{(estimation.insurance_pay || 0).toLocaleString()}</div>
                </div>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 10 }}>{estimation.note}</p>
            </div>
          ) : activeStep === 'finance' || (completed.has('benefits') && !completed.has('finance')) ? (
            <>
              <div className="input-group" style={{ marginBottom: 14 }}>
                <label className="input-label">Procedure Cost (₹)</label>
                <input
                  className="input-field"
                  type="number"
                  placeholder="e.g. 100000"
                  value={procedureCost}
                  onChange={e => setProcedureCost(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && runEstimation()}
                />
              </div>
              <button className="btn btn-primary iv-action-btn" onClick={runEstimation} disabled={loading || !procedureCost}>
                {loading && activeStep === 'finance' ? <><Loader size={16} className="spinner" /> Calculating…</> : <>Estimate Cost <DollarSign size={16} /></>}
              </button>
            </>
          ) : (
            <p className="iv-locked-msg">Complete benefits step first.</p>
          )}
        </div>

      {/* ── PANEL 7: Denial Risk ────────────────────────────────────────── */}
        <div className={`glass-panel iv-panel ${!completed.has('finance') ? 'panel-locked' : ''} ${completed.has('risk') ? 'panel-done' : ''}`}>
          <div className="iv-panel-header">
            <div className="iv-panel-num">7</div>
            <h2>Denial Risk Score</h2>
            {completed.has('risk') && <CheckCircle size={18} color="var(--secondary)" />}
          </div>
          {completed.has('risk') && denialRisk ? (
            <div>
              <FieldGrid fields={{
                'Risk Level':  denialRisk.risk_level,
                'Risk Score':  `${denialRisk.risk_score}/100`,
                'Summary':     denialRisk.summary,
              }} />
            </div>
          ) : activeStep === 'risk' || (completed.has('finance') && !completed.has('risk')) ? (
            <>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>Calculate the likelihood of claim denial based on coverage and card data.</p>
              <button className="btn btn-primary iv-action-btn" onClick={runDenialRisk} disabled={loading}>
                {loading && activeStep === 'risk' ? <><Loader size={16} className="spinner" /> Scoring…</> : <>Score Denial Risk <AlertTriangle size={16} /></>}
              </button>
            </>
          ) : (
            <p className="iv-locked-msg">Complete financial estimation first.</p>
          )}
        </div>

        {/* ── PANEL 8: AI Authorization ──────────────────────────────────── */}
        <div className={`glass-panel iv-panel ${!completed.has('risk') ? 'panel-locked' : ''} ${completed.has('auth') ? 'panel-done' : ''}`}>
          <div className="iv-panel-header">
            <div className="iv-panel-num">8</div>
            <h2>AI Authorization Check</h2>
            {completed.has('auth') && <CheckCircle size={18} color="var(--secondary)" />}
          </div>
          {completed.has('auth') && authResult ? (
            <FieldGrid fields={{
              'Status':           authResult.authorization_status,
              'Confidence':       `${(authResult.confidence_score * 100).toFixed(0)}%`,
              'Reason':           authResult.reason,
              'Source':           authResult.source,
            }} />
          ) : activeStep === 'auth' || (completed.has('risk') && !completed.has('auth')) ? (
            <>
              <div className="input-group" style={{ marginBottom: 10 }}>
                <label className="input-label">CPT Code *</label>
                <input className="input-field" type="text" placeholder="e.g. 99213"
                  value={cptCode} onChange={e => setCptCode(e.target.value)} />
              </div>
              <div className="input-group" style={{ marginBottom: 10 }}>
                <label className="input-label">Diagnosis Codes (comma-separated)</label>
                <input className="input-field" type="text" placeholder="e.g. J01.90, Z23"
                  value={diagCodes} onChange={e => setDiagCodes(e.target.value)} />
              </div>
              <div className="input-group" style={{ marginBottom: 14 }}>
                <label className="input-label">Medical Summary</label>
                <input className="input-field" type="text" placeholder="Brief clinical summary…"
                  value={medSummary} onChange={e => setMedSummary(e.target.value)} />
              </div>
              <button className="btn btn-primary iv-action-btn" onClick={runAuthorization} disabled={loading || !cptCode}>
                {loading && activeStep === 'auth' ? <><Loader size={16} className="spinner" /> Checking…</> : <>Run AI Authorization <Zap size={16} /></>}
              </button>
            </>
          ) : (
            <p className="iv-locked-msg">Complete denial risk step first.</p>
          )}
        </div>

      </div>

      {/* ── Done Banner ────────────────────────────────────────────────────── */}
      {completed.has('auth') && (
        <div className="glass-panel iv-done-banner fade-in">
          <CheckCircle size={22} color="var(--secondary)" />
          <div>
            <strong>Full verification & authorization complete!</strong>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', margin: '4px 0 0' }}>
              Session ID: <code>{sessionId}</code> — All data saved. Check the Results Dashboard.
            </p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 10 }}>
            <button className="btn btn-secondary" onClick={reset}><RefreshCw size={14} /> New Verification</button>
          </div>
        </div>
      )}
    </div>
  );
}
