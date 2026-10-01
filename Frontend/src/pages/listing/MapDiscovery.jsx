import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchMapListings } from '../../redux/slices/listingSlice';
import MapView from '../../components/map/MapView';
import ListingCard from '../../components/listing/ListingCard';

const MapDiscovery = () => {
  const dispatch = useDispatch();
  const { mapMarkers, isLoading } = useSelector((s) => s.listings);

  useEffect(() => {
    dispatch(fetchMapListings({ availability_status: 'Active' }));
  }, [dispatch]);

  return (
    <div className="map-page">
      <h2>Map Discovery</h2>
      {isLoading && <div className="loading">Loading map…</div>}
      <MapView markers={mapMarkers} height="500px" />
      <div className="map-list-preview">
        {mapMarkers.slice(0, 6).map((m) => (
          <ListingCard key={m.listing_id} listing={m} />
        ))}
      </div>
    </div>
  );
};

export default MapDiscovery;