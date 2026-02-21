// ─── VEHICLES PAGE ────────────────────────────────────────────────────────────
import { useState, useEffect, useCallback } from 'react';
import { vehiclesAPI, driversAPI, tripsAPI, maintenanceAPI, expensesAPI, analyticsAPI, aiAPI } from '../api/client';
import { StatusBadge, Loading, Modal, SearchBar, KPICard, RiskChip, ScoreBar, fmt, fmtDate, daysUntil } from '../components/UI';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const CHART_STYLE = { background: 'transparent', border: '1px solid #1a2d4a', borderRadius: 8, fontSize: 12 };

// ── Generic fetch hook ────────────────────────────────────────────────────────
function useData(fetchFn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchFn();
      setData(res.data.data);
    } catch (e) {
      setError(e.response?.data?.message || 'Error loading data');
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => { load(); }, [load]);
  return { data, loading, error, reload: load };
}

// ─── VEHICLES ─────────────────────────────────────────────────────────────────
export function VehicleRegistry({ showToast }) {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [predictions, setPredictions] = useState({});
  const [form, setForm] = useState({ registration_number: '', make: '', model: '', type: 'truck', capacity_kg: '', odometer_km: '', fuel_efficiency_kmpl: '' });
  const { data: vehicles, loading, reload } = useData(() => vehiclesAPI.list({ status: filter !== 'all' ? filter : undefined, search: search || undefined }), [filter, search]);

  useEffect(() => {
    aiAPI.fleetPredictions().then(r => {
      const map = {};
      r.data.data.forEach(p => { map[p.vehicle_id] = p.prediction; });
      setPredictions(map);
    }).catch(() => {});
  }, [vehicles]);

  const save = async () => {
    try {
      await vehiclesAPI.create({ ...form, capacity_kg: +form.capacity_kg, odometer_km: +form.odometer_km || 0, fuel_efficiency_kmpl: form.fuel_efficiency_kmpl ? +form.fuel_efficiency_kmpl : undefined });
      showToast('Vehicle registered!');
      setShowModal(false);
      reload();
    } catch (e) {
      showToast(e.response?.data?.message || 'Failed to register vehicle', 'error');
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Vehicle Registry ({vehicles?.length ?? 0})</span>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <SearchBar value={search} onChange={setSearch} placeholder="Search reg, make..." />
            <select className="form-input form-select" style={{ width: 'auto', padding: '8px 32px 8px 12px' }} value={filter} onChange={e => setFilter(e.target.value)}>
              {['all', 'available', 'on_trip', 'in_shop'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Add Vehicle</button>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>#</th><th>Registration</th><th>Make / Model</th><th>Type</th><th>Capacity</th><th>Odometer</th><th>Efficiency</th><th>Status</th><th>AI Health</th></tr></thead>
            <tbody>
              {(vehicles || []).map((v, i) => {
                const pred = predictions[v.id];
                return (
                  <tr key={v.id}>
                    <td className="muted" style={{ fontSize: 11 }}>{i + 1}</td>
                    <td className="mono">{v.registration_number}</td>
                    <td>{v.make} {v.model}</td>
                    <td>{v.type}</td>
                    <td>{fmt(v.capacity_kg)} kg</td>
                    <td>{fmt(v.odometer_km)} km</td>
                    <td>{v.fuel_efficiency_kmpl ? `${v.fuel_efficiency_kmpl} km/L` : '—'}</td>
                    <td><StatusBadge status={v.status} /></td>
                    <td>{pred ? <RiskChip level={pred.risk_level} probability={pred.probability} /> : <span className="muted">—</span>}</td>
                  </tr>
                );
              })}
              {(!vehicles || vehicles.length === 0) && <tr><td colSpan={9} style={{ textAlign: 'center', padding: 32, color: 'var(--muted)' }}>No vehicles found</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <Modal title="🚛 Register New Vehicle" onClose={() => setShowModal(false)}>
          <div className="form-row">
            <div className="form-group"><label className="form-label">Registration *</label><input className="form-input" placeholder="GJ05AB1234" value={form.registration_number} onChange={e => setForm(f => ({ ...f, registration_number: e.target.value }))} /></div>
            <div className="form-group"><label className="form-label">Type *</label><select className="form-input form-select" value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))}><option value="truck">Truck</option><option value="mini">Mini</option><option value="van">Van</option><option value="tanker">Tanker</option></select></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="form-label">Make *</label><input className="form-input" placeholder="Tata" value={form.make} onChange={e => setForm(f => ({ ...f, make: e.target.value }))} /></div>
            <div className="form-group"><label className="form-label">Model *</label><input className="form-input" placeholder="407" value={form.model} onChange={e => setForm(f => ({ ...f, model: e.target.value }))} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="form-label">Capacity (kg) *</label><input className="form-input" type="number" value={form.capacity_kg} onChange={e => setForm(f => ({ ...f, capacity_kg: e.target.value }))} /></div>
            <div className="form-group"><label className="form-label">Odometer (km)</label><input className="form-input" type="number" value={form.odometer_km} onChange={e => setForm(f => ({ ...f, odometer_km: e.target.value }))} /></div>
          </div>
          <div className="form-group"><label className="form-label">Fuel Efficiency (km/L)</label><input className="form-input" type="number" placeholder="8.5" value={form.fuel_efficiency_kmpl} onChange={e => setForm(f => ({ ...f, fuel_efficiency_kmpl: e.target.value }))} /></div>
          <div className="form-actions">
            <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={save}>💾 Save</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default VehicleRegistry;

// ─── TRIPS PAGE ───────────────────────────────────────────────────────────────
export function TripDispatcher({ showToast }) {
  const [showModal, setShowModal] = useState(false);
  const [dispatchError, setDispatchError] = useState('');
  const [form, setForm] = useState({ vehicle_id: '', driver_id: '', cargo_weight_kg: '', origin: '', destination: '', scheduled_departure: '', estimated_fuel_cost: '' });
  const { data: trips, loading, reload } = useData(() => tripsAPI.list({ per_page: 30 }));
  const { data: vehicles } = useData(() => vehiclesAPI.list({ status: 'available', per_page: 50 }));
  const { data: drivers }  = useData(() => driversAPI.list({ status: 'available', per_page: 50 }));

  const selectedVehicle = vehicles?.find(v => v.id === form.vehicle_id);

  const dispatch = async () => {
    setDispatchError('');
    try {
      await tripsAPI.create({ ...form, cargo_weight_kg: +form.cargo_weight_kg, estimated_fuel_cost: form.estimated_fuel_cost ? +form.estimated_fuel_cost : undefined });
      showToast('Trip dispatched successfully!');
      setShowModal(false);
      reload();
    } catch (e) {
      setDispatchError(e.response?.data?.message || 'Dispatch failed');
    }
  };

  const updateStatus = async (tripId, status) => {
    try {
      await tripsAPI.updateStatus(tripId, { status });
      showToast(`Trip ${status}!`);
      reload();
    } catch (e) {
      showToast(e.response?.data?.message || 'Update failed', 'error');
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Trip Dispatcher ({trips?.length ?? 0} trips)</span>
          <button className="btn btn-primary" onClick={() => { setShowModal(true); setDispatchError(''); }}>+ New Trip</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>Vehicle</th><th>Driver</th><th>Cargo</th><th>Route</th><th>Departure</th><th>Status</th><th>Est. Fuel</th><th>Action</th></tr></thead>
            <tbody>
              {(trips || []).map(t => (
                <tr key={t.id}>
                  <td><span className="tag">{t.id.slice(-8).toUpperCase()}</span></td>
                  <td className="mono">{t.vehicle_reg}</td>
                  <td>{t.driver_name}</td>
                  <td>{fmt(t.cargo_weight_kg)} kg</td>
                  <td className="muted" style={{ fontSize: 12 }}>{t.origin} → {t.destination}</td>
                  <td className="muted" style={{ fontSize: 11 }}>{t.scheduled_departure?.slice(0, 16).replace('T', ' ')}</td>
                  <td><StatusBadge status={t.status} /></td>
                  <td style={{ color: 'var(--accent2)' }}>₹{fmt(t.estimated_fuel_cost)}</td>
                  <td>
                    {t.status === 'dispatched' && <button className="btn btn-ghost btn-sm" onClick={() => updateStatus(t.id, 'in_transit')}>▶ Start</button>}
                    {t.status === 'in_transit' && <button className="btn btn-ghost btn-sm" onClick={() => updateStatus(t.id, 'completed')}>✓ Complete</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <Modal title="🚛 Book New Trip" onClose={() => setShowModal(false)}>
          <div className="form-group">
            <label className="form-label">Vehicle *</label>
            <select className="form-input form-select" value={form.vehicle_id} onChange={e => setForm(f => ({ ...f, vehicle_id: e.target.value }))}>
              <option value="">— Select available vehicle —</option>
              {(vehicles || []).map(v => <option key={v.id} value={v.id}>{v.registration_number} · {v.make} {v.model} · Cap: {fmt(v.capacity_kg)}kg</option>)}
            </select>
            {selectedVehicle && <div style={{ marginTop: 6, fontSize: 11, color: 'var(--accent)' }}>Max capacity: {fmt(selectedVehicle.capacity_kg)} kg · {selectedVehicle.fuel_efficiency_kmpl} km/L</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Driver *</label>
            <select className="form-input form-select" value={form.driver_id} onChange={e => setForm(f => ({ ...f, driver_id: e.target.value }))}>
              <option value="">— Select available driver —</option>
              {(drivers || []).map(d => <option key={d.id} value={d.id}>{d.full_name} · Safety: {d.safety_score}/100</option>)}
            </select>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="form-label">Origin *</label><input className="form-input" placeholder="Surat, Gujarat" value={form.origin} onChange={e => setForm(f => ({ ...f, origin: e.target.value }))} /></div>
            <div className="form-group"><label className="form-label">Destination *</label><input className="form-input" placeholder="Mumbai, Maharashtra" value={form.destination} onChange={e => setForm(f => ({ ...f, destination: e.target.value }))} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="form-label">Cargo Weight (kg) *</label><input className="form-input" type="number" value={form.cargo_weight_kg} onChange={e => { setForm(f => ({ ...f, cargo_weight_kg: e.target.value })); setDispatchError(''); }} /></div>
            <div className="form-group"><label className="form-label">Est. Fuel Cost (₹)</label><input className="form-input" type="number" value={form.estimated_fuel_cost} onChange={e => setForm(f => ({ ...f, estimated_fuel_cost: e.target.value }))} /></div>
          </div>
          <div className="form-group"><label className="form-label">Scheduled Departure *</label><input className="form-input" type="datetime-local" value={form.scheduled_departure} onChange={e => setForm(f => ({ ...f, scheduled_departure: e.target.value }))} /></div>
          {dispatchError && <div className="form-error">⚠ {dispatchError}</div>}
          <div className="form-actions">
            <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={dispatch}>🚀 Dispatch</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── MAINTENANCE PAGE ─────────────────────────────────────────────────────────
export function MaintenancePage({ showToast }) {
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ vehicle_id: '', service_type: '', description: '', cost: '', service_date: '', odometer_at_service: '', next_service_km: '' });
  const { data: logs, loading, reload } = useData(() => maintenanceAPI.list({ per_page: 30 }));
  const { data: vehicles } = useData(() => vehiclesAPI.list({ per_page: 100 }));

  const save = async () => {
    try {
      await maintenanceAPI.create({ ...form, cost: +form.cost, odometer_at_service: +form.odometer_at_service, next_service_km: form.next_service_km ? +form.next_service_km : undefined });
      showToast('Maintenance logged. Vehicle locked from dispatch.', 'info');
      setShowModal(false);
      reload();
    } catch (e) {
      showToast(e.response?.data?.message || 'Failed to log maintenance', 'error');
    }
  };

  const complete = async (id) => {
    try {
      await maintenanceAPI.complete(id);
      showToast('Service completed. Vehicle unlocked!');
      reload();
    } catch (e) {
      showToast('Failed to complete service', 'error');
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Maintenance & Service Logs ({logs?.length ?? 0})</span>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Log Service</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Vehicle</th><th>Service Type</th><th>Description</th><th>Cost</th><th>Date</th><th>Odometer</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>
              {(logs || []).map(m => (
                <tr key={m.id}>
                  <td className="mono">{m.vehicle_reg}</td>
                  <td style={{ fontWeight: 500 }}>{m.service_type}</td>
                  <td className="muted" style={{ fontSize: 12, maxWidth: 180 }}>{m.description}</td>
                  <td style={{ color: 'var(--accent2)' }}>₹{fmt(m.cost)}</td>
                  <td className="muted" style={{ fontSize: 12 }}>{m.service_date}</td>
                  <td>{fmt(m.odometer_at_service)} km</td>
                  <td><StatusBadge status={m.status} /></td>
                  <td>{m.status !== 'completed' && <button className="btn btn-ghost btn-sm" onClick={() => complete(m.id)}>✓ Complete</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <Modal title="🔧 Log Maintenance" onClose={() => setShowModal(false)}>
          <div className="form-group">
            <label className="form-label">Vehicle *</label>
            <select className="form-input form-select" value={form.vehicle_id} onChange={e => setForm(f => ({ ...f, vehicle_id: e.target.value }))}>
              <option value="">— Select vehicle —</option>
              {(vehicles || []).map(v => <option key={v.id} value={v.id}>{v.registration_number} · {v.make} {v.model}</option>)}
            </select>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="form-label">Service Type *</label><input className="form-input" placeholder="Oil Change, Tyres..." value={form.service_type} onChange={e => setForm(f => ({ ...f, service_type: e.target.value }))} /></div>
            <div className="form-group"><label className="form-label">Cost (₹) *</label><input className="form-input" type="number" value={form.cost} onChange={e => setForm(f => ({ ...f, cost: e.target.value }))} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="form-label">Date *</label><input className="form-input" type="date" value={form.service_date} onChange={e => setForm(f => ({ ...f, service_date: e.target.value }))} /></div>
            <div className="form-group"><label className="form-label">Odometer (km) *</label><input className="form-input" type="number" value={form.odometer_at_service} onChange={e => setForm(f => ({ ...f, odometer_at_service: e.target.value }))} /></div>
          </div>
          <div className="form-group"><label className="form-label">Next Service at (km)</label><input className="form-input" type="number" value={form.next_service_km} onChange={e => setForm(f => ({ ...f, next_service_km: e.target.value }))} /></div>
          <div className="form-group"><label className="form-label">Description</label><textarea className="form-input" rows={2} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} /></div>
          <div className="form-warn" style={{ marginBottom: 12 }}>⚠ Auto-Lock: Vehicle will be locked from dispatch until service is completed.</div>
          <div className="form-actions">
            <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={save}>💾 Save Log</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── EXPENSES PAGE ────────────────────────────────────────────────────────────
export function ExpensesPage({ showToast }) {
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ vehicle_id: '', expense_type: 'fuel', amount: '', fuel_liters: '', fuel_price_per_liter: '', expense_date: '', notes: '' });
  const { data: expenses, loading, reload } = useData(() => expensesAPI.list({ per_page: 30 }));
  const { data: vehicles } = useData(() => vehiclesAPI.list({ per_page: 100 }));

  const totalFuel   = expenses?.filter(e => e.expense_type === 'fuel').reduce((s, e) => s + e.amount, 0) || 0;
  const totalRepair = expenses?.filter(e => e.expense_type === 'repair').reduce((s, e) => s + e.amount, 0) || 0;
  const total       = expenses?.reduce((s, e) => s + e.amount, 0) || 0;

  const save = async () => {
    try {
      await expensesAPI.create({ ...form, amount: +form.amount, fuel_liters: form.fuel_liters ? +form.fuel_liters : undefined, fuel_price_per_liter: form.fuel_price_per_liter ? +form.fuel_price_per_liter : undefined });
      showToast('Expense logged!');
      setShowModal(false);
      reload();
    } catch (e) {
      showToast(e.response?.data?.message || 'Failed', 'error');
    }
  };

  if (loading) return <Loading />;

  const TYPE_COLORS = { fuel: '#00d4ff', repair: '#ff6b35', toll: '#ffc800', insurance: '#00ff9d', other: '#888' };

  return (
    <div>
      <div className="kpi-grid mb-6">
        <KPICard label="Total Expenses"  value={`₹${fmt(total)}`}       color="red"    icon="💰" />
        <KPICard label="Fuel Costs"      value={`₹${fmt(totalFuel)}`}   color="blue"   icon="⛽" />
        <KPICard label="Repair Costs"    value={`₹${fmt(totalRepair)}`} color="orange" icon="🔧" />
        <KPICard label="Records"         value={expenses?.length}        color="green"  icon="📋" />
      </div>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Expense & Fuel Log</span>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Add Expense</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Vehicle</th><th>Type</th><th>Amount</th><th>Liters</th><th>₹/Liter</th><th>Date</th><th>Driver</th></tr></thead>
            <tbody>
              {(expenses || []).map(e => (
                <tr key={e.id}>
                  <td className="mono">{e.vehicle_reg}</td>
                  <td><span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: `${TYPE_COLORS[e.expense_type]}18`, color: TYPE_COLORS[e.expense_type], border: `1px solid ${TYPE_COLORS[e.expense_type]}33`, fontWeight: 600 }}>{e.expense_type.toUpperCase()}</span></td>
                  <td style={{ color: 'var(--accent2)', fontWeight: 600 }}>₹{fmt(e.amount)}</td>
                  <td className="muted">{e.fuel_liters ? `${e.fuel_liters} L` : '—'}</td>
                  <td className="muted">{e.fuel_price_per_liter ? `₹${e.fuel_price_per_liter}` : '—'}</td>
                  <td className="muted" style={{ fontSize: 12 }}>{e.expense_date}</td>
                  <td>{e.driver_name || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <Modal title="💰 Log Expense" onClose={() => setShowModal(false)}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Vehicle *</label>
              <select className="form-input form-select" value={form.vehicle_id} onChange={e => setForm(f => ({ ...f, vehicle_id: e.target.value }))}>
                <option value="">— Select —</option>
                {(vehicles || []).map(v => <option key={v.id} value={v.id}>{v.registration_number}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Type *</label>
              <select className="form-input form-select" value={form.expense_type} onChange={e => setForm(f => ({ ...f, expense_type: e.target.value }))}>
                {['fuel', 'repair', 'toll', 'insurance', 'other'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="form-label">Amount (₹) *</label><input className="form-input" type="number" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} /></div>
            <div className="form-group"><label className="form-label">Date *</label><input className="form-input" type="date" value={form.expense_date} onChange={e => setForm(f => ({ ...f, expense_date: e.target.value }))} /></div>
          </div>
          {form.expense_type === 'fuel' && (
            <div className="form-row">
              <div className="form-group"><label className="form-label">Liters</label><input className="form-input" type="number" value={form.fuel_liters} onChange={e => setForm(f => ({ ...f, fuel_liters: e.target.value }))} /></div>
              <div className="form-group"><label className="form-label">Price/Liter (₹)</label><input className="form-input" type="number" value={form.fuel_price_per_liter} onChange={e => setForm(f => ({ ...f, fuel_price_per_liter: e.target.value }))} /></div>
            </div>
          )}
          <div className="form-group"><label className="form-label">Notes</label><textarea className="form-input" rows={2} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
          <div className="form-actions">
            <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={save}>💾 Save</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── DRIVERS PAGE ─────────────────────────────────────────────────────────────
export function DriversPage({ showToast }) {
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ full_name: '', license_number: '', license_expiry: '', phone: '' });
  const { data: drivers, loading, reload } = useData(() => driversAPI.list({ per_page: 50 }));

  const save = async () => {
    try {
      await driversAPI.create(form);
      showToast('Driver profile created!');
      setShowModal(false);
      reload();
    } catch (e) {
      showToast(e.response?.data?.message || 'Failed', 'error');
    }
  };

  if (loading) return <Loading />;

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Driver Performance & Safety ({drivers?.length ?? 0})</span>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Add Driver</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>License</th><th>Expiry</th><th>Safety Score</th><th>Trips</th><th>KM Driven</th><th>Incidents</th><th>Status</th></tr></thead>
            <tbody>
              {(drivers || []).map(d => {
                const days = daysUntil(d.license_expiry);
                const expColor = days < 0 ? 'var(--danger)' : days < 30 ? 'var(--warn)' : 'var(--accent2)';
                return (
                  <tr key={d.id}>
                    <td style={{ fontWeight: 600 }}>{d.full_name}</td>
                    <td className="mono">{d.license_number}</td>
                    <td><span style={{ fontSize: 12, color: expColor, fontWeight: 600 }}>{days < 0 ? '⛔ EXPIRED' : days < 30 ? `⚠ ${days}d left` : d.license_expiry}</span></td>
                    <td><ScoreBar value={d.safety_score} /></td>
                    <td>{fmt(d.total_trips)}</td>
                    <td>{fmt(d.total_km_driven)} km</td>
                    <td style={{ color: d.incidents_count > 2 ? 'var(--danger)' : d.incidents_count > 0 ? 'var(--warn)' : 'var(--accent2)' }}>{d.incidents_count}</td>
                    <td><StatusBadge status={d.duty_status} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <Modal title="👤 Add Driver" onClose={() => setShowModal(false)}>
          <div className="form-group"><label className="form-label">Full Name *</label><input className="form-input" value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} /></div>
          <div className="form-row">
            <div className="form-group"><label className="form-label">License No. *</label><input className="form-input" value={form.license_number} onChange={e => setForm(f => ({ ...f, license_number: e.target.value }))} /></div>
            <div className="form-group"><label className="form-label">Expiry Date *</label><input className="form-input" type="date" value={form.license_expiry} onChange={e => setForm(f => ({ ...f, license_expiry: e.target.value }))} /></div>
          </div>
          <div className="form-group"><label className="form-label">Phone</label><input className="form-input" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} /></div>
          <div className="form-actions">
            <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={save}>💾 Save</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── ANALYTICS PAGE ───────────────────────────────────────────────────────────
export function AnalyticsPage({ showToast }) {
  const { data: summary }  = useData(() => analyticsAPI.summary({ months: 6 }));
  const { data: roi }      = useData(() => analyticsAPI.vehicleROI());
  const { data: fuelEff }  = useData(() => analyticsAPI.fuelEff());
  const { data: forecast } = useData(() => aiAPI.fuelForecast());
  const { data: deadAssets } = useData(() => aiAPI.deadAssets());

  const totalRev  = roi?.reduce((s, v) => s + v.estimated_revenue, 0) || 0;
  const totalCost = roi?.reduce((s, v) => s + v.total_cost, 0) || 0;

  return (
    <div>
      <div className="kpi-grid mb-6">
        <KPICard label="Est. Fleet Revenue"  value={`₹${fmt(Math.round(totalRev))}`}        color="green"  icon="📈" />
        <KPICard label="Total Fleet Costs"   value={`₹${fmt(Math.round(totalCost))}`}       color="red"    icon="📉" />
        <KPICard label="Est. Net Profit"     value={`₹${fmt(Math.round(totalRev-totalCost))}`} color={totalRev > totalCost ? 'green' : 'red'} icon="💹" />
        <KPICard label="Dead Assets"         value={deadAssets?.count ?? 0}                  color="orange" icon="🚫" />
      </div>

      <div className="grid-2 mb-6">
        <div className="card">
          <div className="card-header"><span className="card-title">Monthly P&L</span></div>
          <div className="card-body">
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summary || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(26,45,74,.5)" />
                  <XAxis dataKey="month_short" tick={{ fill: '#5a7fa0', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#5a7fa0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `₹${v/1000}k`} />
                  <Tooltip contentStyle={CHART_STYLE} formatter={v => [`₹${fmt(v)}`]} />
                  <Bar dataKey="total_cost"   fill="#ff6b35" radius={[4,4,0,0]} name="Cost" />
                  <Bar dataKey="fuel_cost"    fill="#00d4ff" radius={[4,4,0,0]} name="Fuel" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">🤖 Fuel Cost Forecast (AI)</span></div>
          <div className="card-body">
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={[...(forecast?.historical || []).map(h => ({ name: h.month, actual: h.actual })), ...(forecast?.forecast || []).map(f => ({ name: f.month, predicted: f.predicted, upper: f.upper_bound, lower: f.lower_bound }))]}>
                  <defs>
                    <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00ff9d" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#00ff9d" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(26,45,74,.5)" />
                  <XAxis dataKey="name" tick={{ fill: '#5a7fa0', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#5a7fa0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `₹${v/1000}k`} />
                  <Tooltip contentStyle={CHART_STYLE} formatter={v => [`₹${fmt(v)}`]} />
                  <Area type="monotone" dataKey="actual"    stroke="#00d4ff" strokeWidth={2} fill="transparent" name="Actual" />
                  <Area type="monotone" dataKey="predicted" stroke="#00ff9d" strokeWidth={2} strokeDasharray="5 5" fill="url(#fg)" name="Forecast" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header"><span className="card-title">🤖 AI Vehicle ROI Analysis</span></div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Vehicle</th><th>Type</th><th>Completed Trips</th><th>Distance</th><th>Est. Revenue</th><th>Total Cost</th><th>Net ROI</th><th>Verdict</th></tr></thead>
            <tbody>
              {(roi || []).map(v => (
                <tr key={v.vehicle_id}>
                  <td className="mono">{v.registration}</td>
                  <td>{v.type}</td>
                  <td>{v.trips_completed}</td>
                  <td>{fmt(v.total_distance_km)} km</td>
                  <td style={{ color: '#00ff9d' }}>₹{fmt(Math.round(v.estimated_revenue))}</td>
                  <td style={{ color: 'var(--warn)' }}>₹{fmt(Math.round(v.total_cost))}</td>
                  <td style={{ fontWeight: 700, color: v.net_roi >= 0 ? '#00ff9d' : '#ff3366' }}>₹{fmt(Math.round(v.net_roi))}</td>
                  <td>
                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, fontWeight: 600, background: v.net_roi > 100000 ? 'rgba(0,255,157,.1)' : v.net_roi >= 0 ? 'rgba(255,200,0,.1)' : 'rgba(255,51,102,.1)', color: v.net_roi > 100000 ? '#00ff9d' : v.net_roi >= 0 ? '#ffc800' : '#ff3366', border: '1px solid currentColor' }}>
                      {v.net_roi > 100000 ? '⭐ Top Performer' : v.net_roi >= 0 ? '✓ Profitable' : '⚠ Review'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {(deadAssets?.dead_assets?.length > 0) && (
        <div className="card">
          <div className="card-header"><span className="card-title">⚠ Dead Asset Detection</span></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Vehicle</th><th>Make/Model</th><th>Idle Days</th><th>Last Activity</th><th>Recommendation</th></tr></thead>
              <tbody>
                {deadAssets.dead_assets.map(a => (
                  <tr key={a.vehicle_id}>
                    <td className="mono">{a.registration}</td>
                    <td>{a.make_model}</td>
                    <td style={{ color: 'var(--danger)', fontWeight: 700 }}>{a.idle_days} days</td>
                    <td className="muted">{a.last_activity}</td>
                    <td style={{ fontSize: 12, color: 'var(--warn)' }}>{a.recommendation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
