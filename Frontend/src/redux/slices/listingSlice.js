import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// ---------- Thunks ----------

// Public listing search
export const fetchListings = createAsyncThunk(
  'listings/fetchAll',
  async (params = {}, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/listings/', { params });
      return data; // { items, total, page, size, pages }
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Seller's own listings
export const fetchMyListings = createAsyncThunk(
  'listings/fetchMine',
  async ({ page = 1, size = 20, status } = {}, { rejectWithValue }) => {
    try {
      const params = { page, size };
      if (status) params.status = status;
      const { data } = await axiosInstance.get('/listings/my-listings', { params });
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const fetchListingById = createAsyncThunk(
  'listings/fetchOne',
  async (id, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get(`/listings/${id}`);
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
      const { data } = await axiosInstance.post('/listings/', payload);
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
      const { data } = await axiosInstance.put(`/listings/${id}`, payload);
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
      await axiosInstance.delete(`/listings/${id}`);
      return id;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Media: multipart with `file` and optional `is_primary`
export const uploadListingMedia = createAsyncThunk(
  'listings/uploadMedia',
  async ({ listingId, file, isPrimary = false }, { rejectWithValue }) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('is_primary', isPrimary ? 'true' : 'false');
      const { data } = await axiosInstance.post(
        `/listings/${listingId}/media`,
        formData
      );
      return data.media || data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const deleteListingMedia = createAsyncThunk(
  'listings/deleteMedia',
  async ({ listingId, mediaId }, { rejectWithValue }) => {
    try {
      await axiosInstance.delete(`/listings/${listingId}/media/${mediaId}`);
      return { listingId, mediaId };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const setPrimaryMedia = createAsyncThunk(
  'listings/setPrimaryMedia',
  async ({ listingId, mediaId }, { rejectWithValue }) => {
    try {
      await axiosInstance.put(`/listings/${listingId}/media/${mediaId}/primary`);
      return { listingId, mediaId };
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Map markers
export const fetchMapListings = createAsyncThunk(
  'listings/fetchMap',
  async (params = {}, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/listings/map', { params });
      // Response may be a raw array or { items: [...] }
      return Array.isArray(data) ? data : data.items || [];
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// Optional price prediction (see Sprint 2 plan). Adjust path to match your ML service.
export const predictPrice = createAsyncThunk(
  'listings/predictPrice',
  async (payload, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/listings/predict-price', payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

// ---------- Slice ----------

const initialState = {
  items: [],
  myItems: [],
  total: 0,
  myTotal: 0,
  page: 1,
  size: 12,
  pages: 1,
  filters: {
    material_name: '',
    category_id: '',
    min_price: '',
    max_price: '',
    min_quantity: '',
    max_quantity: '',
    unit: '',
    status: 'Active',
    city: '',
    state: '',
    sort_by: 'created_at',
    sort_order: 'desc',
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
    setFilters: (s, a) => { s.filters = { ...s.filters, ...a.payload }; s.page = 1; },
    resetFilters: (s) => { s.filters = initialState.filters; s.page = 1; },
    setPage: (s, a) => { s.page = a.payload; },
    clearCurrent: (s) => { s.current = null; },
    clearPrediction: (s) => { s.prediction = null; },
    clearListingError: (s) => { s.error = null; },
  },
  extraReducers: (builder) => {
    builder
      // fetchListings
      .addCase(fetchListings.pending, (s) => { s.isLoading = true; s.error = null; })
      .addCase(fetchListings.fulfilled, (s, a) => {
        s.isLoading = false;
        s.items = a.payload.items || [];
        s.total = a.payload.total ?? 0;
        s.page = a.payload.page ?? 1;
        s.size = a.payload.size ?? s.size;
        s.pages = a.payload.pages ?? 1;
      })
      .addCase(fetchListings.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load listings';
      })

      // fetchMyListings
      .addCase(fetchMyListings.pending, (s) => { s.isLoading = true; s.error = null; })
      .addCase(fetchMyListings.fulfilled, (s, a) => {
        s.isLoading = false;
        s.myItems = a.payload.items || [];
        s.myTotal = a.payload.total ?? 0;
      })
      .addCase(fetchMyListings.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load your listings';
      })

      // fetchListingById
      .addCase(fetchListingById.pending, (s) => { s.isLoading = true; s.error = null; s.current = null; })
      .addCase(fetchListingById.fulfilled, (s, a) => { s.isLoading = false; s.current = a.payload; })
      .addCase(fetchListingById.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load listing';
      })

      // createListing
      .addCase(createListing.pending, (s) => { s.isSaving = true; s.error = null; })
      .addCase(createListing.fulfilled, (s, a) => { s.isSaving = false; s.current = a.payload; })
      .addCase(createListing.rejected, (s, a) => {
        s.isSaving = false;
        s.error = a.payload?.detail || 'Failed to create listing';
      })

      // updateListing
      .addCase(updateListing.pending, (s) => { s.isSaving = true; s.error = null; })
      .addCase(updateListing.fulfilled, (s, a) => {
        s.isSaving = false;
        s.current = a.payload;
        const idx = s.myItems.findIndex((l) => l.id === a.payload.id);
        if (idx !== -1) s.myItems[idx] = a.payload;
      })
      .addCase(updateListing.rejected, (s, a) => {
        s.isSaving = false;
        s.error = a.payload?.detail || 'Failed to update listing';
      })

      // deleteListing
      .addCase(deleteListing.fulfilled, (s, a) => {
        s.myItems = s.myItems.filter((l) => l.id !== a.payload);
        s.items = s.items.filter((l) => l.id !== a.payload);
      })

      // uploadListingMedia
      .addCase(uploadListingMedia.pending, (s) => { s.isUploading = true; s.error = null; })
      .addCase(uploadListingMedia.fulfilled, (s, a) => {
        s.isUploading = false;
        if (s.current) s.current.media = [...(s.current.media || []), a.payload];
      })
      .addCase(uploadListingMedia.rejected, (s, a) => {
        s.isUploading = false;
        s.error = a.payload?.detail || 'Upload failed';
      })

      // delete media
      .addCase(deleteListingMedia.fulfilled, (s, a) => {
        if (s.current) {
          s.current.media = (s.current.media || []).filter((m) => m.id !== a.payload.mediaId);
        }
      })

      // set primary
      .addCase(setPrimaryMedia.fulfilled, (s, a) => {
        if (s.current?.media) {
          s.current.media = s.current.media.map((m) => ({
            ...m,
            is_primary: m.id === a.payload.mediaId,
          }));
        }
      })

      // map
      .addCase(fetchMapListings.pending, (s) => { s.isLoading = true; })
      .addCase(fetchMapListings.fulfilled, (s, a) => { s.isLoading = false; s.mapMarkers = a.payload; })
      .addCase(fetchMapListings.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load map data';
      })

      // prediction
      .addCase(predictPrice.pending, (s) => { s.isLoading = true; s.error = null; })
      .addCase(predictPrice.fulfilled, (s, a) => { s.isLoading = false; s.prediction = a.payload; })
      .addCase(predictPrice.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Price prediction unavailable';
      });
  },
});

export const {
  setFilters, resetFilters, setPage, clearCurrent, clearPrediction, clearListingError,
} = listingSlice.actions;
export default listingSlice.reducer;