import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { verifyOtp, resendOtp, clearError } from '../../redux/slices/authSlices';

const EmailVerification = () => {
  const [otp, setOtp] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { pendingUser, isLoading, error, otpExpiresIn } = useSelector(
    (s) => s.auth
  );

  // If user lands here without registering (e.g. refresh), send them back
  useEffect(() => {
    if (!pendingUser?.email) {
      navigate('/register');
    }
  }, [pendingUser, navigate]);

  const handleVerify = (e) => {
    e.preventDefault();
    dispatch(
      verifyOtp({
        type: 'EMAIL_VERIFICATION',
        email: pendingUser.email,
        otp,
      })
    )
      .unwrap()
      .then(() => {
        // Move on to phone verification
        navigate('/verify-phone');
      })
      .catch(() => {});
  };

  const handleResend = () => {
    dispatch(
      resendOtp({
        type: 'EMAIL_VERIFICATION',
        email: pendingUser.email,
      })
    );
  };

  if (!pendingUser) return null;

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Email Verification</h2>
        <p>
          We sent a 6-digit OTP to <strong>{pendingUser.email}</strong>.
          Please enter it below.
        </p>

        <form onSubmit={handleVerify}>
          <input
            type="text"
            placeholder="Email OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength={6}
            required
          />
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Verifying...' : 'Verify Email'}
          </button>
        </form>

        <div className="auth-links">
          <button
            type="button"
            onClick={handleResend}
            className="link-button"
            disabled={isLoading}
          >
            {isLoading
              ? 'Sending...'
              : otpExpiresIn
              ? `Resend OTP (valid ${otpExpiresIn}s)`
              : 'Resend OTP'}
          </button>
          <button
            type="button"
            className="link-button"
            onClick={() => {
              dispatch(clearError());
              navigate('/register');
            }}
          >
            Back to Register
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmailVerification;