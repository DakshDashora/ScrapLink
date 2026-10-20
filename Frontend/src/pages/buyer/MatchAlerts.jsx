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
      <div className="page-header">
        <h2>Match Alerts</h2>
        {unreadCount > 0 && (
          <button
            className="btn-secondary"
            onClick={() => dispatch(markAllAlertsRead())}
          >
            Mark all read
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {isLoading ? (
        <div className="loading">Loading alerts…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          No match alerts yet. Create a requirement to start receiving matches.
        </div>
      ) : (
        <ul className="alerts-list">
          {items.map((a) => (
            <li
              key={a.id}
              className={`alert-row ${a.is_read ? '' : 'unread'}`}
              onClick={() => !a.is_read && dispatch(markAlertRead(a.id))}
            >
              <div className="alert-row-main">
                <div className="alert-row-title">
                  {a.title || 'New match available'}
                </div>
                <div className="alert-row-sub">
                  {a.material_name || ''}
                  {a.similarity_score != null && (
                    <> · {Math.round(a.similarity_score * 100)}% match</>
                  )}
                </div>
                {a.requirement_id && (
                  <Link
                    to={`/buyer/requirements/${a.requirement_id}`}
                    className="alert-row-link"
                  >
                    View requirement →
                  </Link>
                )}
              </div>
              <div className="alert-row-meta">
                {a.created_at &&
                  new Date(a.created_at).toLocaleDateString()}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default MatchAlerts;