import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

const RoleRoute = ({ allow, children }) => {
  const { user, token, isInitialized } = useSelector((s) => s.auth);

  // If token exists but auth has not finished fetching profile, wait with loading state
  if (token && !isInitialized && !user) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="loading">Authenticating session…</div>
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (!allow.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default RoleRoute;
