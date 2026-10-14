import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { createRequirement, updateRequirement } from '../../redux/slices/requirementSlice';
import { fetchCategories } from '../../redux/slices/categorySlice';

const empty = {
  category_id: '',
  material_name: '',
  grade: '',
  description: '',
  quantity: '',
  unit: 'kg',
  target_price: '',
  location: {
    address: '',
    city: '',
    state: '',
    latitude: '',
    longitude: '',
  },
};

const RequirementForm = ({ initial, isEdit = false }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isSaving, error } = useSelector((s) => s.requirements);
  const categories = useSelector((s) => s.categories.items);

  const [form, setForm] = useState(() => ({
    ...empty,
    ...initial,
    location: { ...empty.location, ...(initial?.location || {}) },
  }));

  useEffect(() => {
    if (categories.length === 0) dispatch(fetchCategories());
  }, [dispatch, categories.length]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const setLoc = (k, v) =>
    setForm((f) => ({ ...f, location: { ...f.location, [k]: v } }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      category_id: form.category_id || null,
      material_name: form.material_name,
      grade: form.grade,
      description: form.description,
      quantity: Number(form.quantity),
      unit: form.unit,
      target_price: form.target_price ? Number(form.target_price) : null,
      location: {
        address: form.location.address,
        city: form.location.city,
        state: form.location.state,
        latitude: form.location.latitude ? Number(form.location.latitude) : null,
        longitude: form.location.longitude ? Number(form.location.longitude) : null,
      },
    };

    const action = isEdit
      ? updateRequirement({ id: initial.id, payload })
      : createRequirement(payload);

    const res = await dispatch(action).unwrap().catch(() => null);
    if (res) navigate(`/buyer/requirements/${res.id}`);
  };

  return (
    <form className="listing-form" onSubmit={handleSubmit}>
      <h2>{isEdit ? 'Edit Requirement' : 'Create Requirement'}</h2>
      <p className="form-intro">
        Describe the scrap you're looking for. Our AI will match your
        requirement with active listings.
      </p>

      <div className="form-grid">
        <label>
          Material Name *
          <input
            type="text"
            value={form.material_name}
            onChange={(e) => set('material_name', e.target.value)}
            placeholder="e.g. Copper Wire, HMS Steel"
            required
          />
        </label>

        <label>
          Category
          <select
            value={form.category_id}
            onChange={(e) => set('category_id', e.target.value)}
          >
            <option value="">-- Any category --</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>

        <label>
          Grade / Quality
          <input
            type="text"
            value={form.grade}
            onChange={(e) => set('grade', e.target.value)}
            placeholder="e.g. 99.5% Pure, Grade A"
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
          <select value={form.unit} onChange={(e) => set('unit', e.target.value)}>
            <option value="kg">kg</option>
            <option value="tonne">tonne</option>
            <option value="unit">unit</option>
            <option value="meter">meter</option>
            <option value="liter">liter</option>
          </select>
        </label>

        <label>
          Target Price (₹) — optional
          <input
            type="number"
            min="0"
            step="any"
            value={form.target_price}
            onChange={(e) => set('target_price', e.target.value)}
          />
        </label>
      </div>

      <label className="full">
        Description *
        <textarea
          rows="4"
          value={form.description}
          onChange={(e) => set('description', e.target.value)}
          placeholder="Include specifics: purity, dimensions, expected use, delivery timelines…"
          required
        />
      </label>

      <fieldset>
        <legend>Preferred Delivery Location (optional)</legend>
        <div className="form-grid">
          <label>City
            <input type="text" value={form.location.city}
              onChange={(e) => setLoc('city', e.target.value)} />
          </label>
          <label>State
            <input type="text" value={form.location.state}
              onChange={(e) => setLoc('state', e.target.value)} />
          </label>
        </div>
      </fieldset>

      {error && <div className="error-message">{error}</div>}

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={isSaving}>
          {isSaving ? 'Saving…' : isEdit ? 'Update Requirement' : 'Create Requirement'}
        </button>
        <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>
          Cancel
        </button>
      </div>
    </form>
  );
};

export default RequirementForm;