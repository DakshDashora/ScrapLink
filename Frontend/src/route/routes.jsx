import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { getCurrentUser } from '../redux/slices/authSlices';

import ProtectedRoute from './ProtectedRoute';
import DashboardLayout from '../components/Layout/DashboardLayout';

import Landing from '../pages/Landing';
import Login from '../components/auth/Login';
import Register from '../components/auth/Register';
import EmailVerification from '../components/auth/EmailVerification';
import PhoneVerification from '../components/auth/PhoneVerification';
import ForgotPassword from '../components/auth/ForgotPassword';
import ResetPassword from '../components/auth/ResetPassword';
import Dashboard from '../pages/Dashboard';
import Marketplace from '../pages/Marketplace';
import ListingDetails from '../pages/ListingDetails';
import CreateListing from '../pages/CreateListing';
import EditListing from '../pages/EditListing';
import MyListings from '../pages/MyListings';
import MapDiscovery from '../pages/MapDiscovery';

import '../styles/global.css';
import '../styles/listings.css';

function RoutePage() {
  const dispatch = useDispatch();

  useEffect(() => {
    // If token exists, fetch user on app load
    const token = localStorage.getItem('accessToken');
    if (token) {
      dispatch(getCurrentUser());
    }
  }, [dispatch]);

  return (
    
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-email" element={<EmailVerification />} />
        <Route path="/verify-phone" element={<PhoneVerification />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
           <Route path="marketplace" element={<Marketplace />} />
          <Route path="marketplace/map" element={<MapDiscovery />} />
          <Route path="marketplace/:id" element={<ListingDetails />} />
          <Route path="listings/new" element={<CreateListing />} />
          <Route path="listings/:id/edit" element={<EditListing />} />
          <Route path="my-listings" element={<MyListings />} />
        </Route>
        
      </Routes>
    
  );
}

export default RoutePage;