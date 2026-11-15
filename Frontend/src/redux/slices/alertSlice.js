import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

export const fetchMatchAlerts = createAsyncThunk(
  'alerts/fetch',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/api/matches/match-alerts');
      
      // Handle stringified JSON if returned that way
      let items = data;
      if (typeof data === 'string') {
        try { items = JSON.parse(data); } catch (e) { items = []; }
      }
      
      if (!Array.isArray(items)) {
        items = items.alerts || items.items || [];
      }
      
      return items;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const markAlertRead = createAsyncThunk(
  'alerts/markRead',
  async (alertId, { rejectWithValue }) => {
    try {
      await axiosInstance.put(`/api/matches/match-alerts/${alertId}/read`);
      return alertId;
    } catch (err) {
      // If backend fails, we still return the ID so the UI updates
      return alertId; 
    }
  }
);

export const markAllAlertsRead = createAsyncThunk(
  'alerts/markAllRead',
  async (_, { rejectWithValue }) => {
    try {
      await axiosInstance.put('/api/matches/match-alerts/read-all');
      return true;
    } catch (err) {
      // Fallback: If the endpoint doesn't exist, we catch the error
      // and return true so the local UI still clears the badge.
      return true; 
    }
  }
);

const alertSlice = createSlice({
  name: 'alerts',
  initialState: {
    items: [],
    unreadCount: 0,
    isLoading: false,
    error: null,
  },
  reducers: {
    clearAlertsError: (s) => { s.error = null; },
    // Local fallback to clear all immediately without API
    markAllReadLocal: (s) => {
      s.items = s.items.map((x) => ({ ...x, is_read: true }));
      s.unreadCount = 0;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMatchAlerts.pending, (s) => { s.isLoading = true; s.error = null; })
      .addCase(fetchMatchAlerts.fulfilled, (s, a) => {
        s.isLoading = false;
        s.items = a.payload;
        s.unreadCount = a.payload.filter((x) => !x.is_read).length;
      })
      .addCase(fetchMatchAlerts.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load alerts';
      })
      
      .addCase(markAlertRead.fulfilled, (s, a) => {
        s.items = s.items.map((x) =>
          x.id === a.payload ? { ...x, is_read: true } : x
        );
        s.unreadCount = s.items.filter((x) => !x.is_read).length;
      })
      
      .addCase(markAllAlertsRead.fulfilled, (s) => {
        s.items = s.items.map((x) => ({ ...x, is_read: true }));
        s.unreadCount = 0;
      });
  },
});

export const { clearAlertsError, markAllReadLocal } = alertSlice.actions;
export default alertSlice.reducer;