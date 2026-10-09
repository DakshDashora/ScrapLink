import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const user = useSelector((s) => s.auth.user);
  const role = user?.role;

  // Guard: don't render an empty shell while the profile is still loading
  if (!user) {
    return (
      <div className="dashboard-home">
        <div className="loading">Loading your profile…</div>
      </div>
    );
  }

  return (
    <div className="dashboard-home">
      <h2>Welcome back, {user.full_name || 'there'}</h2>
      <p>Role: <strong>{role || '—'}</strong></p>
      <p>
        Email: {user.email || '—'}{' '}
        {user.email_verified ? '✅' : '⚠'}
      </p>
      <p>
        Phone: {user.phone || '—'}{' '}
        {user.phone_verified ? '✅' : '⚠'}
      </p>

      <div className="quick-actions">
        {(role === 'Seller' || role === 'Admin') && (
          <Link to="/seller/listings/new" className="action-card">
            <h3>+ Create Listing</h3>
            <p>Post new industrial scrap to the marketplace</p>
          </Link>
        )}
        {(role === 'Seller' || role === 'Admin') && (
          <Link to="/seller/listings" className="action-card">
            <h3>My Listings</h3>
            <p>Manage your existing listings</p>
          </Link>
        )}
        {(role === 'Buyer' || role === 'Admin') && (
          <Link to="/marketplace" className="action-card">
            <h3>Browse Marketplace</h3>
            <p>Search active scrap listings</p>
          </Link>
        )}
        {(role === 'Buyer' || role === 'Admin') && (
          <Link to="/marketplace/map" className="action-card">
            <h3>Map Discovery</h3>
            <p>Find scrap near you</p>
          </Link>
        )}
      </div>
    </div>
  );
};

export default Dashboard;