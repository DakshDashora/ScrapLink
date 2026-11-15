import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

const RoleRoute = ({ allow, children }) => {
  const { user, token, isAuthChecking } = useSelector((s) => s.auth);

  // If we have a token, wait for the user profile to load
  if (token && isAuthChecking) {
    return <div className="loading" style={{ padding: '4rem', textAlign: 'center' }}>Verifying session…</div>;
  }

  // If no token, or token exists but fetch failed (no user), kick to login.
  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  // Role check
  if (!allow.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default RoleRoute;