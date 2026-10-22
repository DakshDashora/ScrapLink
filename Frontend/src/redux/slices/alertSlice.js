import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

export const fetchMatchAlerts = createAsyncThunk(
  'alerts/fetch',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/match-alerts');
      const items = Array.isArray(data)
        ? data
        : data.alerts || data.items || [];
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
      await axiosInstance.put(`/match-alerts/${alertId}/read`);
      return alertId;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const markAllAlertsRead = createAsyncThunk(
  'alerts/markAllRead',
  async (_, { rejectWithValue }) => {
    try {
      await axiosInstance.put('/match-alerts/read-all');
      return true;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
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

export const { clearAlertsError } = alertSlice.actions;
export default alertSlice.reducer;