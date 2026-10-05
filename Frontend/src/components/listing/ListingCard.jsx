import { Link } from 'react-router-dom';

const PLACEHOLDER =
  'data:image/svg+xml;base64,' +
  btoa(
    `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">
      <rect width="100%" height="100%" fill="#e2e8f0"/>
      <text x="50%" y="50%" font-size="14" fill="#64748b"
        text-anchor="middle" dy=".3em">No Image</text>
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

  return (
    <Link to={linkTo} className="listing-card">
      <div className="listing-card-image">
        <img src={image} alt={listing.material_name} />
        <span className={`status-badge status-${(listing.availability_status || 'active').toLowerCase()}`}>
          {listing.availability_status}
        </span>
      </div>
      <div className="listing-card-body">
        <h3>{listing.material_name}</h3>
        {listing.grade && <p className="grade">Grade: {listing.grade}</p>}
        <p className="quantity">
          {Number(listing.quantity).toLocaleString()} {listing.unit}
        </p>
        <p className="price">{price}</p>
        <p className="location">📍 {loc}</p>
        {sellerMode && (
          <p className="seller-org">{listing.seller_org_name}</p>
        )}
      </div>
    </Link>
  );
};

export default ListingCard;