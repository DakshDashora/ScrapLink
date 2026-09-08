import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="landing">
      <h1>ScrapLink</h1>
      <p>AI-Driven B2B Industrial Scrap Exchange</p>
      <div className="cta-buttons">
        <Link to="/login" className="btn-primary">Login</Link>
        <Link to="/register" className="btn-secondary">Register</Link>
      </div>
    </div>
  );
};

export default Landing;