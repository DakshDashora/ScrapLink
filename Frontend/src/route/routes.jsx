import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { getCurrentUser } from '../redux/slices/authSlices';

import ProtectedRoute from './ProtectedRoute';
import RoleRoute from './/RoleRoute';
import DashboardLayout from '../components/Layout/DashboardLayout';

import Landing from '../pages/Landing';
import Login from '../components/auth/Login';
import Register from '../components/auth//Register';
import EmailVerification from '../components/auth/EmailVerification';
import PhoneVerification from '../components/auth/PhoneVerification';
import ForgotPassword from '../components/auth/ForgotPassword';
import ResetPassword from '../components/auth/ResetPassword';
import Dashboard from '../pages/Dashboard';

import MyListings from '../pages/seller/MyListing';
import CreateListing from '../pages/seller/CreateListing';
import EditListing from '../pages/seller/EditListing';

import Marketplace from '../pages/buyer/MarketPlace';
import ListingDetails from '../pages/buyer/ListingDetails';
import MapDiscovery from '../pages/buyer/MapDiscovery';
import CreateOrganization from '../pages/organisation/Createorganisation';

import '../styles/global.css';
import '../styles/listing.css';

function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    if (localStorage.getItem('accessToken')) dispatch(getCurrentUser());
  }, [dispatch]);

  return (

    <Routes>
      {/* Public auth */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<EmailVerification />} />
      <Route path="/verify-phone" element={<PhoneVerification />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Protected dashboard shell */}
      <Route path="/" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        <Route path="dashboard" element={<Dashboard />} />

        {/* Seller routes */}
        <Route
          path="seller/listings"
          element={<RoleRoute allow={['Seller', 'Admin']}><MyListings /></RoleRoute>}
        />
        <Route
          path="seller/listings/new"
          element={<RoleRoute allow={['Seller', 'Admin']}><CreateListing /></RoleRoute>}
        />
        <Route
          path="seller/listings/:id/edit"
          element={<RoleRoute allow={['Seller', 'Admin']}><EditListing /></RoleRoute>}
        />

        {/* Buyer routes */}
        <Route
          path="marketplace"
          element={<RoleRoute allow={['Buyer', 'Admin']}><Marketplace /></RoleRoute>}
        />
        <Route
          path="marketplace/map"
          element={<RoleRoute allow={['Buyer', 'Admin']}><MapDiscovery /></RoleRoute>}
        />
        <Route
          path="marketplace/:id"
          element={<RoleRoute allow={['Buyer', 'Admin']}><ListingDetails /></RoleRoute>}
        />
      </Route>
      <Route
        path="organization/new"
        element={
          <RoleRoute allow={['Seller', 'Admin']}>
            <CreateOrganization />
          </RoleRoute>
        }
      />
    </Routes>

  );
}

export default App;