import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import {
  loginUser,
  getCurrentUser,
  clearError,
} from '../../redux/slices/authSlices';
import {
  hydrateFromStorage,
  orgStorageKey,
} from '../../redux/slices/organisationSlice';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { isLoading, error, token, user } = useSelector((s) => s.auth);

  // If already authenticated when this page mounts (e.g. refresh or back button),
  // go straight to the dashboard. Runs only on mount — no race with login submit.
  useEffect(() => {
    if (token && user) {
      navigate('/dashboard', { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Hydrate org id from localStorage once user is available
  useEffect(() => {
    if (user?.user_id) {
      const storedOrgId = localStorage.getItem(orgStorageKey(user.user_id));
      if (storedOrgId) dispatch(hydrateFromStorage(storedOrgId));
    }
  }, [user?.user_id, dispatch]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    try {
      // 1. Authenticate — sets token + stub user
      await dispatch(loginUser({ email, password })).unwrap();

      // 2. Fetch the full profile — authoritative source of user data
      await dispatch(getCurrentUser()).unwrap();

      // 3. Only now navigate — Dashboard will render with full user
      navigate('/dashboard', { replace: true });
    } catch {
      // error already in state via the thunks
    } finally {
      setSubmitting(false);
    }
  };

  const busy = isLoading || submitting;

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
            autoComplete="email"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={busy}>
            {busy ? 'Logging in…' : 'Login'}
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