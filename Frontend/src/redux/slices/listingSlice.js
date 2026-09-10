import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// ---------------- Thunks ----------------

// List + search + filter + paginate
export const fetchListings = createAsyncThunk(
  'listings/fetchAll',
  async (params = {}, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/api/listings', { params });
      return data; // { items, total, page, page_size }
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const fetchListingById = createAsyncThunk(
  'listings/fetchOne',
  async (id, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get(`/api/listings/${id}`);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const createListing = createAsyncThunk(
  'listings/create',
  async (payload, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/api/listings', payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const updateListing = createAsyncThunk(
  'listings/update',
  async ({ id, payload }, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.put(`/api/listings/${id}`, payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const deleteListing = createAsyncThunk(
  'listings/delete',
  async (id, { rejectWithValue }) => {
    try {
      await axiosInstance.delete(`/api/listings/${id}`);
      return id;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const uploadListingMedia = createAsyncThunk(
  'listings/uploadMedia',
  async ({ listingId, file }, { rejectWithValue }) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await axiosInstance.post(
        `/api/listings/${listingId}/media`,
        formData
      );
      return data; // media record with file_url
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const fetchMapListings = createAsyncThunk(
  'listings/fetchMap',
  async (params = {}, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/api/listings/map', { params });
      return data; // array of markers
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const predictPrice = createAsyncThunk(
  'listings/predictPrice',
  async (payload, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/api/predict-price', payload);
      return data; // { recommended_price, price_band, explanation }
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// ---------------- Slice ----------------

const initialState = {
  items: [],
  total: 0,
  page: 1,
  pageSize: 12,
  filters: {
    q: '',
    category_id: '',
    material_name: '',
    min_price: '',
    max_price: '',
    min_quantity: '',
    availability_status: 'Active',
    sort_by: 'created_at',
    sort_dir: 'desc',
  },
  current: null,
  mapMarkers: [],
  prediction: null,
  isLoading: false,
  isSaving: false,
  isUploading: false,
  error: null,
};

const listingSlice = createSlice({
  name: 'listings',
  initialState,
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
      state.page = 1;
    },
    resetFilters: (state) => {
      state.filters = initialState.filters;
      state.page = 1;
    },
    setPage: (state, action) => {
      state.page = action.payload;
    },
    clearCurrent: (state) => {
      state.current = null;
    },
    clearPrediction: (state) => {
      state.prediction = null;
    },
    clearListingError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchListings
      .addCase(fetchListings.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchListings.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload.items || action.payload;
        state.total = action.payload.total ?? (action.payload.items?.length || 0);
        state.page = action.payload.page ?? state.page;
        state.pageSize = action.payload.page_size ?? state.pageSize;
      })
      .addCase(fetchListings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Failed to load listings';
      })

      // fetchListingById
      .addCase(fetchListingById.pending, (state) => {
        state.isLoading = true;
        state.error = null;
        state.current = null;
      })
      .addCase(fetchListingById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.current = action.payload;
      })
      .addCase(fetchListingById.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Failed to load listing';
      })

      // createListing
      .addCase(createListing.pending, (state) => {
        state.isSaving = true;
        state.error = null;
      })
      .addCase(createListing.fulfilled, (state, action) => {
        state.isSaving = false;
        state.items.unshift(action.payload);
      })
      .addCase(createListing.rejected, (state, action) => {
        state.isSaving = false;
        state.error = action.payload?.detail || 'Failed to create listing';
      })

      // updateListing
      .addCase(updateListing.pending, (state) => {
        state.isSaving = true;
        state.error = null;
      })
      .addCase(updateListing.fulfilled, (state, action) => {
        state.isSaving = false;
        const idx = state.items.findIndex(
          (l) => l.listing_id === action.payload.listing_id
        );
        if (idx !== -1) state.items[idx] = action.payload;
        state.current = action.payload;
      })
      .addCase(updateListing.rejected, (state, action) => {
        state.isSaving = false;
        state.error = action.payload?.detail || 'Failed to update listing';
      })

      // deleteListing
      .addCase(deleteListing.fulfilled, (state, action) => {
        state.items = state.items.filter((l) => l.listing_id !== action.payload);
      })

      // upload media
      .addCase(uploadListingMedia.pending, (state) => {
        state.isUploading = true;
        state.error = null;
      })
      .addCase(uploadListingMedia.fulfilled, (state, action) => {
        state.isUploading = false;
        if (state.current) {
          state.current.media = [...(state.current.media || []), action.payload];
        }
      })
      .addCase(uploadListingMedia.rejected, (state, action) => {
        state.isUploading = false;
        state.error = action.payload?.detail || 'Upload failed';
      })

      // map
      .addCase(fetchMapListings.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchMapListings.fulfilled, (state, action) => {
        state.isLoading = false;
        state.mapMarkers = action.payload.items || action.payload;
      })
      .addCase(fetchMapListings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Failed to load map data';
      })

      // prediction
      .addCase(predictPrice.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(predictPrice.fulfilled, (state, action) => {
        state.isLoading = false;
        state.prediction = action.payload;
      })
      .addCase(predictPrice.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.detail || 'Prediction failed';
      });
  },
});

export const {
  setFilters,
  resetFilters,
  setPage,
  clearCurrent,
  clearPrediction,
  clearListingError,
} = listingSlice.actions;

export default listingSlice.reducer;