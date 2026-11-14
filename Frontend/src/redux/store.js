import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../redux/slices/authSlices';
import listingReducer from '../redux/slices/listingSlice';
import categoryReducer from '../redux/slices/categorySlice';
import organizationReducer from '../redux/slices/organisationSlice';

import requirementReducer from '../redux/slices/requirementSlice';
import matchReducer from '../redux/slices/matchSlice';
import alertReducer from '../redux/slices/alertSlice';
import trustReducer from '../redux/slices/trustSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    listings: listingReducer,
    categories: categoryReducer,
    organization: organizationReducer,
    requirements: requirementReducer,
    matches: matchReducer,
    alerts: alertReducer,
    trust: trustReducer,
  },
}); 