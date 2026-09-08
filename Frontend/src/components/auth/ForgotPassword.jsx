import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { forgotPassword, clearError } from '../../redux/slices/authSlices';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const dispatch = useDispatch();
  const { isLoading, error, otpSent } = useSelector((state) => state.auth);

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(forgotPassword(email));
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Forgot Password</h2>
        {otpSent ? (
          <p>Password reset instructions have been sent to your email.</p>
        ) : (
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
              {isLoading ? 'Sending...' : 'Send Reset Link'}
            </button>
          </form>
        )}
        <div className="auth-links">
          <a href="/login" onClick={() => dispatch(clearError())}>Back to Login</a>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;