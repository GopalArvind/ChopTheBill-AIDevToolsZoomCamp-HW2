// Centralized services layer — ALL backend calls go through `api`.
// Switch via .env: VITE_USE_MOCK=true (default) uses mockApi.js so the
// whole app runs without a real backend. Set VITE_USE_MOCK=false to use
// realApi.js (FastAPI per _docs/specs.md).
import { mockApi } from './mockApi.js';
import { realApi } from './realApi.js';

const USE_MOCK = (import.meta.env.VITE_USE_MOCK ?? 'true') !== 'false';
const impl = USE_MOCK ? mockApi : realApi;

export const isMockMode = USE_MOCK;

async function withTokenSync(fn, ...args) {
  const data = await fn(...args);
  // Mock stores its session internally; mirror a token for consistency.
  if (USE_MOCK && data?.token) localStorage.setItem('chopthebil_token', data.token);
  return data;
}

export const api = {
  signup: (p) => withTokenSync(impl.signup, p),
  login: (p) => withTokenSync(impl.login, p),
  logout: () => impl.logout(),
  getProfile: () => impl.getProfile(),
  listGroups: () => impl.listGroups(),
  createGroup: (p) => impl.createGroup(p),
  listExpenses: (gid) => impl.listExpenses(gid),
  createExpense: (gid, p) => impl.createExpense(gid, p),
  getBalances: (gid) => impl.getBalances(gid),
  listUsers: () => impl.listUsers(),
};
