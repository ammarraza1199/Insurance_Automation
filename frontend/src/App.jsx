import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { LayoutDashboard, ScanLine, Stethoscope, Users, Activity, ShieldCheck, BarChart2, ClipboardCheck } from 'lucide-react';

// Existing pages
import HomePage from './pages/HomePage';
import OcrPage from './pages/OcrPage';
import CptPage from './pages/CptPage';
import PatientsPage from './pages/PatientsPage';

// New IV Platform pages
import InsuranceFlowPage from './pages/InsuranceFlowPage';
import AuthorizationPage from './pages/AuthorizationPage';
import ResultsDashboardPage from './pages/ResultsDashboardPage';

const NAV_ITEMS = [
  { path: '/',              label: 'Overview',              icon: LayoutDashboard },
  { path: '/verify',        label: 'Insurance Verification', icon: ShieldCheck     },
  { path: '/authorization', label: 'AI Authorization',      icon: ClipboardCheck  },
  { path: '/results',       label: 'Results Dashboard',     icon: BarChart2       },
  { path: '/patients',      label: 'Patient Records',       icon: Users           },
  { path: '/ocr',           label: 'Legacy OCR',            icon: ScanLine        },
  { path: '/cpt',           label: 'Legacy CPT Lookup',     icon: Stethoscope     },
];

function Sidebar() {
  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Activity color="white" size={20} />
        </div>
        <div className="sidebar-logo-text">
          ZeroKost
          <span>Insurance Intelligence</span>
        </div>
      </div>

      <div className="sidebar-section-label">Medical RCM Platform</div>

      {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
        <NavLink
          key={path}
          to={path}
          end={path === '/'}
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          <Icon size={18} className="nav-icon" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <div className="main-content">
          <Routes>
            <Route path="/"              element={<HomePage />}             />
            <Route path="/verify"        element={<InsuranceFlowPage />}    />
            <Route path="/authorization" element={<AuthorizationPage />}    />
            <Route path="/results"       element={<ResultsDashboardPage />} />
            <Route path="/patients"      element={<PatientsPage />}         />
            <Route path="/ocr"           element={<OcrPage />}              />
            <Route path="/cpt"           element={<CptPage />}              />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
