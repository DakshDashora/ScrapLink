import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTrustScore } from '../../redux/slices/trustSlice';

const TrustIndicator = ({ listingId }) => {
  const dispatch = useDispatch();
  const trust = useSelector((s) => s.trust.byListing[listingId]);
  const { isLoading, error } = useSelector((s) => s.trust);

  useEffect(() => {
    if (listingId && !trust) {
      dispatch(fetchTrustScore(listingId));
    }
  }, [dispatch, listingId, trust]);

  if (isLoading && !trust) {
    return (
      <div className="trust-indicator loading">
        <span>Analysing listing…</span>
      </div>
    );
  }

  if (error && !trust) {
    return (
      <div className="trust-indicator neutral">
        <div className="trust-title">Trust signal</div>
        <div className="trust-message">Not available</div>
      </div>
    );
  }

  if (!trust) return null;

  // Backend may return: { overall_score, label, explanation, ... }
  const label = trust.label || trust.trust_label || classify(trust);
  const score = trust.overall_score ?? trust.score ?? null;
  const explanation = trust.explanation;

  return (
    <div className={`trust-indicator trust-${label.toLowerCase()}`}>
      <div className="trust-title">
        <span className="trust-icon">{iconFor(label)}</span>
        Trust Signal
      </div>
      <div className="trust-label">{prettyLabel(label)}</div>
      {score !== null && (
        <div className="trust-score">
          Score: <strong>{typeof score === 'number' ? score.toFixed(2) : score}</strong>
        </div>
      )}
      {explanation && (
        <div className="trust-explanation">
          {typeof explanation === 'string'
            ? explanation
            : Object.entries(explanation).map(([k, v]) => (
                <div key={k}>
                  <strong>{k}:</strong> {String(v)}
                </div>
              ))}
        </div>
      )}
      <p className="trust-disclaimer">
        An anomaly-based decision-support signal — not a fraud probability.
      </p>
    </div>
  );
};

function classify(trust) {
  const s = trust.overall_score ?? trust.score;
  if (s === undefined || s === null) return 'normal';
  if (s >= 0.7) return 'normal';
  if (s >= 0.4) return 'unusual';
  return 'suspicious';
}

function prettyLabel(label) {
  if (!label) return 'Normal pattern';
  return label
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function iconFor(label) {
  const l = (label || '').toLowerCase();
  if (l.includes('normal')) return '✅';
  if (l.includes('unusual')) return '⚠️';
  if (l.includes('suspicious') || l.includes('anomaly')) return '🚩';
  return 'ℹ️';
}

export default TrustIndicator;