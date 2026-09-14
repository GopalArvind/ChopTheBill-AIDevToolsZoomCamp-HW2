import { useState } from 'react';

export default function AddExpenseModal({ members, userMap, onClose, onSubmit }) {
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [payer, setPayer] = useState(members[0] || '');
  const [mode, setMode] = useState('equal');
  const [shares, setShares] = useState({});
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    const amt = Number(amount);
    if (!description.trim()) return setError('Description required');
    if (!(amt > 0)) return setError('Amount must be > 0');
    let splits = null;
    if (mode === 'custom') {
      splits = members.map((m) => ({ user_id: m, share_amount: Number(shares[m] || 0) }));
      const total = splits.reduce((s, x) => s + x.share_amount, 0);
      if (Math.abs(total - amt) > 0.01) return setError(`Custom shares must sum to ${amt.toFixed(2)} (now ${total.toFixed(2)})`);
    }
    await onSubmit({ description, amount: amt, payer_id: payer, splits });
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Add Expense</h3>
        {error && <p className="error">{error}</p>}
        <form onSubmit={submit}>
          <input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
          <input placeholder="Amount" type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} />
          <label>Payer</label>
          <select value={payer} onChange={(e) => setPayer(e.target.value)}>
            {members.map((m) => <option key={m} value={m}>{userMap[m] || m}</option>)}
          </select>
          <label>Split</label>
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="equal">Equal</option>
            <option value="custom">Custom (unequal)</option>
          </select>
          {mode === 'custom' && members.map((m) => (
            <div className="row" key={m}>
              <span>{userMap[m] || m}</span>
              <input type="number" step="0.01" placeholder="0.00"
                value={shares[m] || ''} onChange={(e) => setShares({ ...shares, [m]: e.target.value })} />
            </div>
          ))}
          <div className="row">
            <button type="button" onClick={onClose}>Cancel</button>
            <button className="primary" type="submit">Add</button>
          </div>
        </form>
      </div>
    </div>
  );
}
