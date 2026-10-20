import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import {
  fetchMatchAlerts,
  markAllAlertsRead,
  markAlertRead,
} from '../../redux/slices/alertSlice';

const AlertBell = () => {
  const dispatch = useDispatch();
  const { items, unreadCount } = useSelector((s) => s.alerts);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  // Poll every 30 s — lightweight; later you can switch to WebSocket
  useEffect(() => {
    dispatch(fetchMatchAlerts());
    const t = setInterval(() => dispatch(fetchMatchAlerts()), 30000);
    return () => clearInterval(t);
  }, [dispatch]);

  // Close on outside click
  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  const recent = items.slice(0, 5);

  return (
    <div className="alert-bell-wrap" ref={wrapRef}>
      <button
        className="alert-bell-btn"
        onClick={() => setOpen((o) => !o)}
        aria-label="Match alerts"
      >
        🔔
        {unreadCount > 0 && (
          <span className="alert-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
        )}
      </button>

      {open && (
        <div className="alert-dropdown">
          <div className="alert-dropdown-header">
            <strong>Match Alerts</strong>
            {unreadCount > 0 && (
              <button
                className="link-button"
                onClick={() => dispatch(markAllAlertsRead())}
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
                  onClick={() => !a.is_read && dispatch(markAlertRead(a.id))}
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
            onClick={() => setOpen(false)}
          >
            See all alerts →
          </Link>
        </div>
      )}
    </div>
  );
};

export default AlertBell;