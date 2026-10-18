const MatchScoreBadge = ({ score, label }) => {
  if (score === null || score === undefined) return null;

  // Score is 0–1; render as a coloured pill
  const pct = Math.round(score * 100);
  const tier = pct >= 80 ? 'high' : pct >= 60 ? 'medium' : 'low';

  return (
    <div className={`match-score-badge match-${tier}`}>
      <span className="score-value">{pct}%</span>
      <span className="score-label">{label || 'Match'}</span>
    </div>
  );
};

export default MatchScoreBadge;