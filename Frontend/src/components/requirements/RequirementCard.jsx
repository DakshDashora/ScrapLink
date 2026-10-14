import { Link } from 'react-router-dom';

const statusClass = (s) =>
  `req-status status-${(s || 'open').toLowerCase()}`;

const RequirementCard = ({ requirement, sellerMode = false }) => {
  const price = requirement.target_price
    ? `₹ ${Number(requirement.target_price).toLocaleString()}`
    : 'Price flexible';

  const loc =
    requirement.location?.city ||
    requirement.location?.state ||
    'Location N/A';

  return (
    <Link
      to={`/buyer/requirements/${requirement.id}`}
      className="listing-card requirement-card"
    >
      <div className="requirement-card-body">
        <div className="requirement-card-top">
          <h3>{requirement.material_name}</h3>
          <span className={statusClass(requirement.status)}>
            {requirement.status}
          </span>
        </div>

        {requirement.grade && (
          <p className="grade">Grade: {requirement.grade}</p>
        )}
        <p className="quantity">
          {Number(requirement.quantity).toLocaleString()} {requirement.unit}
        </p>
        <p className="price">{price}</p>
        <p className="location">📍 {loc}</p>

        {requirement.description && (
          <p className="req-description">
            {requirement.description.length > 90
              ? requirement.description.slice(0, 90) + '…'
              : requirement.description}
          </p>
        )}

        <span className="view-matches-link">View matches →</span>
      </div>
    </Link>
  );
};

export default RequirementCard;