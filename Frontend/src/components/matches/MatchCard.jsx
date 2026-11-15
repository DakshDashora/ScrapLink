import { Link } from 'react-router-dom';
import MatchScoreBadge from './MatchScoreBadge';

const MatchCard = ({ match }) => {
  // 'match' is a single object from the top_matches array
  
  // The API returns asking_price and quantity as numbers, but let's be safe
  const price = match.asking_price ? `₹ ${Number(match.asking_price).toLocaleString()}` : 'Price on request';
  const qty = match.quantity ? `${Number(match.quantity).toLocaleString()} ${match.unit}` : '';
  const loc = match.location?.city || match.location?.state || 'Location N/A';

  return (
    <div className="match-card">
      <div className="match-card-body">
        <div className="match-card-header">
          <h4>{match.material_name}</h4>
          <MatchScoreBadge 
            score={match.similarity_score} 
            label={match.match_quality || 'Match'} 
          />
        </div>

        <div className="match-details">
          {match.category && <p className="muted"><strong>Category:</strong> {match.category}</p>}
          {match.grade && <p className="muted"><strong>Grade:</strong> {match.grade}</p>}
          {qty && <p className="muted"><strong>Qty:</strong> {qty}</p>}
          <p className="price"><strong>Price:</strong> {price}</p>
          <p className="location">📍 {loc}</p>
        </div>

        <div className="constraint-badge">
          {match.hard_constraints_passed ? (
            <span className="text-green-600">✅ Constraints Met</span>
          ) : (
            <span className="text-orange-500">⚠️ Partial Match</span>
          )}
        </div>

        <Link 
          to={`/marketplace/${match.listing_id}`} 
          className="btn-secondary small-btn"
          style={{ marginTop: '1rem', display: 'inline-block' }}
        >
          View Listing →
        </Link>
      </div>
    </div>
  );
};

export default MatchCard;