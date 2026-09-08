import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../../redux/slices/authSlices';

const DashboardLayout = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const user = useSelector((state) => state.auth.user);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  return (
    <div className="dashboard-layout">
      <header className="dashboard-header">
        <div className="logo">ScrapLink</div>
        <nav>
          <span>Welcome, {user?.full_name || 'User'}</span>
          <button onClick={handleLogout}>Logout</button>
        </nav>
      </header>
      <aside className="dashboard-sidebar">
        <ul>
          <li><Link to="/dashboard">Dashboard</Link></li>
          <li><Link to="/dashboard/profile">Profile</Link></li>
          {/* more links later */}
        </ul>
      </aside>
      <main className="dashboard-content">
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;