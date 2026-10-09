import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// ---------------- Helpers ----------------

/**
 * Normalize a user object coming from any endpoint.
 * Login returns:  { user_id, full_name, email, role, email_verified, phone_verified }
 * /auth/me may return: { id, name, email, role, ... } — same fields under different keys.
 * This function guarantees a consistent shape across the app.
 */
function normalizeUser(raw) {
  if (!raw) return null;
  return {
    user_id: raw.user_id || raw.id || null,
    full_name: raw.full_name || raw.name || '',
    email: raw.email || '',
    role: raw.role || null,
    phone: raw.phone || null,
    email_verified: !!raw.email_verified,
    phone_verified: !!raw.phone_verified,
    created_at: raw.created_at || null,
  };
}

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

// ---------------- Thunks ----------------

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/auth/register', userData);
      return data;
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

export const resendOtp = createAsyncThunk(
  'auth/resendOtp',
  async (payload, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/auth/otp/resend', payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

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
  user: null,
  token: localStorage.getItem('accessToken') || null,

  // signup flow
  pendingUser: null,
  emailVerified: false,
  phoneVerified: false,

  // UI state
  isLoading: false,
  otpSent: false,
  otpExpiresIn: null,
  error: null,
  passwordResetRequestedFor: null,
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

        // Set a stub user so the UI has SOMETHING immediately.
        // getCurrentUser will overwrite this with the full profile.
        state.user = normalizeUser(action.payload);
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
        // Normalize regardless of endpoint shape (id vs user_id, name vs full_name)
        state.user = normalizeUser(action.payload);
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = extractError(action.payload, 'Failed to fetch user');
        state.token = null;
        state.user = null;
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

export const {
  logout,
  clearError,
  resetOtpSent,
  clearPendingUser,
} = authSlice.actions;

export default authSlice.reducer;