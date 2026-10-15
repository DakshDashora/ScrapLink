const RequirementStatusBadge = ({ status }) => {
  const cls = `status-badge status-${(status || 'open').toLowerCase()}`;
  return <span className={cls}>{status || 'Open'}</span>;
};

export default RequirementStatusBadge;