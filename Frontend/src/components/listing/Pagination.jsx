const Pagination = ({ page, total, pageSize, onPageChange }) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  const pages = [];
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || Math.abs(i - page) <= 1) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== '...') {
      pages.push('...');
    }
  }

  return (
    <div className="pagination">
      <button disabled={page === 1} onClick={() => onPageChange(page - 1)}>
        Prev
      </button>
      {pages.map((p, i) =>
        p === '...' ? (
          <span key={i} className="ellipsis">…</span>
        ) : (
          <button
            key={i}
            className={p === page ? 'active' : ''}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        )
      )}
      <button
        disabled={page === totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        Next
      </button>
    </div>
  );
};

export default Pagination;