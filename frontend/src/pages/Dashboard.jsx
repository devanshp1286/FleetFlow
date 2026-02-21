import { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { dashboardAPI, analyticsAPI } from '../api/client';
import { KPICard, StatusBadge, Loading, fmt } from '../components/UI';

const CHART_STYLE = { background: 'transparent', border: '1px solid #1a2d4a', borderRadius: 8, fontSize: 12 };

export default function Dashboard({ showToast }) {
  const [kpis, setKpis]   = useState(null);
  const [trips, setTrips]  = useState([]);
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [kRes, tRes, sRes] = await Promise.all([
        dashboardAPI.kpis(),
        dashboardAPI.liveTrips(),
        analyticsAPI.summary({ months: 6 }),
      ]);
      setKpis(kRes.data.data);
      setTrips(tRes.data.data);
      setSummary(sRes.data.data);
    } catch (e) {
      showToast('Failed to load dashboard data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000); // Live polling
    return () => clearInterval(interval);
  }, []);

  if (loading) return <Loading text="Loading fleet data..." />;

  const statusData = kpis ? [
    { name: 'Available', value: kpis.fleet.available, color: '#00ff9d' },
    { name: 'On Trip',   value: kpis.fleet.active,    color: '#00d4ff' },
    { name: 'In Shop',   value: kpis.fleet.in_shop,   color: '#ff6b35' },
  ] : [];

  return (
    <div>
      {/* KPI Cards */}
      <div className="kpi-grid mb-6">
        <KPICard label="Active Fleet"        value={kpis?.fleet.active}      sub={`${kpis?.fleet.utilization_pct}% utilization`}                color="blue"   icon="🚛" />
        <KPICard label="Maintenance Alerts"  value={kpis?.alerts.total}      sub={`${kpis?.alerts.in_shop} in shop · ${kpis?.alerts.license_expiring} lic. expiring`} color={kpis?.alerts.total > 0 ? 'orange' : 'green'} icon="🔧" />
        <KPICard label="Pending Cargo"       value={kpis?.trips.pending}     sub="Awaiting dispatch"                                            color="orange"  icon="📦" />
        <KPICard label="Monthly Fuel Cost"   value={`₹${fmt(kpis?.financials.monthly_fuel)}`} sub="Current month"                             color="red"    icon="⛽" />
      </div>

      {/* Charts Row */}
      <div className="grid-2 mb-6">
        <div className="card">
          <div className="card-header"><span className="card-title">Fleet Status Distribution</span></div>
          <div className="card-body">
            <div style={{ height: 160 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={statusData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" paddingAngle={3}>
                    {statusData.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip contentStyle={CHART_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {statusData.map(s => (
              <div key={s.name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: s.color, flexShrink: 0 }} />
                <span style={{ fontSize: 12, color: 'var(--muted)', flex: 1 }}>{s.name}</span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{s.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Monthly Cost Trend</span></div>
          <div className="card-body">
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={summary}>
                  <defs>
                    <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#00d4ff" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}   />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(26,45,74,.5)" />
                  <XAxis dataKey="month_short" tick={{ fill: '#5a7fa0', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#5a7fa0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `₹${v/1000}k`} />
                  <Tooltip contentStyle={CHART_STYLE} formatter={v => [`₹${fmt(v)}`, 'Total Cost']} />
                  <Area type="monotone" dataKey="total_cost" stroke="#00d4ff" strokeWidth={2} fill="url(#cg)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Live Trips */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Live Trips</span>
          <span className="live-dot">● LIVE</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Trip ID</th><th>Vehicle</th><th>Driver</th><th>Route</th><th>Status</th><th>Est. Fuel</th></tr></thead>
            <tbody>
              {trips.length === 0 && (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: 32, color: 'var(--muted)' }}>No active trips</td></tr>
              )}
              {trips.map(t => (
                <tr key={t.id}>
                  <td><span className="tag">{t.id.slice(-8).toUpperCase()}</span></td>
                  <td className="mono">{t.vehicle_reg}</td>
                  <td>{t.driver_name}</td>
                  <td className="muted" style={{ fontSize: 12 }}>{t.origin} → {t.destination}</td>
                  <td><StatusBadge status={t.status} /></td>
                  <td style={{ color: 'var(--accent2)' }}>₹{fmt(t.estimated_fuel_cost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
