import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  uploadListingMedia,
  deleteListingMedia,
  setPrimaryMedia,
} from '../../features/listings/listingSlice';

const ImageUploader = ({ listingId, media = [] }) => {
  const dispatch = useDispatch();
  const { isUploading, error } = useSelector((s) => s.listings);
  const [file, setFile] = useState(null);
  const [isPrimary, setIsPrimary] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    await dispatch(uploadListingMedia({ listingId, file, isPrimary })).unwrap().catch(() => {});
    setFile(null);
    setIsPrimary(false);
  };

  return (
    <div className="image-uploader">
      <div className="upload-controls">
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={isPrimary}
            onChange={(e) => setIsPrimary(e.target.checked)}
          />
          Set as primary image
        </label>
        <button
          className="btn-primary"
          onClick={handleUpload}
          disabled={!file || isUploading}
        >
          {isUploading ? 'Uploading…' : 'Upload'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="existing-images">
        {media.map((m) => (
          <div key={m.id} className={`media-item ${m.is_primary ? 'is-primary' : ''}`}>
            <img src={m.file_url} alt="listing" />
            {m.is_primary && <span className="primary-tag">Primary</span>}
            <div className="media-actions">
              {!m.is_primary && (
                <button
                  onClick={() =>
                    dispatch(setPrimaryMedia({ listingId, mediaId: m.id }))
                  }
                >
                  Set Primary
                </button>
              )}
              <button
                className="btn-danger-small"
                onClick={() =>
                  dispatch(deleteListingMedia({ listingId, mediaId: m.id }))
                }
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ImageUploader;