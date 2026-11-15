import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import {
  fetchMatchAlerts,
  markAlertRead,
  markAllAlertsRead,
} from '../../redux/slices/alertSlice';

const MatchAlerts = () => {
  const dispatch = useDispatch();
  const { items, unreadCount, isLoading, error } = useSelector((s) => s.alerts);

  useEffect(() => {
    dispatch(fetchMatchAlerts());
  }, [dispatch]);

  return (
    <div className="alerts-page">
      <div className="page-header alerts-header">
        <div>
          <h2>Match Alerts</h2>
          <p className="page-subtitle">Real-time alerts when sellers list scrap matching your active requirements</p>
        </div>
        {unreadCount > 0 && (
          <button
            className="btn-secondary"
            onClick={() => dispatch(markAllAlertsRead())}
          >
            ✓ Mark all as read
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {isLoading ? (
        <div className="loading">Loading alerts…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔔</div>
          <h3>No match alerts yet</h3>
          <p>Create a buyer requirement to start receiving automated match recommendations.</p>
          <Link to="/buyer/requirements/new" className="btn-primary" style={{ marginTop: '1rem', display: 'inline-block' }}>
            + Create New Requirement
          </Link>
        </div>
      ) : (
        <ul className="alerts-list">
          {items.map((a) => {
            const title = a.title || a.listing_name || a.material_name || 'New scrap listing match';
            const scorePct = a.similarity_score != null ? Math.round(a.similarity_score * 100) : null;
            const dateStr = a.created_at ? new Date(a.created_at).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            }) : '';

            return (
              <li
                key={a.id}
                className={`alert-row ${a.is_read ? 'read' : 'unread'}`}
                onClick={() => !a.is_read && dispatch(markAlertRead(a.id))}
              >
                <div className="alert-row-left">
                  <div className="alert-status-indicator"></div>
                  <div className="alert-row-main">
                    <div className="alert-row-title-row">
                      <h4 className="alert-row-title">{title}</h4>
                      {scorePct != null && (
                        <span className="match-pct-badge">{scorePct}% Match</span>
                      )}
                    </div>

                    <div className="alert-row-sub">
                      {a.listing_name && a.listing_name !== title && (
                        <span>Material: <strong>{a.listing_name}</strong> · </span>
                      )}
                      <span>Created {dateStr}</span>
                    </div>

                    <div className="alert-actions-row">
                      {a.requirement_id && (
                        <Link
                          to={`/buyer/requirements/${a.requirement_id}`}
                          className="alert-link-btn primary-link"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View Requirement Matches →
                        </Link>
                      )}
                      {a.listing_id && (
                        <Link
                          to={`/marketplace/${a.listing_id}`}
                          className="alert-link-btn secondary-link"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View Listing Details ↗
                        </Link>
                      )}
                    </div>
                  </div>
                </div>

                <div className="alert-row-meta">
                  {!a.is_read && (
                    <span className="unread-dot-badge">New</span>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default MatchAlerts;
