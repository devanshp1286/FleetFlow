import { useEffect, useState } from 'react';
import useAuthStore from './store/authStore';
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import VehicleRegistry from './pages/Vehicles';
import TripDispatcher from './pages/Trips';
import MaintenancePage from './pages/Maintenance';
import ExpensesPage from './pages/Expenses';
import DriversPage from './pages/Drivers';
import AnalyticsPage from './pages/Analytics';
import { useToast } from './components/UI';

const NAV = [
  { id: 'dashboard',   icon: '📊', label: 'Dashboard' },
  { id: 'vehicles',    icon: '🚛', label: 'Vehicle Registry' },
  { id: 'trips',       icon: '🗺', label: 'Trip Dispatcher' },
  { id: 'maintenance', icon: '🔧', label: 'Maintenance' },
  { id: 'expenses',    icon: '💰', label: 'Expense & Fuel' },
  { id: 'drivers',     icon: '👤', label: 'Driver Profiles' },
  { id: 'analytics',   icon: '📈', label: 'Analytics' },
];

const PAGE_TITLES = {
  dashboard: 'Dashboard', vehicles: 'Vehicle Registry', trips: 'Trip Dispatcher',
  maintenance: 'Maintenance & Service', expenses: 'Expense & Fuel Log',
  drivers: 'Driver Profiles', analytics: 'Operational Analytics',
};

const PAGE_COMPONENTS = {
  dashboard: Dashboard, vehicles: VehicleRegistry, trips: TripDispatcher,
  maintenance: MaintenancePage, expenses: ExpensesPage,
  drivers: DriversPage, analytics: AnalyticsPage,
};

export default function App() {
  const { user, hydrateUser, logout } = useAuthStore();
  const [page, setPage] = useState('dashboard');
  const { show, ToastContainer } = useToast();

  useEffect(() => { hydrateUser(); }, []);

  if (!user) return <LoginPage />;

  const PageComponent = PAGE_COMPONENTS[page];

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo-area">
          <div className="logo-name">FleetFlow</div>
          <div className="logo-tag">Fleet Intelligence</div>
        </div>
        <nav className="nav-list">
          {NAV.map(n => (
            <div key={n.id} className={`nav-item${page === n.id ? ' active' : ''}`} onClick={() => setPage(n.id)}>
              <span className="nav-icon">{n.icon}</span>
              {n.label}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-pill">
            <div className="avatar">{user.username[0].toUpperCase()}</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{user.username}</div>
              <div style={{ fontSize: 11, color: 'var(--muted)' }}>{user.role}</div>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 10, width: '100%', justifyContent: 'center' }} onClick={logout}>
            Logout
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="main-content">
        <div className="topbar">
          <h1 className="page-heading">{PAGE_TITLES[page]}</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="live-dot">● LIVE</span>
            <span style={{ fontSize: 12, color: 'var(--muted)' }}>
              {new Date().toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}
            </span>
          </div>
        </div>
        <div className="page-content">
          <PageComponent showToast={show} />
        </div>
      </div>

      <ToastContainer />
    </div>
  );
}
