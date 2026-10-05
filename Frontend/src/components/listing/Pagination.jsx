const Pagination = ({ page, pages, onChange }) => {
  if (!pages || pages <= 1) return null;

  const list = [];
  for (let i = 1; i <= pages; i++) {
    if (i === 1 || i === pages || Math.abs(i - page) <= 1) list.push(i);
    else if (list[list.length - 1] !== '...') list.push('...');
  }

  return (
    <div className="pagination">
      <button disabled={page === 1} onClick={() => onChange(page - 1)}>Prev</button>
      {list.map((p, i) =>
        p === '...' ? (
          <span key={i} className="ellipsis">…</span>
        ) : (
          <button
            key={i}
            className={p === page ? 'active' : ''}
            onClick={() => onChange(p)}
          >
            {p}
          </button>
        )
      )}
      <button disabled={page === pages} onClick={() => onChange(page + 1)}>Next</button>
    </div>
  );
};

export default Pagination;