import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api.js';

export default function Dashboard() {
  const [groups, setGroups] = useState([]);
  const [name, setName] = useState('');
  const [members, setMembers] = useState('');
  const [error, setError] = useState('');

  const load = () => api.listGroups().then(setGroups).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.createGroup({ name, members: members.split(',').map((s) => s.trim()).filter(Boolean) });
      setName(''); setMembers(''); load();
    } catch (err) { setError(err.message); }
  };

  return (
    <div>
      <h2>Groups</h2>
      {error && <p className="error">{error}</p>}
      {groups.map((g) => (
        <div className="card" key={g.id}>
          <Link to={`/groups/${g.id}`}><strong>{g.name}</strong></Link>
          <div>{g.members.length} members</div>
        </div>
      ))}
      {groups.length === 0 && <p>No groups yet. Create one below.</p>}
      <div className="card">
        <h3>Create group</h3>
        <form onSubmit={create}>
          <input placeholder="Group name (e.g. Weekend Trip)" value={name} onChange={(e) => setName(e.target.value)} />
          <input placeholder="Members (comma emails, optional)" value={members} onChange={(e) => setMembers(e.target.value)} />
          <button className="primary" type="submit">Create</button>
        </form>
      </div>
    </div>
  );
}
