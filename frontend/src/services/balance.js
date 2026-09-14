// Shared balance logic: net balances + minimized transactions.
// Matches specs.md: compute net balances and minimize transactions.
export function computeBalances(expenses) {
  const net = {}; // user_id -> net amount (positive = owed money)
  for (const e of expenses) {
    net[e.payer_id] = (net[e.payer_id] || 0) + Number(e.amount);
    for (const s of e.splits || []) {
      net[s.user_id] = (net[s.user_id] || 0) - Number(s.share_amount);
    }
  }
  const creditors = [];
  const debtors = [];
  for (const [user_id, amount] of Object.entries(net)) {
    const v = Math.round(Number(amount) * 100) / 100;
    if (v > 0.009) creditors.push({ user_id, amount: v });
    else if (v < -0.009) debtors.push({ user_id, amount: -v });
  }
  creditors.sort((a, b) => b.amount - a.amount);
  debtors.sort((a, b) => b.amount - a.amount);

  const transactions = [];
  let i = 0;
  let j = 0;
  while (i < debtors.length && j < creditors.length) {
    const d = debtors[i];
    const c = creditors[j];
    const amt = Math.round(Math.min(d.amount, c.amount) * 100) / 100;
    transactions.push({ from_user_id: d.user_id, to_user_id: c.user_id, amount: amt });
    d.amount = Math.round((d.amount - amt) * 100) / 100;
    c.amount = Math.round((c.amount - amt) * 100) / 100;
    if (d.amount < 0.01) i += 1;
    if (c.amount < 0.01) j += 1;
  }
  return { net, transactions };
}
