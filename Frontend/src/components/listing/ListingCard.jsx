import { Link } from 'react-router-dom';

const PLACEHOLDER =
  'data:image/svg+xml;base64,' +
  btoa(
    `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200">
      <rect width="100%" height="100%" fill="#f1f5f9"/>
      <path d="M120 85 L150 115 L180 85" stroke="#94a3b8" stroke-width="3" fill="none"/>
      <text x="50%" y="65%" font-family="sans-serif" font-size="13" fill="#64748b" text-anchor="middle">No Image</text>
    </svg>`
  );

const ListingCard = ({ listing, sellerMode = false }) => {
  const media = listing.media || [];
  const primary = media.find((m) => m.is_primary) || media[0];
  const image = primary?.file_url || PLACEHOLDER;

  const loc =
    listing.location?.city ||
    listing.location?.state ||
    listing.location?.address ||
    'Location N/A';

  const price = listing.asking_price
    ? `₹ ${Number(listing.asking_price).toLocaleString()}`
    : 'Price on request';

  const linkTo = sellerMode
    ? `/seller/listings/${listing.id}/edit`
    : `/marketplace/${listing.id}`;

  const statusClass = (listing.availability_status || 'active').toLowerCase();

  return (
    <Link to={linkTo} className="listing-card modern-card">
      <div className="listing-card-image">
        <img src={image} alt={listing.material_name} loading="lazy" />
        <span className={`status-badge status-${statusClass}`}>
          {listing.availability_status || 'Active'}
        </span>
      </div>
      <div className="listing-card-body">
        <div className="listing-card-header">
          <h3 className="listing-title">{listing.material_name}</h3>
        </div>

        <div className="listing-meta-row">
          <span className="qty-badge">
            📦 {Number(listing.quantity).toLocaleString()} {listing.unit || 'kg'}
          </span>
          {listing.grade && <span className="grade-badge">Grade: {listing.grade}</span>}
        </div>

        <div className="listing-price-row">
          <span className="price-tag">{price}</span>
        </div>

        <div className="listing-footer">
          <span className="location-tag">📍 {loc}</span>
          {sellerMode && (
            <span className="seller-action-hint">Edit Listing →</span>
          )}
        </div>
      </div>
    </Link>
  );
};

export default ListingCard;
