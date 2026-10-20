const MatchReasonList = ({ reasons }) => {
  if (!reasons) return null;

  // Backend may send: array of strings, object of key→value, or nested
  let list = [];
  if (Array.isArray(reasons)) list = reasons;
  else if (typeof reasons === 'object') {
    list = Object.entries(reasons).map(([k, v]) => `${k}: ${v}`);
  }

  if (list.length === 0) return null;

  return (
    <ul className="match-reasons">
      {list.map((r, i) => (
        <li key={i}>{typeof r === 'string' ? r : JSON.stringify(r)}</li>
      ))}
    </ul>
  );
};

export default MatchReasonList;