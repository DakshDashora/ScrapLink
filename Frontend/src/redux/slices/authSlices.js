import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// -------------------- Async Thunks --------------------

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/api/auth/register', userData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/api/auth/login', credentials);
      return response.data; // expects { access_token, user, ... }
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/me',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.get('/api/auth/me');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const sendEmailOtp = createAsyncThunk(
  'auth/sendEmailOtp',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/api/auth/send-email-otp');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const verifyEmail = createAsyncThunk(
  'auth/verifyEmail',
  async (otp, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/api/auth/verify-email', { otp });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const sendPhoneOtp = createAsyncThunk(
  'auth/sendPhoneOtp',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/api/auth/send-phone-otp');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const verifyPhone = createAsyncThunk(
  'auth/verifyPhone',
  async (otp, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/api/auth/verify-phone', { otp });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const forgotPassword = createAsyncThunk(
  'auth/forgotPassword',
  async (email, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/api/auth/forgot-password', { email });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const resetPassword = createAsyncThunk(
  'auth/resetPassword',
  async ({ token, newPassword }, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/api/auth/reset-password', {
        token,
        new_password: newPassword,
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// -------------------- Slice --------------------

const initialState = {
  user: null,
  token: localStorage.getItem('accessToken') || null,
  isLoading: false,
  error: null,
  emailVerified: false,
  phoneVerified: false,
  otpSent: false,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      localStorage.removeItem('accessToken');
    },
    clearError: (state) => {
      state.error = null;
    },
    resetOtpSent: (state) => {
      state.otpSent = false;
    },
  },
  extraReducers: (builder) => {
    builder
      // Register
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false;
        // registration does not return token; user must login
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Registration failed';
      })
      // Login
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.access_token;
        state.user = action.payload.user;
        localStorage.setItem('accessToken', action.payload.access_token);
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Login failed';
      })
      // Get current user
      .addCase(getCurrentUser.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Failed to fetch user';
        state.token = null;
        localStorage.removeItem('accessToken');
      })
      // Send Email OTP
      .addCase(sendEmailOtp.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(sendEmailOtp.fulfilled, (state) => {
        state.isLoading = false;
        state.otpSent = true;
      })
      .addCase(sendEmailOtp.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Failed to send OTP';
      })
      // Verify Email
      .addCase(verifyEmail.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(verifyEmail.fulfilled, (state) => {
        state.isLoading = false;
        state.emailVerified = true;
        if (state.user) state.user.email_verified = true;
      })
      .addCase(verifyEmail.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Verification failed';
      })
      // Send Phone OTP
      .addCase(sendPhoneOtp.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(sendPhoneOtp.fulfilled, (state) => {
        state.isLoading = false;
        state.otpSent = true;
      })
      .addCase(sendPhoneOtp.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Failed to send OTP';
      })
      // Verify Phone
      .addCase(verifyPhone.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(verifyPhone.fulfilled, (state) => {
        state.isLoading = false;
        state.phoneVerified = true;
        if (state.user) state.user.phone_verified = true;
      })
      .addCase(verifyPhone.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Verification failed';
      })
      // Forgot Password
      .addCase(forgotPassword.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(forgotPassword.fulfilled, (state) => {
        state.isLoading = false;
        state.otpSent = true; // reusing flag
      })
      .addCase(forgotPassword.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Request failed';
      })
      // Reset Password
      .addCase(resetPassword.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(resetPassword.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(resetPassword.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Reset failed';
      });
  },
});

export const { logout, clearError, resetOtpSent } = authSlice.actions;
export default authSlice.reducer;