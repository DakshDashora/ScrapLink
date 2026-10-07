import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchListings, setPage } from '../../redux/slices/listingSlice';
import SearchFilters from '../../components/listing/SearchFilters';
import ListingCard from '../../components/listing/ListingCard';
import Pagination from '../../components/listing/Pagination';

const Marketplace = () => {
  const dispatch = useDispatch();
  const { items, page, pages, size, filters, isLoading, error } =
    useSelector((s) => s.listings);

  useEffect(() => {
    const cleanFilters = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    );
    dispatch(fetchListings({ ...cleanFilters, page, size }));
  }, [dispatch, filters, page, size]);

  return (
    <div className="marketplace-page">
      <h2>Marketplace</h2>
      <SearchFilters />
      {error && <div className="error-message">{error}</div>}
      {isLoading ? (
        <div className="loading">Loading listings…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">No listings match your criteria.</div>
      ) : (
        <>
          <div className="listings-grid">
            {items.map((l) => <ListingCard key={l.id} listing={l} />)}
          </div>
          <Pagination page={page} pages={pages} onChange={(p) => dispatch(setPage(p))} />
        </>
      )}
    </div>
  );
};

export default Marketplace;