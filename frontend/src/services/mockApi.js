// Mock implementation of the full backend API.
// Same interface as realApi.js. Persists to localStorage so the app
// runs without a real backend. Seed data matches _docs/specs.md models:
// User {id, name, email}, Group {id, name, members}, Expense {id, group_id,
// description, amount, payer_id, date}, Split {user_id, share_amount}.
import { computeBalances } from './balance.js';

const USERS_KEY = 'chopthebil_mock_users';
const GROUPS_KEY = 'chopthebil_mock_groups';
const EXPENSES_KEY = 'chopthebil_mock_expenses';
const SESSION_KEY = 'chopthebil_mock_session';

const delay = (ms = 150) => new Promise((r) => setTimeout(r, ms));
const uid = (p) => `${p}_${Math.random().toString(36).slice(2, 9)}`;

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}
function save(key, val) {
  localStorage.setItem(key, JSON.stringify(val));
}

function seedIfEmpty() {
  if (!localStorage.getItem(USERS_KEY)) {
    save(USERS_KEY, [
      { id: 'u_demo', name: 'Demo User', email: 'demo@example.com', password: 'demo1234' },
      { id: 'u_alex', name: 'Alex', email: 'alex@example.com', password: 'demo1234' },
      { id: 'u_sam', name: 'Sam', email: 'sam@example.com', password: 'demo1234' },
    ]);
  }
  if (!localStorage.getItem(GROUPS_KEY)) {
    save(GROUPS_KEY, [
      { id: 'g_trip', name: 'Weekend Trip', members: ['u_demo', 'u_alex', 'u_sam'] },
    ]);
  }
  if (!localStorage.getItem(EXPENSES_KEY)) {
    save(EXPENSES_KEY, [
      {
        id: 'e_1', group_id: 'g_trip', description: 'Dinner', amount: 90,
        payer_id: 'u_demo', date: new Date().toISOString().slice(0, 10),
        splits: [
          { user_id: 'u_demo', share_amount: 30 },
          { user_id: 'u_alex', share_amount: 30 },
          { user_id: 'u_sam', share_amount: 30 },
        ],
      },
    ]);
  }
}

function currentUser() {
  seedIfEmpty();
  const session = load(SESSION_KEY, null);
  if (!session) return null;
  const users = load(USERS_KEY, []);
  return users.find((u) => u.id === session.user_id) || null;
}

function publicUser(u) {
  return { id: u.id, name: u.name, email: u.email };
}

export const mockApi = {
  async signup({ name, email, password }) {
    await delay();
    seedIfEmpty();
    const users = load(USERS_KEY, []);
    if (users.some((u) => u.email === email)) throw new Error('Email already registered');
    const user = { id: uid('u'), name, email, password };
    users.push(user);
    save(USERS_KEY, users);
    save(SESSION_KEY, { user_id: user.id, token: `mock_${user.id}` });
    return { user: publicUser(user), token: `mock_${user.id}` };
  },

  async login({ email, password }) {
    await delay();
    seedIfEmpty();
    const users = load(USERS_KEY, []);
    const user = users.find((u) => u.email === email && u.password === password);
    if (!user) throw new Error('Invalid email or password');
    save(SESSION_KEY, { user_id: user.id, token: `mock_${user.id}` });
    return { user: publicUser(user), token: `mock_${user.id}` };
  },

  async logout() {
    await delay(50);
    localStorage.removeItem(SESSION_KEY);
  },

  async getProfile() {
    await delay(50);
    const u = currentUser();
    if (!u) throw new Error('Not authenticated');
    return publicUser(u);
  },

  async listGroups() {
    await delay();
    const u = currentUser();
    if (!u) throw new Error('Not authenticated');
    const groups = load(GROUPS_KEY, []);
    return groups.filter((g) => g.members.includes(u.id));
  },

  async createGroup({ name, members = [] }) {
    await delay();
    const u = currentUser();
    if (!u) throw new Error('Not authenticated');
    if (!name?.trim()) throw new Error('Group name required');
    const groups = load(GROUPS_KEY, []);
    // members is a list of emails or names; resolve demo users by email, else create placeholder ids
    const users = load(USERS_KEY, []);
    const memberIds = new Set([u.id]);
    for (const m of members) {
      const found = users.find((x) => x.email === m);
      if (found) memberIds.add(found.id);
      else if (m?.trim()) {
        const nu = { id: uid('u'), name: m.trim(), email: m.trim(), password: '' };
        users.push(nu);
        memberIds.add(nu.id);
      }
    }
    save(USERS_KEY, users);
    const group = { id: uid('g'), name: name.trim(), members: [...memberIds] };
    groups.push(group);
    save(GROUPS_KEY, groups);
    return group;
  },

  async listExpenses(groupId) {
    await delay();
    if (!currentUser()) throw new Error('Not authenticated');
    const all = load(EXPENSES_KEY, []);
    return all.filter((e) => e.group_id === groupId);
  },

  async createExpense(groupId, { description, amount, payer_id, splits, date }) {
    await delay();
    const u = currentUser();
    if (!u) throw new Error('Not authenticated');
    if (!description?.trim()) throw new Error('Description required');
    if (!(Number(amount) > 0)) throw new Error('Amount must be > 0');
    const groups = load(GROUPS_KEY, []);
    const group = groups.find((g) => g.id === groupId);
    if (!group) throw new Error('Group not found');
    const payer = payer_id || u.id;
    if (!group.members.includes(payer)) throw new Error('Payer must be a group member');
    // Default: equal split across members if splits not provided
    let finalSplits = splits;
    if (!finalSplits || !finalSplits.length) {
      const share = Math.round((Number(amount) / group.members.length) * 100) / 100;
      finalSplits = group.members.map((user_id) => ({ user_id, share_amount: share }));
    }
    const expense = {
      id: uid('e'), group_id: groupId, description: description.trim(),
      amount: Number(amount), payer_id: payer,
      date: date || new Date().toISOString().slice(0, 10),
      splits: finalSplits,
    };
    const all = load(EXPENSES_KEY, []);
    all.push(expense);
    save(EXPENSES_KEY, all);
    return expense;
  },

  async getBalances(groupId) {
    await delay();
    if (!currentUser()) throw new Error('Not authenticated');
    const all = load(EXPENSES_KEY, []);
    const expenses = all.filter((e) => e.group_id === groupId);
    return computeBalances(expenses);
  },

  async listUsers() {
    await delay(50);
    const users = load(USERS_KEY, []);
    return users.map(publicUser);
  },
};
