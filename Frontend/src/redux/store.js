import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../redux/slices/authSlices';

export const store = configureStore({
  reducer: {
    auth: authReducer,
  },
});