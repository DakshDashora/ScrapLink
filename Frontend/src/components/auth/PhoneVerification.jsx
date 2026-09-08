import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { sendPhoneOtp, verifyPhone, resetOtpSent, clearError } from '../../redux/slices/authSlices';

const PhoneVerification = () => {
  const [otp, setOtp] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error, otpSent } = useSelector((state) => state.auth);

  useEffect(() => {
    if (!otpSent) {
      dispatch(sendPhoneOtp());
    }
  }, [dispatch, otpSent]);

  const handleVerify = (e) => {
    e.preventDefault();
    dispatch(verifyPhone(otp)).unwrap()
      .then(() => {
        navigate('/dashboard');
      })
      .catch(() => {});
  };

  const handleResend = () => {
    dispatch(resetOtpSent());
    dispatch(sendPhoneOtp());
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Phone Verification</h2>
        <p>We sent a 6-digit OTP to your phone. Please enter it below.</p>
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
            {isLoading ? 'Verifying...' : 'Verify Phone'}
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

export default PhoneVerification;