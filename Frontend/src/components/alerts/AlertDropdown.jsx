import { Link } from 'react-router-dom';

const AlertDropdown = ({ 
  items = [], 
  unreadCount = 0, 
  onMarkAllRead, 
  onMarkRead, 
  onClose 
}) => {
  const recent = items.slice(0, 5);

  return (
    <div className="alert-dropdown" onClick={(e) => e.stopPropagation()}>
      <div className="alert-dropdown-header">
        <div className="dropdown-title">
          <strong>Match Alerts</strong>
          {unreadCount > 0 && <span className="dropdown-unread-pill">{unreadCount} new</span>}
        </div>
        {unreadCount > 0 && (
          <button
            className="link-button mark-all-btn"
            onClick={onMarkAllRead}
            type="button"
          >
            Mark all read
          </button>
        )}
      </div>

      {recent.length === 0 ? (
        <div className="alert-empty">
          <span>🔔</span>
          <p>No new matches yet.</p>
        </div>
      ) : (
        <ul className="alert-list">
          {recent.map((a) => {
            const title = a.title || a.listing_name || a.material_name || 'New scrap listing match';
            const scorePct = a.similarity_score != null ? Math.round(a.similarity_score * 100) : null;
            return (
              <li
                key={a.id}
                className={`alert-item ${a.is_read ? 'read' : 'unread'}`}
                onClick={() => !a.is_read && onMarkRead(a.id)}
              >
                <div className="alert-item-content">
                  <div className="alert-item-title-row">
                    <span className="alert-item-title">{title}</span>
                    {scorePct != null && (
                      <span className="alert-item-pct">{scorePct}%</span>
                    )}
                  </div>
                  <div className="alert-item-sub">
                    {a.created_at ? new Date(a.created_at).toLocaleDateString() : ''}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <div className="alert-dropdown-footer">
        <Link
          to="/buyer/match-alerts"
          className="alert-see-all"
          onClick={onClose}
        >
          View all match alerts →
        </Link>
      </div>
    </div>
  );
};

export default AlertDropdown;
