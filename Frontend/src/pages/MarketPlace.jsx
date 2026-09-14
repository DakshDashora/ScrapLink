import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchListings } from '../features/listings/listingSlice';
import SearchFilters from '../components/listings/SearchFilters';
import ListingCard from '../components/listings/ListingCard';
import Pagination from '../components/listings/Pagination';

const Marketplace = () => {
  const dispatch = useDispatch();
  const { items, total, page, pageSize, filters, isLoading, error } = useSelector(
    (s) => s.listings
  );

  useEffect(() => {
    dispatch(fetchListings({ ...filters, page, page_size: pageSize }));
  }, [dispatch, filters, page, pageSize]);

  const handlePage = (p) =>
    dispatch({ type: 'listings/setPageFromOutside', payload: p });

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
            {items.map((l) => (
              <ListingCard key={l.listing_id} listing={l} />
            ))}
          </div>
          <PaginationWithDispatch
            page={page}
            total={total}
            pageSize={pageSize}
            onPageChange={handlePage}
          />
        </>
      )}
    </div>
  );
};

// helper so setPage action gets imported
import { setPage } from '../features/listings/listingSlice';

const PaginationWithDispatch = ({ page, total, pageSize, onPageChange }) => {
  const dispatch = useDispatch();
  return (
    <Pagination
      page={page}
      total={total}
      pageSize={pageSize}
      onPageChange={(p) => dispatch(setPage(p))}
    />
  );
};

export default Marketplace;