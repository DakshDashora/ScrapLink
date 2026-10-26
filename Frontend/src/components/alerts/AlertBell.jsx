import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchMatchAlerts,
  markAllAlertsRead,
  markAlertRead,
} from '../../redux/slices/alertSlice';
import AlertDropdown from './AlertDropdown';

const AlertBell = () => {
  const dispatch = useDispatch();
  const { items, unreadCount } = useSelector((s) => s.alerts);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  // Poll every 30 seconds for new alerts
  useEffect(() => {
    dispatch(fetchMatchAlerts());
    const t = setInterval(() => dispatch(fetchMatchAlerts()), 30000);
    return () => clearInterval(t);
  }, [dispatch]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const onDocClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  return (
    <div className="alert-bell-wrap" ref={wrapRef}>
      <button
        className="alert-bell-btn"
        onClick={() => setOpen((o) => !o)}
        aria-label="Match alerts"
        type="button"
      >
        🔔
        {unreadCount > 0 && (
          <span className="alert-badge">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <AlertDropdown
          items={items}
          unreadCount={unreadCount}
          onMarkAllRead={() => dispatch(markAllAlertsRead())}
          onMarkRead={(id) => dispatch(markAlertRead(id))}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
};

export default AlertBell;