import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { fetchMyListings } from '../../redux/slices/listingSlice';
import ListingCard from '../../components/listing/ListingCard';

const MyListings = () => {
  const dispatch = useDispatch();
  const { myItems, isLoading, error } = useSelector((s) => s.listings);

  useEffect(() => {
    dispatch(fetchMyListings({ page: 1, size: 50 }));
  }, [dispatch]);

  return (
    <div className="my-listings-page">
      <div className="page-header">
        <h2>My Listings</h2>
        <Link to="/seller/listings/new" className="btn-primary">+ New Listing</Link>
      </div>

      {error && <div className="error-message">{error}</div>}

      {isLoading ? (
        <div className="loading">Loading…</div>
      ) : myItems.length === 0 ? (
        <div className="empty-state">
          You haven't created any listings yet. Click <strong>+ New Listing</strong> to get started.
        </div>
      ) : (
        <div className="listings-grid">
          {myItems.map((l) => (
            <ListingCard key={l.id} listing={l} sellerMode />
          ))}
        </div>
      )}
    </div>
  );
};

export default MyListings;