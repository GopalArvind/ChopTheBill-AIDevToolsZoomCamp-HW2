export default function BalanceSummary({ balances, userMap }) {
  if (!balances) return null;
  const { transactions = [], net = {} } = balances;
  const nameOf = (id) => userMap?.[id] || id;
  return (
    <div className="card">
      <h3>Balance summary</h3>
      {transactions.length === 0 ? (
        <p>All settled up.</p>
      ) : (
        <ul>
          {transactions.map((t, i) => (
            <li key={i}>{nameOf(t.from_user_id)} owes {nameOf(t.to_user_id)} ${Number(t.amount).toFixed(2)}</li>
          ))}
        </ul>
      )}
      <details>
        <summary>Net balances</summary>
        <ul>
          {Object.entries(net).map(([uid, amt]) => (
            <li key={uid}>{nameOf(uid)}: ${Number(amt).toFixed(2)}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}
