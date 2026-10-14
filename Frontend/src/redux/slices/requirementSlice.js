import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// ---------- Thunks ----------

export const fetchRequirements = createAsyncThunk(
  'requirements/fetchAll',
  async (params = {}, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/requirements/', { params });
      // Handle { items: [...] } | { requirements: [...] } | array
      const items = Array.isArray(data)
        ? data
        : data.items || data.requirements || [];
      return {
        items,
        total: data.total ?? items.length,
        page: data.page ?? 1,
        size: data.size ?? 20,
        pages: data.pages ?? 1,
      };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const fetchRequirementById = createAsyncThunk(
  'requirements/fetchOne',
  async (id, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get(`/requirements/${id}`);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const createRequirement = createAsyncThunk(
  'requirements/create',
  async (payload, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/requirements/', payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const updateRequirement = createAsyncThunk(
  'requirements/update',
  async ({ id, payload }, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.put(`/requirements/${id}`, payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const deactivateRequirement = createAsyncThunk(
  'requirements/deactivate',
  async (id, { rejectWithValue }) => {
    try {
      await axiosInstance.delete(`/requirements/${id}`);
      return id;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// ---------- Slice ----------

const initialState = {
  items: [],
  total: 0,
  page: 1,
  size: 20,
  pages: 1,
  current: null,
  isLoading: false,
  isSaving: false,
  error: null,
};

const requirementSlice = createSlice({
  name: 'requirements',
  initialState,
  reducers: {
    clearCurrentRequirement: (s) => { s.current = null; },
    clearRequirementError: (s) => { s.error = null; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRequirements.pending, (s) => { s.isLoading = true; s.error = null; })
      .addCase(fetchRequirements.fulfilled, (s, a) => {
        s.isLoading = false;
        s.items = a.payload.items;
        s.total = a.payload.total;
        s.page = a.payload.page;
        s.size = a.payload.size;
        s.pages = a.payload.pages;
      })
      .addCase(fetchRequirements.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load requirements';
      })

      .addCase(fetchRequirementById.pending, (s) => {
        s.isLoading = true; s.error = null; s.current = null;
      })
      .addCase(fetchRequirementById.fulfilled, (s, a) => {
        s.isLoading = false; s.current = a.payload;
      })
      .addCase(fetchRequirementById.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load requirement';
      })

      .addCase(createRequirement.pending, (s) => { s.isSaving = true; s.error = null; })
      .addCase(createRequirement.fulfilled, (s, a) => {
        s.isSaving = false;
        s.items.unshift(a.payload);
      })
      .addCase(createRequirement.rejected, (s, a) => {
        s.isSaving = false;
        s.error = a.payload?.detail || 'Failed to create requirement';
      })

      .addCase(updateRequirement.pending, (s) => { s.isSaving = true; s.error = null; })
      .addCase(updateRequirement.fulfilled, (s, a) => {
        s.isSaving = false;
        s.current = a.payload;
        const idx = s.items.findIndex((r) => r.id === a.payload.id);
        if (idx !== -1) s.items[idx] = a.payload;
      })
      .addCase(updateRequirement.rejected, (s, a) => {
        s.isSaving = false;
        s.error = a.payload?.detail || 'Failed to update requirement';
      })

      .addCase(deactivateRequirement.fulfilled, (s, a) => {
        s.items = s.items.map((r) =>
          r.id === a.payload ? { ...r, status: 'Closed' } : r
        );
      });
  },
});

export const {
  clearCurrentRequirement,
  clearRequirementError,
} = requirementSlice.actions;

export default requirementSlice.reducer;