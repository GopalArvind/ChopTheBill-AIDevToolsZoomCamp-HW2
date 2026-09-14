import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../services/api.js';
import AddExpenseModal from '../components/AddExpenseModal.jsx';
import BalanceSummary from '../components/BalanceSummary.jsx';

export default function GroupPage() {
  const { groupId } = useParams();
  const [expenses, setExpenses] = useState([]);
  const [balances, setBalances] = useState(null);
  const [groups, setGroups] = useState([]);
  const [users, setUsers] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState('');

  const group = groups.find((g) => g.id === groupId);
  const userMap = Object.fromEntries(users.map((u) => [u.id, u.name]));

  const load = async () => {
    try {
      const [ex, bal, gs, us] = await Promise.all([
        api.listExpenses(groupId), api.getBalances(groupId), api.listGroups(), api.listUsers(),
      ]);
      setExpenses(ex); setBalances(bal); setGroups(gs); setUsers(us);
    } catch (e) { setError(e.message); }
  };
  useEffect(() => { load(); }, [groupId]);

  const addExpense = async (payload) => {
    await api.createExpense(groupId, payload);
    setShowModal(false);
    load();
  };

  return (
    <div>
      <h2>{group?.name || 'Group'}</h2>
      {error && <p className="error">{error}</p>}
      <button className="primary" onClick={() => setShowModal(true)}>Add Expense</button>
      <div className="card">
        <h3>Expenses</h3>
        <table>
          <thead><tr><th>Description</th><th>Payer</th><th>Amount</th><th>Date</th></tr></thead>
          <tbody>
            {expenses.map((e) => (
              <tr key={e.id}>
                <td>{e.description}</td>
                <td>{userMap[e.payer_id] || e.payer_id}</td>
                <td>${Number(e.amount).toFixed(2)}</td>
                <td>{e.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {expenses.length === 0 && <p>No expenses yet.</p>}
      </div>
      <BalanceSummary balances={balances} userMap={userMap} />
      {showModal && (
        <AddExpenseModal members={group?.members || []} userMap={userMap}
          onClose={() => setShowModal(false)} onSubmit={addExpense} />
      )}
    </div>
  );
}
