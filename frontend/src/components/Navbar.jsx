import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { isMockMode } from '../services/api.js';

export default function Navbar() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const onLogout = async () => { await logout(); nav('/login'); };
  return (
    <nav className="nav">
      <Link to="/">ChopTheBill</Link>
      <Link to="/groups">Groups</Link>
      <span className="spacer" />
      {isMockMode && <span style={{ opacity: 0.7, marginRight: 8 }}>(mock API)</span>}
      {user ? (
        <>
          <span>{user.name}</span>
          <button onClick={onLogout}>Logout</button>
        </>
      ) : (
        <>
          <Link to="/login">Login</Link>
          <Link to="/signup">Signup</Link>
        </>
      )}
    </nav>
  );
}
