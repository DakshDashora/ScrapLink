import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { confirmPasswordReset, clearError } from '../../redux/slices/authSlices';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const emailFromQuery = searchParams.get('email') || '';

  const [email, setEmail] = useState(emailFromQuery);
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState('');

  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error } = useSelector((s) => s.auth);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLocalError('');

    if (newPassword !== confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }

    dispatch(
      confirmPasswordReset({
        email,
        otp,
        new_password: newPassword,
      })
    )
      .unwrap()
      .then(() => {
        navigate('/login');
      })
      .catch(() => {});
  };

  const shownError = localError || error;

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Reset Password</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Your registered email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="OTP from email"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength={6}
            required
          />
          <input
            type="password"
            placeholder="New Password (8+ chars)"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Confirm New Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          {shownError && <div className="error-message">{shownError}</div>}

          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Resetting...' : 'Reset Password'}
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

export default ResetPassword;