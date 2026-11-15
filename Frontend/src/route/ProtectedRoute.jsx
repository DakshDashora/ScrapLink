import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

const ProtectedRoute = ({ children }) => {
  const { token, isAuthChecking } = useSelector((s) => s.auth);

  // If we have a token, wait for the user profile to load before rendering
  if (token && isAuthChecking) {
    return <div className="loading" style={{ padding: '4rem', textAlign: 'center' }}>Verifying session…</div>;
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;