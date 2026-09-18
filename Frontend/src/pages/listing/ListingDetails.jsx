import { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchListingById,
  deleteListing,
  clearCurrent,
} from '../features/listings/listingSlice';
import PriceRecommendation from '../components/listings/PriceRecommendation';
import MapView from '../../components/map/MapView';

const ListingDetails = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { current, isLoading, error } = useSelector((s) => s.listings);
  const authUser = useSelector((s) => s.auth.user);

  useEffect(() => {
    dispatch(fetchListingById(id));
    return () => dispatch(clearCurrent());
  }, [dispatch, id]);

  const handleDelete = async () => {
    if (!window.confirm('Delete this listing?')) return;
    const res = await dispatch(deleteListing(id)).unwrap().catch(() => null);
    if (res) navigate('/my-listings');
  };

  if (isLoading || !current) return <div className="loading">Loading…</div>;
  if (error) return <div className="error-message">{error}</div>;

  const isOwner = authUser?.user_id === current.seller_user_id;
  const images = current.media?.map((m) => m.file_url) || [];
  const hasCoords =
    current.location?.latitude && current.location?.longitude;

  return (
    <div className="listing-details">
      <div className="listing-details-header">
        <h2>{current.material_name}</h2>
        {isOwner && (
          <div className="owner-actions">
            <Link to={`/listings/${current.listing_id}/edit`} className="btn-secondary">
              Edit
            </Link>
            <button onClick={handleDelete} className="btn-danger">Delete</button>
          </div>
        )}
      </div>

      <div className="listing-details-grid">
        <div className="gallery">
          {images.length ? (
            images.map((url, i) => <img key={i} src={url} alt={`media-${i}`} />)
          ) : (
            <div className="no-image">No images</div>
          )}
        </div>

        <div className="info">
          <p><strong>Quantity:</strong> {current.quantity} {current.unit}</p>
          {current.grade && <p><strong>Grade:</strong> {current.grade}</p>}
          <p>
            <strong>Asking Price:</strong>{' '}
            {current.asking_price
              ? `₹ ${Number(current.asking_price).toLocaleString()}`
              : 'Price on request'}
          </p>
          <p><strong>Status:</strong> {current.availability_status}</p>
          <p><strong>Location:</strong> {current.location?.city || '—'}</p>
          {current.description && (
            <p className="description">{current.description}</p>
          )}

          <PriceRecommendation listing={current} />
        </div>
      </div>

      {hasCoords && (
        <div className="map-section">
          <h3>Pickup Location</h3>
          <MapView
            markers={[
              {
                ...current,
                location: {
                  latitude: current.location.latitude,
                  longitude: current.location.longitude,
                },
              },
            ]}
            height="350px"
          />
        </div>
      )}
    </div>
  );
};

export default ListingDetails;