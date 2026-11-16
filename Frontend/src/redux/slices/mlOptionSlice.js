import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../api/axiosConfig';

// Bulletproof parser
const parseOptions = (rawData, type) => {
  console.log(`[ML Options] Raw ${type} response:`, rawData);

  let data = rawData;
  // 1. Parse stringified JSON if the backend double-encoded it
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data);
    } catch {
      // If it's just a raw comma-separated string: "Steel,Copper"
      return data.split(',').map((s) => s.trim());
    }
  }

  // 2. Unwrap common dictionary shapes
  if (Array.isArray(data)) return data;
  if (data?.items && Array.isArray(data.items)) return data.items;
  if (data?.materials && Array.isArray(data.materials)) return data.materials;
  if (data?.scrap_types && Array.isArray(data.scrap_types)) return data.scrap_types;
  if (data?.data && Array.isArray(data.data)) return data.data;

  // 3. If it's an array of objects, map to string
  if (Array.isArray(data)) {
    return data.map((item) => 
      typeof item === 'object' ? (item.name || item.value || item.id) : item
    );
  }

  console.warn(`[ML Options] Could not parse ${type} shape. Returning empty array.`);
  return [];
};

export const fetchMlMaterials = createAsyncThunk(
  'mlOptions/fetchMaterials',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/api/ml-options/materials');
      return parseOptions(data, 'materials');
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const fetchMlScrapTypes = createAsyncThunk(
  'mlOptions/fetchScrapTypes',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await axiosInstance.get('/api/ml-options/scrap-types');
      return parseOptions(data, 'scrap-types');
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

const mlOptionSlice = createSlice({
  name: 'mlOptions',
  initialState: {
    materials: [],
    scrapTypes: [],
    isLoading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchMlMaterials.pending, (s) => { s.isLoading = true; })
      .addCase(fetchMlMaterials.fulfilled, (s, a) => {
        s.isLoading = false;
        // Ensure array of strings
        s.materials = a.payload.map(String); 
      })
      .addCase(fetchMlMaterials.rejected, (s, a) => {
        s.isLoading = false;
        s.error = a.payload?.detail || 'Failed to load materials';
      })
      
      .addCase(fetchMlScrapTypes.fulfilled, (s, a) => {
        s.scrapTypes = a.payload.map(String);
      });
  },
});

export default mlOptionSlice.reducer;