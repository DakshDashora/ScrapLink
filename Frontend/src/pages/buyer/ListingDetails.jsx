import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchListingById, clearCurrent } from '../../redux/slices/listingSlice';
import PriceRecommendation from '../../components/listing/PriceRecommendation';
import MapView from '../../components/map/MapView';

const ListingDetails = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { current, isLoading, error } = useSelector((s) => s.listings);

  useEffect(() => {
    dispatch(fetchListingById(id));
    return () => dispatch(clearCurrent());
  }, [dispatch, id]);

  if (isLoading || !current) return <div className="loading">Loading…</div>;
  if (error) return <div className="error-message">{error}</div>;

  const media = current.media || [];
  const primary = media.find((m) => m.is_primary) || media[0];
  const hasCoords =
    current.location?.latitude && current.location?.longitude;

  return (
    <div className="listing-details">
      <div className="listing-details-header">
        <h2>{current.material_name}</h2>
        <span className={`status-badge status-${(current.availability_status || '').toLowerCase()}`}>
          {current.availability_status}
        </span>
      </div>

      <div className="listing-details-grid">
        <div className="gallery">
          {primary ? (
            <img src={primary.file_url} alt={current.material_name} className="primary-image" />
          ) : (
            <div className="no-image">No images available</div>
          )}
          {media.length > 1 && (
            <div className="thumbnails">
              {media.filter((m) => m.id !== primary?.id).map((m) => (
                <img key={m.id} src={m.file_url} alt="thumbnail" />
              ))}
            </div>
          )}
        </div>

        <div className="info">
          <p><strong>Seller:</strong> {current.seller_org_name}</p>
          {current.category_name && <p><strong>Category:</strong> {current.category_name}</p>}
          <p><strong>Quantity:</strong> {Number(current.quantity).toLocaleString()} {current.unit}</p>
          {current.grade && <p><strong>Grade:</strong> {current.grade}</p>}
          <p><strong>Asking Price:</strong> {current.asking_price ? `₹ ${Number(current.asking_price).toLocaleString()}` : 'On request'}</p>
          <p><strong>Location:</strong> {current.location?.city || current.location?.state || '—'}</p>
          {current.description && <p className="description">{current.description}</p>}

          <PriceRecommendation listing={current} />
        </div>
      </div>

      {hasCoords && (
        <div className="map-section">
          <h3>Pickup Location</h3>
          <MapView
            markers={[{
              ...current,
              latitude: current.location.latitude,
              longitude: current.location.longitude,
            }]}
            height="350px"
          />
        </div>
      )}
    </div>
  );
};

export default ListingDetails;