import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchListingById } from '../features/listings/listingSlice';
import ListingForm from '../components/listings/ListingForm';
import ImageUploader from '../components/listings/ImageUploader';

const EditListing = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { current, isLoading } = useSelector((s) => s.listings);

  useEffect(() => {
    dispatch(fetchListingById(id));
  }, [dispatch, id]);

  if (isLoading || !current) return <div className="loading">Loading…</div>;

  return (
    <div className="page-container">
      <ListingForm initial={current} isEdit />
      <div className="upload-section">
        <h3>Listing Images</h3>
        <ImageUploader listingId={current.listing_id} />
        <div className="existing-images">
          {current.media?.map((m) => (
            <img key={m.media_id} src={m.file_url} alt="listing" />
          ))}
        </div>
      </div>
    </div>
  );
};

export default EditListing;