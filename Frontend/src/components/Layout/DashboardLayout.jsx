import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../../redux/slices/authSlices';
import AlertBell from '../alerts/AlertBell';

const DashboardLayout = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const user = useSelector((s) => s.auth.user);
  const role = user?.role;

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  return (
    <div className="dashboard-layout">
      <header className="dashboard-header">
        <div className="logo">ScrapLink</div>

        <nav className="top-nav">
          {(role === 'Buyer' || role === 'Admin') && <AlertBell />}
          <span className="user-info">
            {user?.full_name || 'User'} · <strong>{role}</strong>
          </span>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </nav>
      </header>

      <aside className="dashboard-sidebar">
        <ul>
          <li><NavLink to="/dashboard" end>Dashboard</NavLink></li>

          {(role === 'Seller' || role === 'Admin') && (
            <>
              <li className="section-label">Seller</li>
              <li><NavLink to="/organization/new">Create Organization</NavLink></li>
              <li><NavLink to="/seller/listings">My Listings</NavLink></li>
              <li><NavLink to="/seller/listings/new">Create Listing</NavLink></li>
            </>
          )}

          {(role === 'Buyer' || role === 'Admin') && (
            <>
              <li className="section-label">Buyer</li>
              <li><NavLink to="/marketplace">Marketplace</NavLink></li>
              <li><NavLink to="/marketplace/map">Map Discovery</NavLink></li>
              <li><NavLink to="/buyer/requirements">My Requirements</NavLink></li>
              <li><NavLink to="/buyer/requirements/new">Create Requirement</NavLink></li>
              <li><NavLink to="/buyer/match-alerts">Match Alerts</NavLink></li>
            </>
          )}
        </ul>
      </aside>

      <main className="dashboard-content">
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;