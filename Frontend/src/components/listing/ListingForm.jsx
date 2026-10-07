import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { createListing, updateListing } from '../../redux/slices/listingSlice';

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

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const setLoc = (k, v) => setForm((f) => ({ ...f, location: { ...f.location, [k]: v } }));

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
      navigate(isEdit ? `/marketplace/${res.id}` : `/seller/listings/${res.id}/edit`);
    }
  };

  return (
    <form className="listing-form" onSubmit={handleSubmit}>
      <h2>{isEdit ? 'Edit Listing' : 'Create Listing'}</h2>

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
          >
            <option value="">-- Select --</option>
            {categories.map((c) => (
              <option key={c.id || c.category_id} value={c.id || c.category_id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Grade / Quality
          <input type="text" value={form.grade} onChange={(e) => set('grade', e.target.value)} />
        </label>

        <label>
          Quantity *
          <input
            type="number" min="0" step="any"
            value={form.quantity}
            onChange={(e) => set('quantity', e.target.value)}
            required
          />
        </label>

        <label>
          Unit
          <select value={form.unit} onChange={(e) => set('unit', e.target.value)}>
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
            type="number" min="0" step="any"
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

      <fieldset>
        <legend>Pickup Location</legend>
        <div className="form-grid">
          <label>Address
            <input type="text" value={form.location.address}
              onChange={(e) => setLoc('address', e.target.value)} />
          </label>
          <label>City
            <input type="text" value={form.location.city}
              onChange={(e) => setLoc('city', e.target.value)} />
          </label>
          <label>State
            <input type="text" value={form.location.state}
              onChange={(e) => setLoc('state', e.target.value)} />
          </label>
          <label>Latitude
            <input type="number" step="any" value={form.location.latitude}
              onChange={(e) => setLoc('latitude', e.target.value)} />
          </label>
          <label>Longitude
            <input type="number" step="any" value={form.location.longitude}
              onChange={(e) => setLoc('longitude', e.target.value)} />
          </label>
        </div>
      </fieldset>

      {error && <div className="error-message">{error}</div>}

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={isSaving}>
          {isSaving ? 'Saving…' : isEdit ? 'Update Listing' : 'Create Listing'}
        </button>
        <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>
          Cancel
        </button>
      </div>
    </form>
  );
};

export default ListingForm;