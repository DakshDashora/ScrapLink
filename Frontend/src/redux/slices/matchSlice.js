import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// Refresh and fetch ranked matches for a requirement
export const refreshMatches = createAsyncThunk(
  'matches/refresh',
  async (requirementId, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post(
        `/matches/${requirementId}/refresh`
      );
      return { requirementId, data };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const fetchMatches = createAsyncThunk(
  'matches/fetch',
  async (requirementId, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get(`/matches/${requirementId}`);
      return { requirementId, data };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// ---------- Slice ----------

function unwrap(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.matches)) return data.matches;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

const initialState = {
  byRequirement: {},       // { [requirementId]: [match, ...] }
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
      // Refresh
      .addCase(refreshMatches.pending, (s) => {
        s.isRefreshing = true;
        s.error = null;
      })
      .addCase(refreshMatches.fulfilled, (s, a) => {
        s.isRefreshing = false;
        s.byRequirement[a.payload.requirementId] = unwrap(a.payload.data);
        s.lastRefreshedAt = new Date().toISOString();
      })
      .addCase(refreshMatches.rejected, (s, a) => {
        s.isRefreshing = false;
        s.error = a.payload?.detail || 'Failed to refresh matches';
      })

      // Fetch
      .addCase(fetchMatches.pending, (s) => {
        s.isLoading = true;
        s.error = null;
      })
      .addCase(fetchMatches.fulfilled, (s, a) => {
        s.isLoading = false;
        s.byRequirement[a.payload.requirementId] = unwrap(a.payload.data);
      })
      .addCase(fetchMatches.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to fetch matches';
      });
  },
});

export const { clearMatchesFor, clearMatchError } = matchSlice.actions;
export default matchSlice.reducer;