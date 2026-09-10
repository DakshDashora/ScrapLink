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

const ListingCard = ({ listing }) => {
  const image = listing.media?.[0]?.file_url || PLACEHOLDER;
  const locationText =
    listing.location?.city ||
    listing.location?.address ||
    listing.location?.state ||
    'Location N/A';

  return (
    <Link to={`/marketplace/${listing.listing_id}`} className="listing-card">
      <div className="listing-card-image">
        <img src={image} alt={listing.material_name} />
        <span className={`status-badge status-${listing.availability_status?.toLowerCase()}`}>
          {listing.availability_status}
        </span>
      </div>
      <div className="listing-card-body">
        <h3>{listing.material_name}</h3>
        {listing.grade && <p className="grade">Grade: {listing.grade}</p>}
        <p className="quantity">
          {listing.quantity} {listing.unit}
        </p>
        <p className="price">
          {listing.asking_price
            ? `₹ ${Number(listing.asking_price).toLocaleString()}`
            : 'Price on request'}
        </p>
        <p className="location">📍 {locationText}</p>
      </div>
    </Link>
  );
};

export default ListingCard;