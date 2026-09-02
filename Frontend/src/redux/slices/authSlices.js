// src/redux/slices/authSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authService } from '../../components/axios/axiosConfig';

// Initial state matching the Users table structure
const initialState = {
  user: {
    user_id: null,
    full_name: '',
    email: '',
    role: '', // 'Buyer' | 'Seller' | 'Admin'
    phone: '',
    email_verified: false,
    phone_verified: false,
    created_at: null,
    updated_at: null,
  },
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  registerSuccess: false,
  loginSuccess: false,
  emailVerificationSent: false,
  phoneVerificationSent: false,
};

// Async Thunks
export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await authService.register(userData);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Registration failed';
      return rejectWithValue(errorMessage);
    }
  }
);

export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials);
      
      // Store token in localStorage
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('token_type', response.data.token_type || 'bearer');
        localStorage.setItem('expires_in', response.data.expires_in || '3600');
      }
      
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Login failed';
      
      // Check if email is not verified
      if (error.response?.data?.requires_verification) {
        return rejectWithValue({
          message: errorMessage,
          requiresVerification: true,
          email: error.response?.data?.email,
        });
      }
      
      return rejectWithValue(errorMessage);
    }
  }
);

export const logoutUser = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
    } catch (error) {
      // Even if logout fails, clear local storage
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('token_type');
      localStorage.removeItem('expires_in');
    }
    return null;
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.getCurrentUser();
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to fetch user';
      return rejectWithValue(errorMessage);
    }
  }
);

export const verifyEmail = createAsyncThunk(
  'auth/verifyEmail',
  async (token, { rejectWithValue }) => {
    try {
      const response = await authService.verifyEmail(token);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Email verification failed';
      return rejectWithValue(errorMessage);
    }
  }
);

export const verifyPhone = createAsyncThunk(
  'auth/verifyPhone',
  async (code, { rejectWithValue }) => {
    try {
      const response = await authService.verifyPhone(code);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Phone verification failed';
      return rejectWithValue(errorMessage);
    }
  }
);

export const requestPhoneVerification = createAsyncThunk(
  'auth/requestPhoneVerification',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.requestPhoneVerification();
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to send verification code';
      return rejectWithValue(errorMessage);
    }
  }
);

export const resendVerificationEmail = createAsyncThunk(
  'auth/resendVerificationEmail',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.resendVerificationEmail();
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to resend verification email';
      return rejectWithValue(errorMessage);
    }
  }
);

export const forgotPassword = createAsyncThunk(
  'auth/forgotPassword',
  async (email, { rejectWithValue }) => {
    try {
      const response = await authService.forgotPassword(email);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to send reset email';
      return rejectWithValue(errorMessage);
    }
  }
);

export const resetPassword = createAsyncThunk(
  'auth/resetPassword',
  async ({ token, newPassword }, { rejectWithValue }) => {
    try {
      const response = await authService.resetPassword(token, newPassword);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Password reset failed';
      return rejectWithValue(errorMessage);
    }
  }
);

export const updateProfile = createAsyncThunk(
  'auth/updateProfile',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await authService.updateProfile(userData);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Profile update failed';
      return rejectWithValue(errorMessage);
    }
  }
);

// Auth Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearErrors: (state) => {
      state.error = null;
    },
    clearSuccessFlags: (state) => {
      state.registerSuccess = false;
      state.loginSuccess = false;
      state.emailVerificationSent = false;
      state.phoneVerificationSent = false;
    },
    setAuthenticated: (state, action) => {
      state.isAuthenticated = action.payload;
    },
    restoreSession: (state) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        state.token = token;
        state.isAuthenticated = true;
      }
    },
    updateUserField: (state, action) => {
      const { field, value } = action.payload;
      state.user[field] = value;
    },
  },
  extraReducers: (builder) => {
    builder
      // Register
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
        state.registerSuccess = false;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.registerSuccess = true;
        state.user = {
          ...state.user,
          ...action.payload.data,
        };
        state.error = null;
        state.emailVerificationSent = true;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false;
        state.registerSuccess = false;
        state.error = action.payload || 'Registration failed';
      })
      
      // Login
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
        state.loginSuccess = false;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.loginSuccess = true;
        state.token = action.payload.access_token;
        state.user = {
          ...state.user,
          ...action.payload.user,
        };
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.loginSuccess = false;
        state.token = null;
        state.error = action.payload.message || action.payload || 'Login failed';
        
        // Handle email verification requirement
        if (action.payload?.requiresVerification) {
          state.user.email = action.payload.email;
        }
      })
      
      // Logout
      .addCase(logoutUser.fulfilled, (state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.token = null;
        state.user = initialState.user;
        state.error = null;
        state.registerSuccess = false;
        state.loginSuccess = false;
        state.emailVerificationSent = false;
        state.phoneVerificationSent = false;
      })
      
      // Get Current User
      .addCase(getCurrentUser.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = {
          ...state.user,
          ...action.payload.data,
        };
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.user = initialState.user;
        state.error = action.payload || 'Failed to fetch user';
      })
      
      // Verify Email
      .addCase(verifyEmail.fulfilled, (state, action) => {
        state.user.email_verified = true;
        state.error = null;
      })
      .addCase(verifyEmail.rejected, (state, action) => {
        state.error = action.payload || 'Email verification failed';
      })
      
      // Verify Phone
      .addCase(verifyPhone.fulfilled, (state, action) => {
        state.user.phone_verified = true;
        state.phoneVerificationSent = false;
        state.error = null;
      })
      .addCase(verifyPhone.rejected, (state, action) => {
        state.error = action.payload || 'Phone verification failed';
      })
      
      // Request Phone Verification
      .addCase(requestPhoneVerification.fulfilled, (state) => {
        state.phoneVerificationSent = true;
        state.error = null;
      })
      .addCase(requestPhoneVerification.rejected, (state, action) => {
        state.phoneVerificationSent = false;
        state.error = action.payload || 'Failed to send verification code';
      })
      
      // Resend Verification Email
      .addCase(resendVerificationEmail.fulfilled, (state) => {
        state.emailVerificationSent = true;
        state.error = null;
      })
      .addCase(resendVerificationEmail.rejected, (state, action) => {
        state.error = action.payload || 'Failed to resend verification email';
      })
      
      // Forgot Password
      .addCase(forgotPassword.fulfilled, (state) => {
        state.error = null;
      })
      .addCase(forgotPassword.rejected, (state, action) => {
        state.error = action.payload || 'Failed to send reset email';
      })
      
      // Reset Password
      .addCase(resetPassword.fulfilled, (state) => {
        state.error = null;
      })
      .addCase(resetPassword.rejected, (state, action) => {
        state.error = action.payload || 'Password reset failed';
      })
      
      // Update Profile
      .addCase(updateProfile.fulfilled, (state, action) => {
        state.user = {
          ...state.user,
          ...action.payload.data,
        };
        state.error = null;
      })
      .addCase(updateProfile.rejected, (state, action) => {
        state.error = action.payload || 'Profile update failed';
      });
  },
});

// Export actions
export const {
  clearErrors,
  clearSuccessFlags,
  setAuthenticated,
  restoreSession,
  updateUserField,
} = authSlice.actions;

// Export selectors
export const selectAuth = (state) => state.auth;
export const selectUser = (state) => state.auth.user;
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectIsLoading = (state) => state.auth.isLoading;
export const selectError = (state) => state.auth.error;
export const selectToken = (state) => state.auth.token;
export const selectEmailVerified = (state) => state.auth.user.email_verified;
export const selectPhoneVerified = (state) => state.auth.user.phone_verified;

// Export reducer
export default authSlice.reducer;