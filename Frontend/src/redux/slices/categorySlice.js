import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

export const fetchCategories = createAsyncThunk(
  'categories/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/categories/');
      // Backend returns array directly OR { items: [...] }
      const list = Array.isArray(data) ? data : data.items || [];
      return list;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

const categorySlice = createSlice({
  name: 'categories',
  initialState: { items: [], isLoading: false, error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchCategories.pending, (s) => { s.isLoading = true; s.error = null; })
      .addCase(fetchCategories.fulfilled, (s, a) => { s.isLoading = false; s.items = a.payload; })
      .addCase(fetchCategories.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load categories';
      });
  },
});

export default categorySlice.reducer;