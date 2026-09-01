// src/components/Auth/Register.jsx
import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  registerUser,
  clearErrors,
  clearSuccessFlags,
  selectAuth,
} from '../../redux/slices/authSlices';
import './Auth.css';

const Register = ({ onSwitchToLogin }) => {
  const dispatch = useDispatch();
  const { isLoading, error, registerSuccess } = useSelector(selectAuth);

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'Seller',
    gstin: '',
  });

  const [passwordStrength, setPasswordStrength] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [touchedFields, setTouchedFields] = useState({});

  useEffect(() => {
    // Clear errors when component mounts
    dispatch(clearErrors());
    
    return () => {
      dispatch(clearErrors());
      dispatch(clearSuccessFlags());
    };
  }, [dispatch]);

  useEffect(() => {
    if (registerSuccess) {
      // Show success message and redirect after 3 seconds
      const timer = setTimeout(() => {
        dispatch(clearSuccessFlags());
        onSwitchToLogin();
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [registerSuccess, onSwitchToLogin, dispatch]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Check password strength
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

  const validateGSTIN = (gstin) => {
    if (!gstin) return true;
    const gstinPattern = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
    return gstinPattern.test(gstin);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    dispatch(clearErrors());

    // Validate GSTIN
    if (formData.gstin && !validateGSTIN(formData.gstin)) {
      // You can set a specific error state here
      return;
    }

    const result = await dispatch(registerUser(formData));
    if (registerUser.fulfilled.match(result)) {
      // Success handling is done in useEffect
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">Create Account</h2>
        <p className="auth-subtitle">Register as a seller</p>

        {error && (
          <div className="auth-error">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}
        
        {registerSuccess && (
          <div className="auth-success">
            <span className="success-icon">✓</span>
            Registration successful! Redirecting to login...
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
              <option value="Admin">Admin</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="gstin">GSTIN</label>
            <input
              type="text"
              id="gstin"
              name="gstin"
              value={formData.gstin}
              onChange={handleChange}
              onBlur={() => handleBlur('gstin')}
              placeholder="Enter GSTIN (e.g., 08AAAAA0000A1Z5)"
              maxLength="15"
              className={touchedFields.gstin && formData.gstin && !validateGSTIN(formData.gstin) ? 'error' : ''}
            />
            <small className="form-hint">Format: 08AAAAA0000A1Z5 (Optional for buyers)</small>
            {touchedFields.gstin && formData.gstin && !validateGSTIN(formData.gstin) && (
              <span className="field-error">Invalid GSTIN format</span>
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
                Registering...
              </>
            ) : (
              'Register'
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