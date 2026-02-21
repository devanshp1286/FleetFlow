import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

const client = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach access token to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
client.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem('refresh_token');
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {}, {
          headers: { Authorization: `Bearer ${refresh}` },
        });
        localStorage.setItem('access_token', data.data.access_token);
        original.headers.Authorization = `Bearer ${data.data.access_token}`;
        return client(original);
      } catch {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

// ── API Methods ───────────────────────────────────────────────────────────────

export const authAPI = {
  login:   (body) => client.post('/auth/login', body),
  register:(body) => client.post('/auth/register', body),
  me:      ()     => client.get('/auth/me'),
};

export const dashboardAPI = {
  kpis:           () => client.get('/dashboard/kpis'),
  liveTrips:      () => client.get('/dashboard/live-trips'),
  recentActivity: () => client.get('/dashboard/recent-activity'),
};

export const vehiclesAPI = {
  list:   (params) => client.get('/vehicles/', { params }),
  get:    (id)     => client.get(`/vehicles/${id}`),
  create: (body)   => client.post('/vehicles/', body),
  update: (id, b)  => client.put(`/vehicles/${id}`, b),
  delete: (id)     => client.delete(`/vehicles/${id}`),
};

export const driversAPI = {
  list:   (params) => client.get('/drivers/', { params }),
  get:    (id)     => client.get(`/drivers/${id}`),
  create: (body)   => client.post('/drivers/', body),
  update: (id, b)  => client.put(`/drivers/${id}`, b),
};

export const tripsAPI = {
  list:         (params) => client.get('/trips/', { params }),
  get:          (id)     => client.get(`/trips/${id}`),
  create:       (body)   => client.post('/trips/', body),
  updateStatus: (id, b)  => client.patch(`/trips/${id}/status`, b),
};

export const maintenanceAPI = {
  list:     (params) => client.get('/maintenance/', { params }),
  create:   (body)   => client.post('/maintenance/', body),
  complete: (id)     => client.patch(`/maintenance/${id}/complete`),
};

export const expensesAPI = {
  list:   (params) => client.get('/expenses/', { params }),
  create: (body)   => client.post('/expenses/', body),
};

export const analyticsAPI = {
  summary:     (params) => client.get('/analytics/summary', { params }),
  vehicleROI:  ()       => client.get('/analytics/vehicle-roi'),
  fuelEff:     ()       => client.get('/analytics/fuel-efficiency'),
  driverPerf:  ()       => client.get('/analytics/driver-performance'),
};

export const aiAPI = {
  fleetPredictions: () => client.get('/ai/maintenance-prediction/fleet/all'),
  vehiclePrediction:(id)=> client.get(`/ai/maintenance-prediction/${id}`),
  fuelForecast:     () => client.get('/ai/fuel-forecast'),
  deadAssets:       () => client.get('/ai/dead-assets'),
};

export default client;
