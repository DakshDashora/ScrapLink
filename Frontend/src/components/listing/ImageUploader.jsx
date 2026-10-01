import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { uploadListingMedia } from '../../redux/slices/listingSlice';

const ImageUploader = ({ listingId }) => {
  const dispatch = useDispatch();
  const { isUploading, error } = useSelector((s) => s.listings);
  const [previews, setPreviews] = useState([]);

  const handleFiles = async (files) => {
    for (const file of files) {
      const url = URL.createObjectURL(file);
      setPreviews((p) => [...p, { file, url }]);
      // eslint-disable-next-line no-await-in-loop
      await dispatch(uploadListingMedia({ listingId, file }));
    }
  };

  return (
    <div className="image-uploader">
      <label className="upload-drop">
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={(e) => handleFiles(Array.from(e.target.files))}
        />
        <span>{isUploading ? 'Uploading…' : 'Click to upload images'}</span>
      </label>

      {error && <div className="error-message">{error}</div>}

      <div className="previews">
        {previews.map((p, i) => (
          <img key={i} src={p.url} alt={`preview-${i}`} />
        ))}
      </div>
    </div>
  );
};

export default ImageUploader;