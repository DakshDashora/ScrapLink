import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchListingById, clearCurrent } from '../../redux/slices/listingSlice';
import ListingForm from '../../components/listing/ListingForm';
import ImageUploader from '../../components/listing/ImageUploader';

const EditListing = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { current, isLoading } = useSelector((s) => s.listings);

  useEffect(() => {
    dispatch(fetchListingById(id));
    return () => dispatch(clearCurrent());
  }, [dispatch, id]);

  if (isLoading || !current) return <div className="loading">Loading…</div>;

  return (
    <div className="page-container">
      <ListingForm initial={current} isEdit />
      <div className="upload-section">
        <h3>Listing Images</h3>
        <ImageUploader listingId={current.id} media={current.media} />
      </div>
    </div>
  );
};

export default EditListing;