import { Link } from 'react-router-dom';
import MatchScoreBadge from './MatchScoreBadge';
import MatchReasonList from './MatchReasonList';

const MatchCard = ({ match }) => {
  // Backend may return the listing inline or under .listing
  const listing = match.listing || match;
  const similarity =
    match.similarity_score ??
    match.score ??
    match.similarity ??
    null;

  const image =
    listing.media?.[0]?.file_url ||
    listing.primary_image_url ||
    null;

  const loc =
    listing.location?.city ||
    listing.location?.state ||
    '';

  return (
    <div className="match-card">
      <div className="match-card-media">
        {image ? (
          <img src={image} alt={listing.material_name} />
        ) : (
          <div className="no-image-small">No image</div>
        )}
        <MatchScoreBadge score={similarity} label="Semantic match" />
      </div>

      <div className="match-card-body">
        <h4>{listing.material_name}</h4>
        {listing.grade && <p className="muted">Grade: {listing.grade}</p>}
        {listing.quantity && (
          <p className="muted">
            {Number(listing.quantity).toLocaleString()} {listing.unit}
          </p>
        )}
        {listing.asking_price && (
          <p className="price">₹ {Number(listing.asking_price).toLocaleString()}</p>
        )}
        {loc && <p className="location">📍 {loc}</p>}

        <MatchReasonList reasons={match.explanation || match.reasons} />

        <Link to={`/marketplace/${listing.id}`} className="btn-secondary small-btn">
          View Listing
        </Link>
      </div>
    </div>
  );
};

export default MatchCard;