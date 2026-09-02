// src/components/Auth/Verification.jsx
import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  resendVerificationEmail,
  requestPhoneVerification,
  verifyPhone,
  selectUser,
  clearErrors,
  clearSuccessFlags,
} from '../../redux/slices/authSlices';
import './Verification.css';

const Verification = ({ onComplete }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const user = useSelector(selectUser);
  
  const [phoneCode, setPhoneCode] = useState('');
  const [emailResendCountdown, setEmailResendCountdown] = useState(0);
  const [phoneResendCountdown, setPhoneResendCountdown] = useState(0);
  const [verificationStep, setVerificationStep] = useState('email'); // 'email' | 'phone' | 'complete'
  const [emailSent, setEmailSent] = useState(false);
  const [phoneSent, setPhoneSent] = useState(false);
  const [phoneVerified, setPhoneVerified] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Auto-resend countdown timers
  useEffect(() => {
    let emailTimer, phoneTimer;

    if (emailResendCountdown > 0) {
      emailTimer = setTimeout(() => {
        setEmailResendCountdown(prev => prev - 1);
      }, 1000);
    }

    if (phoneResendCountdown > 0) {
      phoneTimer = setTimeout(() => {
        setPhoneResendCountdown(prev => prev - 1);
      }, 1000);
    }

    return () => {
      clearTimeout(emailTimer);
      clearTimeout(phoneTimer);
    };
  }, [emailResendCountdown, phoneResendCountdown]);

  // Send initial verification email
  useEffect(() => {
    if (user?.email && !user.email_verified) {
      handleResendEmail();
    }
  }, []);

  const handleResendEmail = async () => {
    try {
      setError('');
      const result = await dispatch(resendVerificationEmail());
      if (resendVerificationEmail.fulfilled.match(result)) {
        setEmailSent(true);
        setEmailResendCountdown(60);
        setSuccess('Verification email sent successfully!');
        setTimeout(() => setSuccess(''), 5000);
      }
    } catch (err) {
      setError('Failed to send verification email. Please try again.');
    }
  };

  const handleRequestPhoneVerification = async () => {
    if (!user.phone) {
      setError('Please add a phone number to your profile first.');
      return;
    }

    try {
      setError('');
      const result = await dispatch(requestPhoneVerification());
      if (requestPhoneVerification.fulfilled.match(result)) {
        setPhoneSent(true);
        setPhoneResendCountdown(60);
        setVerificationStep('phone');
        setSuccess('Verification code sent to your phone!');
        setTimeout(() => setSuccess(''), 5000);
      }
    } catch (err) {
      setError('Failed to send verification code. Please try again.');
    }
  };

  const handleVerifyPhone = async () => {
    if (!phoneCode || phoneCode.length < 4) {
      setError('Please enter the 4-digit verification code.');
      return;
    }

    try {
      setError('');
      const result = await dispatch(verifyPhone(phoneCode));
      if (verifyPhone.fulfilled.match(result)) {
        setPhoneVerified(true);
        setSuccess('Phone number verified successfully!');
        setTimeout(() => setSuccess(''), 5000);
        setVerificationStep('complete');
        
        // Notify parent component
        if (onComplete) {
          setTimeout(() => onComplete(), 2000);
        }
      }
    } catch (err) {
      setError('Invalid verification code. Please try again.');
      setPhoneCode('');
    }
  };

  const handlePhoneCodeChange = (e) => {
    const value = e.target.value.replace(/\D/g, '');
    if (value.length <= 6) {
      setPhoneCode(value);
      setError('');
    }
  };

  const handleSkipPhone = () => {
    setVerificationStep('complete');
    if (onComplete) {
      onComplete();
    }
  };

  const handleComplete = () => {
    navigate('/dashboard');
  };

  return (
    <div className="verification-container">
      <div className="verification-card">
        <div className="verification-header">
          <h2>Verify Your Account</h2>
          <p>Complete verification to unlock all features</p>
        </div>

        {/* Progress Indicator */}
        <div className="verification-progress">
          <div className={`progress-step ${verificationStep === 'email' || verificationStep === 'phone' || verificationStep === 'complete' ? 'active' : ''}`}>
            <span className="step-number">1</span>
            <span className="step-label">Email</span>
          </div>
          <div className={`progress-line ${verificationStep === 'phone' || verificationStep === 'complete' ? 'active' : ''}`}></div>
          <div className={`progress-step ${verificationStep === 'phone' || verificationStep === 'complete' ? 'active' : ''}`}>
            <span className="step-number">2</span>
            <span className="step-label">Phone</span>
          </div>
          <div className={`progress-line ${verificationStep === 'complete' ? 'active' : ''}`}></div>
          <div className={`progress-step ${verificationStep === 'complete' ? 'active' : ''}`}>
            <span className="step-number">3</span>
            <span className="step-label">Complete</span>
          </div>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="verification-success">
            <span className="success-icon">✓</span>
            {success}
          </div>
        )}
        
        {error && (
          <div className="verification-error">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}

        {/* Email Verification Step */}
        {(verificationStep === 'email' || verificationStep === 'phone' || verificationStep === 'complete') && (
          <div className="verification-section email-section">
            <div className="section-header">
              <span className="section-icon">📧</span>
              <h3>Email Verification</h3>
            </div>
            <div className="section-content">
              <p>
                A verification link has been sent to <strong>{user?.email}</strong>
              </p>
              <div className="status-badge">
                <span className={user?.email_verified ? 'verified' : 'pending'}>
                  {user?.email_verified ? '✓ Verified' : 'Pending Verification'}
                </span>
              </div>
              {!user?.email_verified && (
                <div className="action-buttons">
                  <button
                    onClick={handleResendEmail}
                    disabled={emailResendCountdown > 0}
                    className="resend-btn"
                  >
                    {emailResendCountdown > 0 
                      ? `Resend in ${emailResendCountdown}s` 
                      : 'Resend Verification Email'}
                  </button>
                  <p className="hint-text">
                    Check your spam folder if you don't see the email
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Phone Verification Step */}
        {(verificationStep === 'phone' || verificationStep === 'complete') && (
          <div className="verification-section phone-section">
            <div className="section-header">
              <span className="section-icon">📱</span>
              <h3>Phone Verification</h3>
            </div>
            <div className="section-content">
              {user?.phone ? (
                <>
                  <p>
                    Verify your phone number <strong>{user.phone}</strong>
                  </p>
                  <div className="status-badge">
                    <span className={user?.phone_verified ? 'verified' : 'pending'}>
                      {user?.phone_verified ? '✓ Verified' : 'Pending Verification'}
                    </span>
                  </div>
                  
                  {!user?.phone_verified && !phoneVerified && (
                    <>
                      {!phoneSent ? (
                        <div className="action-buttons">
                          <button
                            onClick={handleRequestPhoneVerification}
                            className="verify-btn"
                          >
                            Send Verification Code
                          </button>
                        </div>
                      ) : (
                        <div className="code-input-section">
                          <div className="input-group">
                            <label htmlFor="phoneCode">Enter 4-digit code</label>
                            <input
                              type="text"
                              id="phoneCode"
                              value={phoneCode}
                              onChange={handlePhoneCodeChange}
                              placeholder="Enter code"
                              maxLength="6"
                              className="code-input"
                              autoFocus
                            />
                            <div className="code-hint">
                              <span>Code sent to {user.phone}</span>
                              <button
                                onClick={handleRequestPhoneVerification}
                                disabled={phoneResendCountdown > 0}
                                className="resend-link"
                              >
                                {phoneResendCountdown > 0 
                                  ? `Resend in ${phoneResendCountdown}s` 
                                  : 'Resend Code'}
                              </button>
                            </div>
                          </div>
                          <div className="action-buttons">
                            <button
                              onClick={handleVerifyPhone}
                              className="verify-btn primary"
                              disabled={!phoneCode || phoneCode.length < 4}
                            >
                              Verify Phone
                            </button>
                            <button
                              onClick={handleSkipPhone}
                              className="skip-btn"
                            >
                              Skip for now
                            </button>
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  {phoneVerified && (
                    <div className="verification-complete">
                      <span className="complete-icon">✅</span>
                      <p>Phone number verified successfully!</p>
                    </div>
                  )}
                </>
              ) : (
                <div className="no-phone-section">
                  <p>No phone number added yet.</p>
                  <button
                    onClick={() => navigate('/profile')}
                    className="add-phone-btn"
                  >
                    Add Phone Number
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Complete Step */}
        {verificationStep === 'complete' && (
          <div className="verification-section complete-section">
            <div className="section-header">
              <span className="section-icon">🎉</span>
              <h3>Verification Complete!</h3>
            </div>
            <div className="section-content">
              <p>
                Your account is now verified. You can now access all features.
              </p>
              <div className="action-buttons">
                <button
                  onClick={handleComplete}
                  className="complete-btn"
                >
                  Go to Dashboard
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="verification-footer">
          <p>
            Need help? <a href="/support">Contact Support</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Verification;