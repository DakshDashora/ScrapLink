// src/components/Auth/Register.jsx (Updated)
import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  registerUser,
  clearErrors,
  clearSuccessFlags,
  selectAuth,
} from '../../redux/slices/authSlices';
import Verification from './Verification';
import './Auth.css';

const Register = ({ onSwitchToLogin }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error, registerSuccess, user } = useSelector(selectAuth);

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'Seller',
    phone: '',
  });

  const [passwordStrength, setPasswordStrength] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [touchedFields, setTouchedFields] = useState({});
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [showVerification, setShowVerification] = useState(false);

  useEffect(() => {
    dispatch(clearErrors());
    
    return () => {
      dispatch(clearErrors());
      dispatch(clearSuccessFlags());
    };
  }, [dispatch]);

  useEffect(() => {
    // If registration is successful and user is created, show verification
    if (registerSuccess && user) {
      setShowVerification(true);
    }
  }, [registerSuccess, user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    if (name === 'password') {
      checkPasswordStrength(value);
    }
  };

  const handleBlur = (field) => {
    setTouchedFields((prev) => ({
      ...prev,
      [field]: true,
    }));
  };

  const checkPasswordStrength = (password) => {
    if (password.length === 0) {
      setPasswordStrength('');
      return;
    }
    
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    const strength = [hasUpperCase, hasLowerCase, hasNumber, hasSpecial].filter(Boolean).length;
    
    if (password.length < 8) {
      setPasswordStrength('weak');
    } else if (strength <= 2) {
      setPasswordStrength('weak');
    } else if (strength === 3) {
      setPasswordStrength('medium');
    } else if (strength === 4) {
      setPasswordStrength('strong');
    }
  };

  const validatePhone = (phone) => {
    if (!phone) return true;
    const phonePattern = /^[0-9]{10}$/;
    return phonePattern.test(phone);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    dispatch(clearErrors());

    // Validate required fields
    if (!formData.full_name || !formData.email || !formData.password) {
      return;
    }

    // Validate phone if provided
    if (formData.phone && !validatePhone(formData.phone)) {
      return;
    }

    // Validate terms
    if (!acceptTerms) {
      // Set error for terms
      return;
    }

    const result = await dispatch(registerUser(formData));
    if (registerUser.fulfilled.match(result)) {
      // Verification will show automatically via useEffect
    }
  };

  const handleVerificationComplete = () => {
    // Navigate to dashboard after verification
    navigate('/dashboard');
  };

  // Show verification component after successful registration
  if (showVerification) {
    return <Verification onComplete={handleVerificationComplete} />;
  }

  // Show registration form
  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">Create Account</h2>
        <p className="auth-subtitle">Join as a {formData.role}</p>

        {error && (
          <div className="auth-error">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="form-group">
            <label htmlFor="full_name">
              Full Name <span className="required">*</span>
            </label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              onBlur={() => handleBlur('full_name')}
              required
              placeholder="Enter your full name"
              className={touchedFields.full_name && !formData.full_name ? 'error' : ''}
            />
            {touchedFields.full_name && !formData.full_name && (
              <span className="field-error">Full name is required</span>
            )}
          </div>

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
            <small className="form-hint">We'll send a verification link to this email</small>
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
                minLength="8"
                className={touchedFields.password && formData.password.length < 8 ? 'error' : ''}
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
            {passwordStrength && (
              <div className={`password-strength password-strength-${passwordStrength}`}>
                Password strength: {passwordStrength}
              </div>
            )}
            <small className="form-hint">
              Must be at least 8 characters with uppercase, lowercase, number, and special character
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="role">Role</label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
            >
              <option value="Seller">Seller</option>
              <option value="Buyer">Buyer</option>
            </select>
            <small className="form-hint">Select your primary role on the platform</small>
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone Number</label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              onBlur={() => handleBlur('phone')}
              placeholder="Enter your phone number (10 digits)"
              maxLength="10"
              className={touchedFields.phone && formData.phone && !validatePhone(formData.phone) ? 'error' : ''}
            />
            {touchedFields.phone && formData.phone && !validatePhone(formData.phone) && (
              <span className="field-error">Please enter a valid 10-digit phone number</span>
            )}
            <small className="form-hint">Optional but recommended for account security</small>
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
                required
              />
              I agree to the <a href="/terms" target="_blank">Terms of Service</a> and <a href="/privacy" target="_blank">Privacy Policy</a>
              <span className="required">*</span>
            </label>
            {!acceptTerms && touchedFields.acceptTerms && (
              <span className="field-error">You must agree to the terms</span>
            )}
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <button
              type="button"
              className="auth-switch"
              onClick={onSwitchToLogin}
            >
              Login here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;