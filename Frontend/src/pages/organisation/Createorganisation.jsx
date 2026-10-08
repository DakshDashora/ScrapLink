import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { createOrganization, clearOrgError } from '../../redux/slices/organisationSlice';

const empty = {
  name: '',
  business_type: 'Company',
  industry_type: '',
  description: '',
  gstin: '',
  location: {
    address: '',
    city: '',
    state: '',
    latitude: '',
    longitude: '',
  },
};

const CreateOrganization = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isSaving, error } = useSelector((s) => s.organization);
  const user = useSelector((s) => s.auth.user);

  const [form, setForm] = useState(empty);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const setLoc = (k, v) =>
    setForm((f) => ({ ...f, location: { ...f.location, [k]: v } }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      name: form.name.trim(),
      business_type: form.business_type,
      industry_type: form.industry_type.trim(),
      description: form.description.trim(),
      gstin: form.gstin.trim() || null,
      location: {
        address: form.location.address,
        city: form.location.city,
        state: form.location.state,
        latitude: form.location.latitude ? Number(form.location.latitude) : null,
        longitude: form.location.longitude ? Number(form.location.longitude) : null,
      },
    };

    const res = await dispatch(
      createOrganization({ payload, userId: user?.user_id })
    ).unwrap().catch(() => null);

    if (res) navigate('/seller/listings/new');
  };

  return (
    <div className="page-container">
      <form className="listing-form" onSubmit={handleSubmit}>
        <h2>Create Organization</h2>
        <p className="form-intro">
          Sellers must belong to an organization before listing scrap.
          You can update these details later.
        </p>

        <div className="form-grid">
          <label>
            Business / Industry Name *
            <input
              type="text"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              required
            />
          </label>

          <label>
            Business Type *
            <select
              value={form.business_type}
              onChange={(e) => set('business_type', e.target.value)}
              required
            >
              <option value="Company">Company</option>
              <option value="Partnership">Partnership</option>
              <option value="Proprietorship">Proprietorship</option>
              <option value="Other">Other</option>
            </select>
          </label>

          <label>
            Industry Type
            <input
              type="text"
              placeholder="e.g. Manufacturing, Recycling"
              value={form.industry_type}
              onChange={(e) => set('industry_type', e.target.value)}
            />
          </label>

          <label>
            GSTIN (if applicable)
            <input
              type="text"
              placeholder="15-character GST number"
              value={form.gstin}
              onChange={(e) => set('gstin', e.target.value.toUpperCase())}
              maxLength={15}
            />
          </label>
        </div>

        <label className="full">
          Description
          <textarea
            rows="3"
            value={form.description}
            onChange={(e) => set('description', e.target.value)}
          />
        </label>

        <fieldset>
          <legend>Location</legend>
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
            {isSaving ? 'Creating…' : 'Create Organization'}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => { dispatch(clearOrgError()); navigate(-1); }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateOrganization;