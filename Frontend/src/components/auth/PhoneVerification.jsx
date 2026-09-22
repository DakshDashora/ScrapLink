import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { verifyOtp, resendOtp, clearError } from '../../redux/slices/authSlices';

const PhoneVerification = () => {
  const [otp, setOtp] = useState('');
  const [otpRequested, setOtpRequested] = useState(false);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { pendingUser, isLoading, error, otpExpiresIn } = useSelector(
    (s) => s.auth
  );

  useEffect(() => {
    if (!pendingUser?.email) {
      navigate('/register');
      return;
    }
    // Send phone OTP automatically on mount
    dispatch(
      resendOtp({
        type: 'PHONE_VERIFICATION',
        email: pendingUser.email,
        phone: pendingUser.phone,
      })
    ).then(() => setOtpRequested(true));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleVerify = (e) => {
    e.preventDefault();
    dispatch(
      verifyOtp({
        type: 'PHONE_VERIFICATION',
        email: pendingUser.email,
        phone: pendingUser.phone,
        otp,
      })
    )
      .unwrap()
      .then(() => {
        // Both verified → user can log in
        navigate('/login');
      })
      .catch(() => {});
  };

  const handleResend = () => {
    dispatch(
      resendOtp({
        type: 'PHONE_VERIFICATION',
        email: pendingUser.email,
        phone: pendingUser.phone,
      })
    );
  };

  if (!pendingUser) return null;

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Phone Verification</h2>
        <p>
          We sent a 6-digit OTP to <strong>{pendingUser.phone}</strong>.
          Please enter it below.
        </p>

        <form onSubmit={handleVerify}>
          <input
            type="text"
            placeholder="Phone OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength={6}
            required
          />
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Verifying...' : 'Verify Phone'}
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
              navigate('/verify-email');
            }}
          >
            Back to Email Verification
          </button>
        </div>
      </div>
    </div>
  );
};

export default PhoneVerification;