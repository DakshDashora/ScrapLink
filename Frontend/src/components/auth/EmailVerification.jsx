import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { sendEmailOtp, verifyEmail, resetOtpSent, clearError } from '../../redux/slices/authSlices';

const EmailVerification = () => {
  const [otp, setOtp] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error, otpSent, user } = useSelector((state) => state.auth);

  useEffect(() => {
    // Send OTP on mount if not sent
    if (!otpSent) {
      dispatch(sendEmailOtp());
    }
  }, [dispatch, otpSent]);

  const handleVerify = (e) => {
    e.preventDefault();
    dispatch(verifyEmail(otp)).unwrap()
      .then(() => {
        navigate('/dashboard');
      })
      .catch(() => {});
  };

  const handleResend = () => {
    dispatch(resetOtpSent());
    dispatch(sendEmailOtp());
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Email Verification</h2>
        <p>We sent a 6-digit OTP to your email. Please enter it below.</p>
        <form onSubmit={handleVerify}>
          <input
            type="text"
            placeholder="OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength="6"
            required
          />
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Verifying...' : 'Verify Email'}
          </button>
        </form>
        <div className="auth-links">
          <button onClick={handleResend} className="link-button" disabled={isLoading}>
            Resend OTP
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmailVerification;