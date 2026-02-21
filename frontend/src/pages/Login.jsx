import { useState } from 'react';
import useAuthStore from '../store/authStore';

export default function LoginPage() {
  const { login, register, loading, error } = useAuthStore();
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ username: '', email: '', password: '', role: 'dispatcher' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async () => {
    if (mode === 'login') {
      await login(form.username, form.password);
    } else {
      await register(form);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">FleetFlow</div>
        <div className="login-tagline">Smart Fleet & Logistics Platform</div>

        <div className="form-group">
          <label className="form-label">Username</label>
          <input className="form-input" placeholder="admin" value={form.username}
            onChange={e => set('username', e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()} />
        </div>
        {mode === 'register' && (
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" type="email" placeholder="you@example.com" value={form.email}
              onChange={e => set('email', e.target.value)} />
          </div>
        )}
        <div className="form-group">
          <label className="form-label">Password</label>
          <input className="form-input" type="password" placeholder="••••••••" value={form.password}
            onChange={e => set('password', e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()} />
        </div>
        {mode === 'register' && (
          <div className="form-group">
            <label className="form-label">Role</label>
            <select className="form-input form-select" value={form.role} onChange={e => set('role', e.target.value)}>
              <option value="admin">Admin</option>
              <option value="dispatcher">Dispatcher</option>
              <option value="driver">Driver</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
        )}

        {error && <div className="form-error">⚠ {error}</div>}

        <button className="btn btn-primary btn-full" style={{ marginTop: 20 }} onClick={submit} disabled={loading}>
          {loading ? '⏳ Please wait...' : mode === 'login' ? '🚀 Login' : '✅ Create Account'}
        </button>

        <div style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: 'var(--muted)' }}>
          {mode === 'login'
            ? <span>New here? <span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => setMode('register')}>Create Account</span></span>
            : <span>Have an account? <span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => setMode('login')}>Login</span></span>
          }
        </div>
        <div style={{ textAlign: 'center', marginTop: 12, fontSize: 11, color: 'var(--muted)' }}>
          Demo: <strong>admin</strong> / <strong>FleetFlow@123</strong> (after running seed.py)
        </div>
      </div>
    </div>
  );
}
