import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchRequirementById,
  clearCurrentRequirement,
} from '../../redux/slices/requirementSlice';
import RequirementForm from '../../components/requirements/RequirementForm';

const EditRequirement = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { current, isLoading } = useSelector((s) => s.requirements);

  useEffect(() => {
    dispatch(fetchRequirementById(id));
    return () => dispatch(clearCurrentRequirement());
  }, [dispatch, id]);

  if (isLoading || !current) return <div className="loading">Loading…</div>;

  return (
    <div className="page-container">
      <RequirementForm initial={current} isEdit />
    </div>
  );
};

export default EditRequirement;