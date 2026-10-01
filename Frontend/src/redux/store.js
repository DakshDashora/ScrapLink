import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../redux/slices/authSlices';
import listingReducer from '../redux/slices/listingSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    listings: listingReducer,
  },
});