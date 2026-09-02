// src/components/Auth/Login.jsx
import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  loginUser,
  clearErrors,
  clearSuccessFlags,
  resendVerificationEmail,
  selectAuth,
  selectIsAuthenticated,
} from '../../redux/slices/authSlices';
import './Auth.css';

const Login = ({ onSwitchToRegister }) => {
  const dispatch = useDispatch();
  const { isLoading, error, loginSuccess, user } = useSelector(selectAuth);
  const isAuthenticated = useSelector(selectIsAuthenticated);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [touchedFields, setTouchedFields] = useState({});
  const [showVerificationMessage, setShowVerificationMessage] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  useEffect(() => {
    dispatch(clearErrors());
    
    const token = localStorage.getItem('access_token');
    if (token && isAuthenticated) {
      // Redirect to dashboard
      console.log('User already logged in');
    }

    return () => {
      dispatch(clearErrors());
      dispatch(clearSuccessFlags());
    };
  }, [dispatch, isAuthenticated]);

  useEffect(() => {
    if (loginSuccess && isAuthenticated) {
      console.log('Login successful! Redirecting...');
    }
  }, [loginSuccess, isAuthenticated]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleBlur = (field) => {
    setTouchedFields((prev) => ({
      ...prev,
      [field]: true,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    dispatch(clearErrors());
    setShowVerificationMessage(false);
    setResendSuccess(false);

    if (!formData.email || !formData.password) {
      return;
    }

    const result = await dispatch(loginUser(formData));
    if (loginUser.rejected.match(result)) {
      if (result.payload?.requiresVerification) {
        setShowVerificationMessage(true);
      }
    }
  };

  const handleResendVerification = async () => {
    const result = await dispatch(resendVerificationEmail());
    if (resendVerificationEmail.fulfilled.match(result)) {
      setResendSuccess(true);
    }
  };

  const handleForgotPassword = () => {
    // Navigate to forgot password page
    console.log('Forgot password clicked');
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">Welcome Back</h2>
        <p className="auth-subtitle">Login to your account</p>

        {error && typeof error === 'string' && (
          <div className="auth-error">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}

        {showVerificationMessage && (
          <div className="auth-warning">
            <span className="warning-icon">🔒</span>
            <div>
              <p><strong>Email not verified</strong></p>
              <p>Please verify your email address to continue.</p>
              {!resendSuccess ? (
                <button 
                  type="button" 
                  className="resend-button"
                  onClick={handleResendVerification}
                >
                  Resend Verification Email
                </button>
              ) : (
                <p className="success-text">✓ Verification email sent!</p>
              )}
            </div>
          </div>
        )}

        {resendSuccess && !showVerificationMessage && (
          <div className="auth-success">
            <span className="success-icon">✓</span>
            Verification email has been resent. Please check your inbox.
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="form-group">
            <label htmlFor="email">
              Email Address <span className="required">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              onBlur={() => handleBlur('email')}
              required
              placeholder="Enter your email"
              autoComplete="email"
              className={touchedFields.email && !formData.email ? 'error' : ''}
            />
            {touchedFields.email && !formData.email && (
              <span className="field-error">Email is required</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">
              Password <span className="required">*</span>
            </label>
            <div className="password-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                onBlur={() => handleBlur('password')}
                required
                placeholder="Enter your password"
                autoComplete="current-password"
                className={touchedFields.password && !formData.password ? 'error' : ''}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            {touchedFields.password && !formData.password && (
              <span className="field-error">Password is required</span>
            )}
          </div>

          <div className="form-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              Remember me
            </label>
            <button
              type="button"
              className="forgot-password"
              onClick={handleForgotPassword}
            >
              Forgot password?
            </button>
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Logging in...
              </>
            ) : (
              'Login'
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <button
              type="button"
              className="auth-switch"
              onClick={onSwitchToRegister}
            >
              Register here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;