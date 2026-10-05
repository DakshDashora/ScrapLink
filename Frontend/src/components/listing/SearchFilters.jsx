import { useDispatch, useSelector } from 'react-redux';
import { useEffect } from 'react';
import { setFilters, resetFilters } from '../../features/listings/listingSlice';
import { fetchCategories } from '../../features/categories/categorySlice';

const SearchFilters = () => {
  const dispatch = useDispatch();
  const filters = useSelector((s) => s.listings.filters);
  const categories = useSelector((s) => s.categories.items);

  useEffect(() => {
    if (categories.length === 0) dispatch(fetchCategories());
  }, [dispatch, categories.length]);

  const update = (k, v) => dispatch(setFilters({ [k]: v }));

  return (
    <div className="search-filters">
      <input
        type="text"
        placeholder="Search material..."
        value={filters.material_name}
        onChange={(e) => update('material_name', e.target.value)}
      />

      <select
        value={filters.category_id}
        onChange={(e) => update('category_id', e.target.value)}
      >
        <option value="">All Categories</option>
        {categories.map((c) => (
          <option key={c.id || c.category_id} value={c.id || c.category_id}>
            {c.name}
          </option>
        ))}
      </select>

      <input
        type="number"
        placeholder="Min ₹"
        value={filters.min_price}
        onChange={(e) => update('min_price', e.target.value)}
      />
      <input
        type="number"
        placeholder="Max ₹"
        value={filters.max_price}
        onChange={(e) => update('max_price', e.target.value)}
      />
      <input
        type="number"
        placeholder="Min Qty"
        value={filters.min_quantity}
        onChange={(e) => update('min_quantity', e.target.value)}
      />

      <select value={filters.unit} onChange={(e) => update('unit', e.target.value)}>
        <option value="">Any Unit</option>
        <option value="kg">kg</option>
        <option value="tonne">tonne</option>
        <option value="unit">unit</option>
        <option value="meter">meter</option>
        <option value="liter">liter</option>
      </select>

      <input
        type="text"
        placeholder="City"
        value={filters.city}
        onChange={(e) => update('city', e.target.value)}
      />

      <select
        value={`${filters.sort_by}:${filters.sort_order}`}
        onChange={(e) => {
          const [by, order] = e.target.value.split(':');
          dispatch(setFilters({ sort_by: by, sort_order: order }));
        }}
      >
        <option value="created_at:desc">Newest First</option>
        <option value="created_at:asc">Oldest First</option>
        <option value="asking_price:asc">Price: Low → High</option>
        <option value="asking_price:desc">Price: High → Low</option>
        <option value="quantity:desc">Quantity: High → Low</option>
      </select>

      <button className="btn-reset" onClick={() => dispatch(resetFilters())}>
        Reset
      </button>
    </div>
  );
};

export default SearchFilters;