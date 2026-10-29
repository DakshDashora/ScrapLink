import { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchRequirementById,
  deactivateRequirement,
  clearCurrentRequirement,
} from '../../redux/slices/requirementSlice';
import {
  fetchMatches,
  refreshMatches,
} from '../../redux/slices/matchSlice';
import MatchCard from '../../components/matches/MatchCard';

const RequirementDetails = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { current, isLoading, error } = useSelector((s) => s.requirements);
  const matches = useSelector((s) => s.matches.byRequirement[id] || []);
  const { isLoading: matchLoading, isRefreshing, error: matchError } =
    useSelector((s) => s.matches);

  useEffect(() => {
    dispatch(fetchRequirementById(id));
    dispatch(fetchMatches(id));
    return () => dispatch(clearCurrentRequirement());
  }, [dispatch, id]);

  const handleRefresh = () => dispatch(refreshMatches(id));

  const handleDeactivate = async () => {
    if (!window.confirm('Deactivate this requirement?')) return;
    const res = await dispatch(deactivateRequirement(id)).unwrap().catch(() => null);
    if (res) navigate('/buyer/requirements');
  };

  if (isLoading || !current) return <div className="loading">Loading…</div>;
  if (error) return <div className="error-message">{error}</div>;

  const isActive = current.status === 'Open' || current.status === 'Active';

  return (
    <div className="requirement-details">
      <div className="page-header">
        <h2>{current.material_name}</h2>
        <div className="owner-actions">
          {isActive && (
            <>
              <Link
                to={`/buyer/requirements/${id}/edit`}
                className="btn-secondary"
              >
                Edit
              </Link>
              <button className="btn-danger" onClick={handleDeactivate}>
                Deactivate
              </button>
            </>
          )}
        </div>
      </div>

      <div className="requirement-summary">
        <div className="summary-left">
          <p>
            <strong>Quantity:</strong>{' '}
            {Number(current.quantity).toLocaleString()} {current.unit}
          </p>
          {current.grade && (
            <p><strong>Grade:</strong> {current.grade}</p>
          )}
          <p>
            <strong>Target Price:</strong>{' '}
            {current.target_price
              ? `₹ ${Number(current.target_price).toLocaleString()}`
              : 'Flexible'}
          </p>
          <p>
            <strong>Location:</strong>{' '}
            {current.location?.city || '—'}
            {current.location?.state && `, ${current.location.state}`}
          </p>
          <p>
            <strong>Status:</strong> {current.status}
          </p>
          {current.description && (
            <p className="description">{current.description}</p>
          )}
        </div>

        <div className="summary-right">
          <button
            className="btn-primary"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? 'Searching…' : '🔄 Find Fresh Matches'}
          </button>
        </div>
      </div>

      <h3 className="section-heading">
        Matched Listings ({matches.length})
      </h3>

      {matchError && <div className="error-message">{matchError}</div>}

      {matchLoading && matches.length === 0 ? (
        <div className="loading">Finding matches…</div>
      ) : matches.length === 0 ? (
        <div className="empty-state">
          No matching listings yet. Try clicking <strong>Find Fresh Matches</strong>{' '}
          once new listings appear.
        </div>
      ) : (
        <div className="matches-grid">
          {matches.map((m) => (
            <MatchCard key={m.id || m.listing?.id} match={m} />
          ))}
        </div>
      )}
    </div>
  );
};

export default RequirementDetails;