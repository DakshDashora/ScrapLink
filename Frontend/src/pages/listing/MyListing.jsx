import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { fetchListings } from '../features/listings/listingSlice';
import ListingCard from '../components/listings/ListingCard';

const MyListings = () => {
  const dispatch = useDispatch();
  const { items, isLoading } = useSelector((s) => s.listings);

  useEffect(() => {
    dispatch(fetchListings({ mine: true, page_size: 100 }));
  }, [dispatch]);

  return (
    <div className="my-listings-page">
      <div className="page-header">
        <h2>My Listings</h2>
        <Link to="/listings/new" className="btn-primary">+ New Listing</Link>
      </div>

      {isLoading ? (
        <div className="loading">Loading…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">You haven't created any listings yet.</div>
      ) : (
        <div className="listings-grid">
          {items.map((l) => <ListingCard key={l.listing_id} listing={l} />)}
        </div>
      )}
    </div>
  );
};

export default MyListings;