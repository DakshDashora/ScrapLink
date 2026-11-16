import { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../../redux/slices/authSlices';
import AlertBell from '../alerts/AlertBell';

const DashboardLayout = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const user = useSelector((s) => s.auth.user);
  const role = user?.role;
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const closeMobileMenu = () => setMobileMenuOpen(false);

  // Determine whether to show the universal back button
  // Do not show back button on root dashboard overview
  const isSubPage = location.pathname !== '/dashboard';

  return (
    <div className={`dashboard-layout ${mobileMenuOpen ? 'mobile-menu-open' : ''}`}>
      <header className="dashboard-header">
        <div className="header-left">
          <button
            className="hamburger-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
          >
            <span className="hamburger-bar"></span>
            <span className="hamburger-bar"></span>
            <span className="hamburger-bar"></span>
          </button>

          <div className="logo" onClick={() => navigate('/dashboard')} style={{ cursor: 'pointer' }}>
            Scrap<span>Link</span>
          </div>

          {isSubPage && (
            <button
              className="back-btn"
              onClick={() => navigate(-1)}
              title="Go back"
              aria-label="Go back"
            >
              ← Back
            </button>
          )}
        </div>

        <nav className="top-nav">
          {(role === 'Buyer' || role === 'Admin') && <AlertBell />}
          <div className="user-badge">
            <span className="user-avatar">{user?.full_name?.charAt(0) || 'U'}</span>
            <span className="user-info">
              <span className="user-name">{user?.full_name || 'User'}</span>
              <span className="user-role">{role}</span>
            </span>
          </div>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </nav>
      </header>

      {/* Backdrop for mobile drawer */}
      {mobileMenuOpen && (
        <div className="sidebar-backdrop" onClick={closeMobileMenu}></div>
      )}

      <aside className={`dashboard-sidebar ${mobileMenuOpen ? 'open' : ''}`}>
        <div className="sidebar-brand-mobile">
          <span>Navigation Menu</span>
          <button className="close-sidebar-btn" onClick={closeMobileMenu}>✕</button>
        </div>

        <ul className="sidebar-nav">
          <li>
            <NavLink to="/dashboard" end onClick={closeMobileMenu}>
              <span className="nav-icon">📊</span> Dashboard
            </NavLink>
          </li>

          {(role === 'Seller' || role === 'Admin') && (
            <>
              <li className="section-label">Seller Actions</li>
              <li>
                <NavLink to="/organization/new" onClick={closeMobileMenu}>
                  <span className="nav-icon">🏢</span> Create Organization
                </NavLink>
              </li>
              <li>
                <NavLink to="/seller/listings" onClick={closeMobileMenu}>
                  <span className="nav-icon">📦</span> My Listings
                </NavLink>
              </li>
              <li>
                <NavLink to="/seller/listings/new" onClick={closeMobileMenu}>
                  <span className="nav-icon">➕</span> Create Listing
                </NavLink>
              </li>
            </>
          )}

          {(role === 'Buyer' || role === 'Admin') && (
            <>
              <li className="section-label">Buyer Actions</li>
              <li>
                <NavLink to="/marketplace" onClick={closeMobileMenu}>
                  <span className="nav-icon">🛒</span> Marketplace
                </NavLink>
              </li>
              <li>
                <NavLink to="/marketplace/map" onClick={closeMobileMenu}>
                  <span className="nav-icon">🗺️</span> Map Discovery
                </NavLink>
              </li>
              <li>
                <NavLink to="/buyer/requirements" onClick={closeMobileMenu}>
                  <span className="nav-icon">📋</span> My Requirements
                </NavLink>
              </li>
              <li>
                <NavLink to="/buyer/requirements/new" onClick={closeMobileMenu}>
                  <span className="nav-icon">➕</span> Create Requirement
                </NavLink>
              </li>
              <li>
                <NavLink to="/buyer/match-alerts" onClick={closeMobileMenu}>
                  <span className="nav-icon">🔔</span> Match Alerts
                </NavLink>
              </li>
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
