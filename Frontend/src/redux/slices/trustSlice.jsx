import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

export const fetchTrustScore = createAsyncThunk(
  'trust/fetch',
  async (listingId, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get(`/trust/${listingId}`);
      return { listingId, data };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

const trustSlice = createSlice({
  name: 'trust',
  initialState: {
    byListing: {},       // { [listingId]: trustResult }
    isLoading: false,
    error: null,
  },
  reducers: {
    clearTrustError: (s) => { s.error = null; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTrustScore.pending, (s) => { s.isLoading = true; s.error = null; })
      .addCase(fetchTrustScore.fulfilled, (s, a) => {
        s.isLoading = false;
        s.byListing[a.payload.listingId] = a.payload.data;
      })
      .addCase(fetchTrustScore.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Trust score unavailable';
      });
  },
});

export const { clearTrustError } = trustSlice.actions;
export default trustSlice.reducer;