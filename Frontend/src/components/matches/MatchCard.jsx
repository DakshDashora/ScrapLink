import { Link } from 'react-router-dom';
import MatchScoreBadge from './MatchScoreBadge';

const MatchCard = ({ match }) => {
  const title = match.material_name || match.listing_name || 'Scrap Material';
  const category = match.category && match.category !== 'Unknown' ? match.category : null;
  const price = match.asking_price ? `₹ ${Number(match.asking_price).toLocaleString()}` : 'Price on request';
  const qty = match.quantity ? `${Number(match.quantity).toLocaleString()} ${match.unit || 'kg'}` : '';
  const loc = match.location?.city || match.location?.state || 'Location N/A';

  return (
    <div className="match-card">
      <div className="match-card-body">
        <div className="match-card-header">
          <h4 className="match-card-title">{title}</h4>
          <MatchScoreBadge 
            score={match.similarity_score} 
            label={match.match_quality || 'Match'} 
          />
        </div>

        <div className="match-details">
          {category && <p className="muted"><span className="detail-label">Category:</span> {category}</p>}
          {match.grade && <p className="muted"><span className="detail-label">Grade:</span> {match.grade}</p>}
          {qty && <p className="muted"><span className="detail-label">Qty:</span> {qty}</p>}
          <p className="price"><span className="detail-label">Price:</span> <strong>{price}</strong></p>
          <p className="location">📍 {loc}</p>
        </div>

        <div className="constraint-badge">
          {match.hard_constraints_passed ? (
            <span className="badge-constraint pass">✅ Constraints Met</span>
          ) : (
            <span className="badge-constraint partial">⚠️ Partial Match</span>
          )}
        </div>

        <Link 
          to={`/marketplace/${match.listing_id}`} 
          className="btn-primary small-btn match-card-action"
        >
          View Listing →
        </Link>
      </div>
    </div>
  );
};

export default MatchCard;
