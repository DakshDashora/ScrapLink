import { useDispatch, useSelector } from 'react-redux';
import { setFilters, resetFilters } from '../../redux/slices/listingSlice';

const SearchFilters = ({ categories = [] }) => {
  const dispatch = useDispatch();
  const filters = useSelector((s) => s.listings.filters);

  const update = (key, value) => dispatch(setFilters({ [key]: value }));

  return (
    <div className="search-filters">
      <input
        type="text"
        placeholder="Search material..."
        value={filters.q}
        onChange={(e) => update('q', e.target.value)}
      />

      <select
        value={filters.category_id}
        onChange={(e) => update('category_id', e.target.value)}
      >
        <option value="">All Categories</option>
        {categories.map((c) => (
          <option key={c.category_id} value={c.category_id}>
            {c.name}
          </option>
        ))}
      </select>

      <input
        type="number"
        placeholder="Min Price"
        value={filters.min_price}
        onChange={(e) => update('min_price', e.target.value)}
      />
      <input
        type="number"
        placeholder="Max Price"
        value={filters.max_price}
        onChange={(e) => update('max_price', e.target.value)}
      />
      <input
        type="number"
        placeholder="Min Qty"
        value={filters.min_quantity}
        onChange={(e) => update('min_quantity', e.target.value)}
      />

      <select
        value={filters.availability_status}
        onChange={(e) => update('availability_status', e.target.value)}
      >
        <option value="Active">Active</option>
        <option value="">All Statuses</option>
        <option value="Reserved">Reserved</option>
        <option value="Sold">Sold</option>
        <option value="Closed">Closed</option>
      </select>

      <select
        value={`${filters.sort_by}:${filters.sort_dir}`}
        onChange={(e) => {
          const [by, dir] = e.target.value.split(':');
          dispatch(setFilters({ sort_by: by, sort_dir: dir }));
        }}
      >
        <option value="created_at:desc">Newest First</option>
        <option value="created_at:asc">Oldest First</option>
        <option value="asking_price:asc">Price: Low → High</option>
        <option value="asking_price:desc">Price: High → Low</option>
        <option value="quantity:desc">Quantity: High → Low</option>
      </select>

      <button onClick={() => dispatch(resetFilters())} className="btn-reset">
        Reset
      </button>
    </div>
  );
};

export default SearchFilters;