import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// ---------------- Thunks ----------------

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/auth/register', userData);
      return data;
      // { id, full_name, email, phone, role, email_verified, phone_verified, created_at }
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/auth/login', credentials);
      return data;
      // { access_token, token_type, user_id, email, role,
      //   email_verified, phone_verified, full_name }
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/me',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/auth/me');
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const getVerificationStatus = createAsyncThunk(
  'auth/verificationStatus',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/auth/verification-status');
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Resend / send OTP (used by both email & phone pages)
// payload: { type: 'EMAIL_VERIFICATION' | 'PHONE_VERIFICATION', email?, phone? }
export const resendOtp = createAsyncThunk(
  'auth/resendOtp',
  async (payload, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/auth/otp/resend', payload);
      return data; // { message, expires_in }
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Verify OTP for email or phone
// payload: { type, email?, phone?, otp }
export const verifyOtp = createAsyncThunk(
  'auth/verifyOtp',
  async (payload, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/auth/otp/verify', payload);
      return { ...payload, message: data };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Step 1 of password reset: request OTP via email
export const requestPasswordReset = createAsyncThunk(
  'auth/requestPasswordReset',
  async ({ email }, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post(
        '/auth/otp/password-reset-request',
        { email }
      );
      return { email, message: data };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Step 2 of password reset: confirm with OTP + new password
export const confirmPasswordReset = createAsyncThunk(
  'auth/confirmPasswordReset',
  async ({ email, otp, new_password }, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post(
        '/auth/otp/password-reset-confirm',
        { email, otp, new_password }
      );
      return { message: data };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// ---------------- Slice ----------------

const initialState = {
  user: null,                    // logged-in user
  token: localStorage.getItem('accessToken') || null,

  // used during the register → email → phone verification flow
  pendingUser: null,             // { id, full_name, email, phone, role, ... }
  emailVerified: false,
  phoneVerified: false,

  // UI state
  isLoading: false,
  otpSent: false,
  otpExpiresIn: null,
  error: null,
  passwordResetRequestedFor: null, // email remembered between the two pages
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.pendingUser = null;
      state.emailVerified = false;
      state.phoneVerified = false;
      localStorage.removeItem('accessToken');
    },
    clearError: (state) => {
      state.error = null;
    },
    resetOtpSent: (state) => {
      state.otpSent = false;
    },
    clearPendingUser: (state) => {
      state.pendingUser = null;
      state.emailVerified = false;
      state.phoneVerified = false;
      state.otpSent = false;
    },
  },
  extraReducers: (builder) => {
    builder
      // ---------- REGISTER ----------
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.pendingUser = action.payload;
        state.emailVerified = !!action.payload.email_verified;
        state.phoneVerified = !!action.payload.phone_verified;
        // Backend auto-sends email OTP on register
        state.otpSent = true;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = extractError(action.payload, 'Registration failed');
      })

      // ---------- LOGIN ----------
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.access_token;
        localStorage.setItem('accessToken', action.payload.access_token);
        state.user = {
          user_id: action.payload.user_id,
          email: action.payload.email,
          role: action.payload.role,
          full_name: action.payload.full_name,
          email_verified: action.payload.email_verified,
          phone_verified: action.payload.phone_verified,
        };
        // Clear the pending signup flow state
        state.pendingUser = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = extractError(action.payload, 'Login failed');
      })

      // ---------- GET ME ----------
      .addCase(getCurrentUser.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = extractError(action.payload, 'Failed to fetch user');
        state.token = null;
        localStorage.removeItem('accessToken');
      })

      // ---------- VERIFICATION STATUS ----------
      .addCase(getVerificationStatus.fulfilled, (state, action) => {
        state.emailVerified = !!action.payload?.email_verified;
        state.phoneVerified = !!action.payload?.phone_verified;
        if (state.user) {
          state.user.email_verified = state.emailVerified;
          state.user.phone_verified = state.phoneVerified;
        }
      })

      // ---------- RESEND OTP ----------
      .addCase(resendOtp.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(resendOtp.fulfilled, (state, action) => {
        state.isLoading = false;
        state.otpSent = true;
        state.otpExpiresIn = action.payload?.expires_in ?? null;
      })
      .addCase(resendOtp.rejected, (state, action) => {
        state.isLoading = false;
        state.error = extractError(action.payload, 'Failed to send OTP');
      })

      // ---------- VERIFY OTP ----------
      .addCase(verifyOtp.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(verifyOtp.fulfilled, (state, action) => {
        state.isLoading = false;
        if (action.payload.type === 'EMAIL_VERIFICATION') {
          state.emailVerified = true;
          if (state.pendingUser) state.pendingUser.email_verified = true;
        } else if (action.payload.type === 'PHONE_VERIFICATION') {
          state.phoneVerified = true;
          if (state.pendingUser) state.pendingUser.phone_verified = true;
        }
      })
      .addCase(verifyOtp.rejected, (state, action) => {
        state.isLoading = false;
        state.error = extractError(action.payload, 'Verification failed');
      })

      // ---------- PASSWORD RESET REQUEST ----------
      .addCase(requestPasswordReset.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(requestPasswordReset.fulfilled, (state, action) => {
        state.isLoading = false;
        state.otpSent = true;
        state.passwordResetRequestedFor = action.payload.email;
      })
      .addCase(requestPasswordReset.rejected, (state, action) => {
        state.isLoading = false;
        state.error = extractError(action.payload, 'Request failed');
      })

      // ---------- PASSWORD RESET CONFIRM ----------
      .addCase(confirmPasswordReset.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(confirmPasswordReset.fulfilled, (state) => {
        state.isLoading = false;
        state.passwordResetRequestedFor = null;
        state.otpSent = false;
      })
      .addCase(confirmPasswordReset.rejected, (state, action) => {
        state.isLoading = false;
        state.error = extractError(action.payload, 'Reset failed');
      });
  },
});

// Backend returns 422 with { detail: [{msg}] } – unwrap nicely
function extractError(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload === 'string') return payload;
  if (payload.detail) {
    if (typeof payload.detail === 'string') return payload.detail;
    if (Array.isArray(payload.detail)) {
      return payload.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
    }
  }
  return fallback;
}

export const {
  logout,
  clearError,
  resetOtpSent,
  clearPendingUser,
} = authSlice.actions;

export default authSlice.reducer;