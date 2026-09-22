import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { requestPasswordReset, clearError } from '../../redux/slices/authSlices';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error } = useSelector((s) => s.auth);

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(requestPasswordReset({ email }))
      .unwrap()
      .then(({ email: sentTo }) => {
        navigate(`/reset-password?email=${encodeURIComponent(sentTo)}`);
      })
      .catch(() => {});
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Forgot Password</h2>
        <p>
          Enter your registered email. We'll send you an OTP to reset your
          password.
        </p>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Your registered email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Sending...' : 'Send Reset OTP'}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/login" onClick={() => dispatch(clearError())}>
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;