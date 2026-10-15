import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { fetchRequirements } from '../../redux/slices/requirementSlice';
import RequirementCard from '../../components/requirements/RequirementCard';

const MyRequirements = () => {
  const dispatch = useDispatch();
  const { items, isLoading, error } = useSelector((s) => s.requirements);

  useEffect(() => {
    dispatch(fetchRequirements());
  }, [dispatch]);

  return (
    <div className="my-listings-page">
      <div className="page-header">
        <h2>My Requirements</h2>
        <Link to="/buyer/requirements/new" className="btn-primary">
          + New Requirement
        </Link>
      </div>

      {error && <div className="error-message">{error}</div>}

      {isLoading ? (
        <div className="loading">Loading requirements…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          You haven't created any requirements yet. Click{' '}
          <strong>+ New Requirement</strong> to let ScrapLink find matches.
        </div>
      ) : (
        <div className="listings-grid">
          {items.map((r) => (
            <RequirementCard key={r.id} requirement={r} />
          ))}
        </div>
      )}
    </div>
  );
};

export default MyRequirements;