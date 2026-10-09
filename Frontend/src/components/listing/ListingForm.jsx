import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';

import { createListing, updateListing } from '../../redux/slices/listingSlice';
import { fetchCategories } from '../../redux/slices/categorySlice';
import { geocodeAddress, reverseGeocode } from '../../utils/geocode';
import { useGeolocation } from '../../utils/useGeolocation';
import LocationPicker from './LocationPicker';

const empty = {
  category_id: '',
  material_name: '',
  grade: '',
  description: '',
  quantity: '',
  unit: 'kg',
  asking_price: '',
  availability_status: 'Active',
  location: {
    address: '',
    city: '',
    state: '',
    latitude: '',
    longitude: '',
  },
};

const ListingForm = ({ initial, isEdit = false }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { isSaving, error } = useSelector((s) => s.listings);
  const categories = useSelector((s) => s.categories.items);

  const [form, setForm] = useState(() => ({
    ...empty,
    ...initial,
    location: { ...empty.location, ...(initial?.location || {}) },
  }));

  const [geocoding, setGeocoding] = useState(false);
  const [geoError, setGeoError] = useState('');

  const [reversing, setReversing] = useState(false);
  const [autoFillNote, setAutoFillNote] = useState('');

  const { requestPosition, loading: gpsLoading, error: gpsError } = useGeolocation();

  // ---------------- Category fetch ----------------
  useEffect(() => {
    if (categories.length === 0) dispatch(fetchCategories());
  }, [dispatch, categories.length]);

  // ---------------- Helpers ----------------
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const setLoc = (k, v) =>
    setForm((f) => ({ ...f, location: { ...f.location, [k]: v } }));

  // ---------------- Geocode from address ----------------
  const handleFindOnMap = async () => {
    setGeoError('');
    setGeocoding(true);
    try {
      const { latitude, longitude } = await geocodeAddress({
        address: form.location.address,
        city: form.location.city,
        state: form.location.state,
      });
      setForm((f) => ({
        ...f,
        location: { ...f.location, latitude, longitude },
      }));
    } catch (err) {
      setGeoError(err.message || 'Could not find location');
    } finally {
      setGeocoding(false);
    }
  };

  // ---------------- GPS: Use My Current Location ----------------
  const handleUseMyLocation = async () => {
    try {
      setAutoFillNote('');
      setGeoError('');
      const { latitude, longitude } = await requestPosition();

      // 1. Drop pin immediately
      setLoc('latitude', latitude);
      setLoc('longitude', longitude);

      // 2. Reverse-geocode to fill city/state/address
      setReversing(true);
      const { city, state, address } = await reverseGeocode(latitude, longitude);
      setForm((f) => ({
        ...f,
        location: {
          ...f.location,
          latitude,
          longitude,
          city: city || f.location.city,
          state: state || f.location.state,
          address: address || f.location.address,
        },
      }));
      setAutoFillNote('Location filled from GPS. You can adjust it manually.');
    } catch {
      // gpsError already captured by hook
    } finally {
      setReversing(false);
    }
  };

  // ---------------- Submit ----------------
  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      category_id: form.category_id,
      material_name: form.material_name,
      grade: form.grade,
      description: form.description,
      quantity: Number(form.quantity),
      unit: form.unit,
      asking_price: form.asking_price ? Number(form.asking_price) : null,
      location: {
        address: form.location.address,
        city: form.location.city,
        state: form.location.state,
        latitude: form.location.latitude ? Number(form.location.latitude) : null,
        longitude: form.location.longitude ? Number(form.location.longitude) : null,
      },
    };
    if (isEdit) payload.availability_status = form.availability_status;

    const action = isEdit
      ? updateListing({ id: initial.id, payload })
      : createListing(payload);

    const res = await dispatch(action).unwrap().catch(() => null);
    if (res) {
      navigate(isEdit ? `/seller/listings/${res.id}/edit` : `/seller/listings`);
    }
  };

  const hasOrgError =
    typeof error === 'string' && error.toLowerCase().includes('organization');

  return (
    <form className="listing-form" onSubmit={handleSubmit}>
      <h2>{isEdit ? 'Edit Listing' : 'Create Listing'}</h2>

      {/* ---------------- Core fields ---------------- */}
      <div className="form-grid">
        <label>
          Material Name *
          <input
            type="text"
            value={form.material_name}
            onChange={(e) => set('material_name', e.target.value)}
            required
          />
        </label>

        <label>
          Category *
          <select
            value={form.category_id}
            onChange={(e) => set('category_id', e.target.value)}
            required
            disabled={categories.length === 0}
          >
            <option value="">
              {categories.length === 0 ? 'Loading categories…' : '-- Select --'}
            </option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Grade / Quality
          <input
            type="text"
            value={form.grade}
            onChange={(e) => set('grade', e.target.value)}
          />
        </label>

        <label>
          Quantity *
          <input
            type="number"
            min="0"
            step="any"
            value={form.quantity}
            onChange={(e) => set('quantity', e.target.value)}
            required
          />
        </label>

        <label>
          Unit
          <select
            value={form.unit}
            onChange={(e) => set('unit', e.target.value)}
          >
            <option value="kg">kg</option>
            <option value="tonne">tonne</option>
            <option value="unit">unit</option>
            <option value="meter">meter</option>
            <option value="liter">liter</option>
          </select>
        </label>

        <label>
          Asking Price (₹)
          <input
            type="number"
            min="0"
            step="any"
            value={form.asking_price}
            onChange={(e) => set('asking_price', e.target.value)}
          />
        </label>

        {isEdit && (
          <label>
            Availability
            <select
              value={form.availability_status}
              onChange={(e) => set('availability_status', e.target.value)}
            >
              <option value="Active">Active</option>
              <option value="Reserved">Reserved</option>
              <option value="Sold">Sold</option>
              <option value="Closed">Closed</option>
            </select>
          </label>
        )}
      </div>

      <label className="full">
        Description
        <textarea
          rows="4"
          value={form.description}
          onChange={(e) => set('description', e.target.value)}
        />
      </label>

      {/* ---------------- Location block ---------------- */}
      <fieldset>
        <legend>Pickup Location</legend>

        <div className="geo-topbar">
          <button
            type="button"
            className="btn-primary use-location-btn"
            onClick={handleUseMyLocation}
            disabled={gpsLoading || reversing}
          >
            {gpsLoading
              ? '📡 Getting location…'
              : reversing
              ? '🌐 Filling address…'
              : '📍 Use My Current Location'}
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={handleFindOnMap}
            disabled={geocoding || (!form.location.city && !form.location.state)}
          >
            {geocoding ? 'Locating…' : '🔎 Find Address on Map'}
          </button>

          {autoFillNote && <span className="auto-fill-note">{autoFillNote}</span>}
        </div>

        {gpsError && <div className="error-message">{gpsError}</div>}
        {geoError && <div className="error-message">{geoError}</div>}

        <div className="form-grid">
          <label>
            Address
            <input
              type="text"
              placeholder="Plot no, street, area"
              value={form.location.address}
              onChange={(e) => setLoc('address', e.target.value)}
            />
          </label>
          <label>
            City
            <input
              type="text"
              placeholder="e.g. Jaipur"
              value={form.location.city}
              onChange={(e) => setLoc('city', e.target.value)}
            />
          </label>
          <label>
            State
            <input
              type="text"
              placeholder="e.g. Rajasthan"
              value={form.location.state}
              onChange={(e) => setLoc('state', e.target.value)}
            />
          </label>
        </div>

        {form.location.latitude && form.location.longitude && (
          <div className="coords-badge">
            📌 Lat: {form.location.latitude}, Lng: {form.location.longitude}
          </div>
        )}

        <div className="map-wrapper">
          <LocationPicker
            latitude={form.location.latitude}
            longitude={form.location.longitude}
            onChange={(lat, lng) => {
              setLoc('latitude', lat);
              setLoc('longitude', lng);
            }}
          />
        </div>

        <details className="advanced-coords">
          <summary>Advanced: enter coordinates manually</summary>
          <div className="form-grid">
            <label>
              Latitude
              <input
                type="number"
                step="any"
                value={form.location.latitude}
                onChange={(e) => setLoc('latitude', e.target.value)}
              />
            </label>
            <label>
              Longitude
              <input
                type="number"
                step="any"
                value={form.location.longitude}
                onChange={(e) => setLoc('longitude', e.target.value)}
              />
            </label>
          </div>
        </details>
      </fieldset>

      {/* ---------------- Error ---------------- */}
      {error && (
        <div className="error-message">
          {error}
          {hasOrgError && (
            <>
              {' '}
              <Link to="/organization/new" className="inline-link">
                → Create Organization
              </Link>
            </>
          )}
        </div>
      )}

      {/* ---------------- Actions ---------------- */}
      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={isSaving}>
          {isSaving ? 'Saving…' : isEdit ? 'Update Listing' : 'Create Listing'}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => navigate(-1)}
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

export default ListingForm;