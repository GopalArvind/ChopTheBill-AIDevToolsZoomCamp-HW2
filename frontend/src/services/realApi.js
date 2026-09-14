// Real backend implementation. Same interface as mockApi.js.
// Expects FastAPI at VITE_API_URL with routes from _docs/specs.md:
// POST /signup, POST /login, GET/POST /groups,
// GET/POST /expenses/{group_id}, GET /balances/{group_id}.
const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

function getToken() {
  return localStorage.getItem('chopthebil_token');
}

async function req(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      msg = data.detail || data.message || msg;
    } catch { /* ignore */ }
    throw new Error(msg);
  }
  return res.status === 204 ? null : res.json();
}

export const realApi = {
  async signup({ name, email, password }) {
    const data = await req('/signup', { method: 'POST', body: { name, email, password } });
    if (data.token) localStorage.setItem('chopthebil_token', data.token);
    return data;
  },
  async login({ email, password }) {
    const data = await req('/login', { method: 'POST', body: { email, password } });
    if (data.token) localStorage.setItem('chopthebil_token', data.token);
    return data;
  },
  async logout() {
    localStorage.removeItem('chopthebil_token');
  },
  async getProfile() {
    return req('/me');
  },
  async listGroups() {
    return req('/groups');
  },
  async createGroup({ name, members }) {
    return req('/groups', { method: 'POST', body: { name, members } });
  },
  async listExpenses(groupId) {
    return req(`/expenses/${groupId}`);
  },
  async createExpense(groupId, payload) {
    return req(`/expenses/${groupId}`, { method: 'POST', body: payload });
  },
  async getBalances(groupId) {
    return req(`/balances/${groupId}`);
  },
  async listUsers() {
    return req('/users');
  },
};
