import { Link } from 'react-router-dom';

const AlertDropdown = ({ 
  items, 
  unreadCount, 
  onMarkAllRead, 
  onMarkRead, 
  onClose 
}) => {
  // Only show the 5 most recent in the dropdown
  const recent = items.slice(0, 5);

  return (
    <div className="alert-dropdown">
      <div className="alert-dropdown-header">
        <strong>Match Alerts</strong>
        {unreadCount > 0 && (
          <button
            className="link-button"
            onClick={onMarkAllRead}
            type="button"
          >
            Mark all read
          </button>
        )}
      </div>

      {recent.length === 0 ? (
        <div className="alert-empty">No new matches yet.</div>
      ) : (
        <ul className="alert-list">
          {recent.map((a) => (
            <li
              key={a.id}
              className={`alert-item ${a.is_read ? '' : 'unread'}`}
              onClick={() => !a.is_read && onMarkRead(a.id)}
            >
              <div className="alert-item-title">
                {a.title || 'New match available'}
              </div>
              <div className="alert-item-sub">
                {a.material_name || a.requirement_name || ''}
              </div>
            </li>
          ))}
        </ul>
      )}

      <Link
        to="/buyer/match-alerts"
        className="alert-see-all"
        onClick={onClose}
      >
        See all alerts →
      </Link>
    </div>
  );
};

export default AlertDropdown;