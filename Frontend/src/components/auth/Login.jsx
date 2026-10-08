import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import { loginUser, clearError } from '../../redux/slices/authSlices';
import { hydrateFromStorage, orgStorageKey } from '../../redux/slices/organisationSlice';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error, token } = useSelector((s) => s.auth);
  const user = useSelector((s) => s.auth.user);

  useEffect(() => {
    if (token) navigate('/dashboard');
  }, [token, navigate]);

  useEffect(() => {
  if (user?.user_id) {
    const storedOrgId = localStorage.getItem(orgStorageKey(user.user_id));
    if (storedOrgId) dispatch(hydrateFromStorage(storedOrgId));
  }
}, [user?.user_id, dispatch]);

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(loginUser({ email, password }))
      .unwrap()
      .then(() => navigate('/dashboard'))
      .catch(() => {});
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Login</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/forgot-password" onClick={() => dispatch(clearError())}>
            Forgot Password?
          </Link>
          <Link to="/register" onClick={() => dispatch(clearError())}>
            Create Account
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;