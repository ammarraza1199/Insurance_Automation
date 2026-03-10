import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, CheckCircle, AlertCircle, Loader } from 'lucide-react';

const UploadDocument = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const processFile = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      setResult(response.data);
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      console.error(err);
      setError('Failed to extract document. Make sure the FastAPI backend is running.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="glass-panel">
      <h2>Upload Medical Document</h2>
      <p style={{ marginBottom: '24px' }}>Upload a PDF or Image to automatically extract patient demographics and ICD-10 Diagnosis codes.</p>
      
      {!file ? (
        <label 
          className={`upload-dropzone ${isDragging ? 'active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input type="file" style={{ display: 'none' }} onChange={handleFileChange} accept=".png, .jpg, .jpeg, .pdf" />
          <UploadCloud className="upload-icon" />
          <div>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem' }}>Click or drag file to this area to upload</h3>
            <p>Support for a single or bulk upload. Strictly prohibit from uploading company data or other band files.</p>
          </div>
        </label>
      ) : (
        <div style={{ padding: '24px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
            <FileText size={32} color="var(--primary)" />
            <div style={{ flex: 1 }}>
              <h4 style={{ margin: 0 }}>{file.name}</h4>
              <p style={{ fontSize: '0.85rem', margin: 0 }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            <button className="btn btn-secondary" onClick={() => { setFile(null); setResult(null); setError(null); }}>
              Cancel
            </button>
          </div>

          <button 
            className="btn btn-primary" 
            style={{ width: '100%' }} 
            onClick={processFile} 
            disabled={isUploading}
          >
            {isUploading ? <><Loader size={18} className="spinner" /> Processing with OCR...</> : 'Extract Data'}
          </button>
        </div>
      )}

      {error && (
        <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '8px', display: 'flex', gap: '12px' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div style={{ marginTop: '24px', animation: 'pulse 0.5s ease-out' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--secondary)', marginBottom: '16px' }}>
            <CheckCircle size={20} />
            <span style={{ fontWeight: 600 }}>Extraction Successful</span>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Patient Name</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 500, marginTop: '4px' }}>{result.data.patient_info.name}</div>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>DOB</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 500, marginTop: '4px' }}>{result.data.patient_info.dob}</div>
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Extracted ICD-10 Codes</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
              {result.data.icd10_codes.length > 0 ? (
                result.data.icd10_codes.map(code => (
                  <span key={code} className="badge">{code}</span>
                ))
              ) : (
                <span style={{ color: 'var(--text-secondary)' }}>No ICD-10 codes found in document.</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadDocument;
