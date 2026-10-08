import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// Read persisted org id (per user)
const ORG_KEY = (userId) => `scraplink_org_${userId || 'anon'}`;

export const createOrganization = createAsyncThunk(
  'org/create',
  async ({ payload, userId }, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.post('/organizations/', payload);
      // Persist so we know the user has an org on next login
      if (userId) localStorage.setItem(ORG_KEY(userId), data.id);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const fetchOrganizationById = createAsyncThunk(
  'org/fetchById',
  async (orgId, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get(`/organizations/${orgId}`);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const updateOrganization = createAsyncThunk(
  'org/update',
  async ({ orgId, payload }, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.put(`/organizations/${orgId}`, payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

const organizationSlice = createSlice({
  name: 'organization',
  initialState: {
    current: null,
    isLoading: false,
    isSaving: false,
    error: null,
  },
  reducers: {
    clearOrgError: (s) => { s.error = null; },
    clearCurrentOrg: (s) => { s.current = null; },
    // Called on login so the header/sidebar can react
    hydrateFromStorage: (s, a) => {
      if (!a.payload) return;
      s.current = { id: a.payload, name: null };
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(createOrganization.pending, (s) => {
        s.isSaving = true;
        s.error = null;
      })
      .addCase(createOrganization.fulfilled, (s, a) => {
        s.isSaving = false;
        s.current = a.payload;
      })
      .addCase(createOrganization.rejected, (s, a) => {
        s.isSaving = false;
        s.error = extractDetail(a.payload) || 'Failed to create organization';
      })

      .addCase(fetchOrganizationById.pending, (s) => { s.isLoading = true; })
      .addCase(fetchOrganizationById.fulfilled, (s, a) => {
        s.isLoading = false;
        s.current = a.payload;
      })
      .addCase(fetchOrganizationById.rejected, (s, a) => {
        s.isLoading = false;
        s.error = extractDetail(a.payload) || 'Failed to load organization';
      })

      .addCase(updateOrganization.pending, (s) => { s.isSaving = true; s.error = null; })
      .addCase(updateOrganization.fulfilled, (s, a) => {
        s.isSaving = false;
        s.current = a.payload;
      })
      .addCase(updateOrganization.rejected, (s, a) => {
        s.isSaving = false;
        s.error = extractDetail(a.payload) || 'Failed to update organization';
      });
  },
});

function extractDetail(payload) {
  if (!payload) return null;
  if (typeof payload === 'string') return payload;
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
  }
  return null;
}

export const {
  clearOrgError,
  clearCurrentOrg,
  hydrateFromStorage,
} = organizationSlice.actions;

export const orgStorageKey = ORG_KEY;
export default organizationSlice.reducer;