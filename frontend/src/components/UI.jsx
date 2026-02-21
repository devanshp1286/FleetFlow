import { useState, useEffect } from 'react';

// ── Toast Notification ────────────────────────────────────────────────────────
export function Toast({ message, type = 'success', onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3500);
    return () => clearTimeout(t);
  }, []);
  const icons = { success: '✅', error: '⚠', info: 'ℹ' };
  return (
    <div className={`toast t-${type}`}>
      <span>{icons[type]}</span>
      <span>{message}</span>
    </div>
  );
}

export function useToast() {
  const [toasts, setToasts] = useState([]);
  const show = (message, type = 'success') => {
    const id = Date.now();
    setToasts(t => [...t, { id, message, type }]);
  };
  const remove = (id) => setToasts(t => t.filter(x => x.id !== id));
  const ToastContainer = () => (
    <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 200, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {toasts.map(t => <Toast key={t.id} {...t} onDone={() => remove(t.id)} />)}
    </div>
  );
  return { show, ToastContainer };
}

// ── Status Badge ──────────────────────────────────────────────────────────────
export function StatusBadge({ status }) {
  const label = status?.replace(/_/g, ' ') ?? '—';
  return <span className={`badge b-${status}`}>{label}</span>;
}

// ── Loading Spinner ───────────────────────────────────────────────────────────
export function Loading({ text = 'Loading...' }) {
  return (
    <div className="loading-overlay">
      <div className="spinner" />
      <span>{text}</span>
    </div>
  );
}

// ── KPI Card ─────────────────────────────────────────────────────────────────
export function KPICard({ label, value, sub, color = 'blue', icon }) {
  return (
    <div className={`kpi-card c-${color}`}>
      {icon && <div className="kpi-icon">{icon}</div>}
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value ?? '—'}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

// ── Modal ─────────────────────────────────────────────────────────────────────
export function Modal({ title, onClose, children }) {
  useEffect(() => {
    const handler = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">{title}</span>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

// ── Search Bar ────────────────────────────────────────────────────────────────
export function SearchBar({ value, onChange, placeholder = 'Search...' }) {
  return (
    <div className="search-wrap">
      <span className="search-icon">🔍</span>
      <input className="search-input" placeholder={placeholder} value={value} onChange={e => onChange(e.target.value)} />
    </div>
  );
}

// ── Score Bar ─────────────────────────────────────────────────────────────────
export function ScoreBar({ value, max = 100 }) {
  const pct = Math.round((value / max) * 100);
  const color = pct >= 80 ? '#00ff9d' : pct >= 60 ? '#ffc800' : '#ff3366';
  return (
    <div style={{ minWidth: 120 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color }}>{value}/{max}</span>
      </div>
      <div className="score-bar-bg">
        <div className="score-bar" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

// ── AI Risk Chip ──────────────────────────────────────────────────────────────
export function RiskChip({ level, probability }) {
  const labels = { high: '⚠ Service Now', medium: '⏰ Service Soon', low: '✓ Healthy' };
  return (
    <span className={`risk-${level}`}>
      🤖 {labels[level]} {probability !== undefined && `(${Math.round(probability * 100)}%)`}
    </span>
  );
}

// ── Formatter helpers (exported for pages) ────────────────────────────────────
export const fmt = (n) => n?.toLocaleString('en-IN') ?? '—';
export const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-IN') : '—';
export const daysUntil = (d) => Math.ceil((new Date(d) - new Date()) / 86400000);
