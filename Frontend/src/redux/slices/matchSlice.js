import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// Trigger ML matching and refresh
export const refreshMatches = createAsyncThunk(
  'matches/refresh',
  async (requirementId, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post(`/api/matches/${requirementId}/refresh`);
      return { requirementId, data };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Fetch already saved matches
export const fetchMatches = createAsyncThunk(
  'matches/fetch',
  async (requirementId, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get(`/api/matches/${requirementId}`);
      return { requirementId, data };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

const initialState = {
  // We store the entire response object now (top_matches, status, disclaimer, etc.)
  byRequirement: {}, 
  isLoading: false,
  isRefreshing: false,
  error: null,
  lastRefreshedAt: null,
};

const matchSlice = createSlice({
  name: 'matches',
  initialState,
  reducers: {
    clearMatchesFor: (s, a) => {
      delete s.byRequirement[a.payload];
    },
    clearMatchError: (s) => { s.error = null; },
  },
  extraReducers: (builder) => {
    builder
      // Refresh Matches
      .addCase(refreshMatches.pending, (s) => {
        s.isRefreshing = true;
        s.error = null;
      })
      .addCase(refreshMatches.fulfilled, (s, a) => {
        s.isRefreshing = false;
        s.byRequirement[a.payload.requirementId] = a.payload.data; // Store full object
        s.lastRefreshedAt = new Date().toISOString();
      })
      .addCase(refreshMatches.rejected, (s, a) => {
        s.isRefreshing = false;
        s.error = a.payload?.detail || 'Failed to refresh matches';
      })

      // Fetch Matches
      .addCase(fetchMatches.pending, (s) => {
        s.isLoading = true;
        s.error = null;
      })
      .addCase(fetchMatches.fulfilled, (s, a) => {
        s.isLoading = false;
        s.byRequirement[a.payload.requirementId] = a.payload.data; // Store full object
      })
      .addCase(fetchMatches.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to fetch matches';
      });
  },
});

export const { clearMatchesFor, clearMatchError } = matchSlice.actions;
export default matchSlice.reducer;