import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="landing">
      <header className="landing-nav">
        <Link to="/" className="landing-brand">Scrap<span>Link</span></Link>
        <span>A smarter industrial materials exchange</span>
      </header>

      <main className="landing-content">
        <section className="landing-copy">
          <span className="landing-eyebrow">Built for circular industry</span>
          <h1>Give useful materials a <span>better next chapter.</span></h1>
          <p>
            Connect businesses buying and selling industrial scrap. Find the
            right materials, make better-fit connections, and keep resources in use.
          </p>
          <div className="cta-buttons">
            <Link to="/register" className="btn-primary">Join ScrapLink</Link>
            <Link to="/login" className="btn-secondary">Sign in</Link>
          </div>
        </section>

        <aside className="landing-panel" aria-label="How ScrapLink helps">
          <span className="panel-label">A better materials cycle</span>
          <h2>Make every connection count.</h2>
          <div className="landing-benefit">
            <span className="benefit-number">01</span>
            <div>
              <h3>Discover materials</h3>
              <p>Explore industrial scrap listings in one place.</p>
            </div>
          </div>
          <div className="landing-benefit">
            <span className="benefit-number">02</span>
            <div>
              <h3>Find a better fit</h3>
              <p>Bring buyer requirements and available supply together.</p>
            </div>
          </div>
          <div className="landing-benefit">
            <span className="benefit-number">03</span>
            <div>
              <h3>Keep value in use</h3>
              <p>Help useful resources find their next destination.</p>
            </div>
          </div>
        </aside>
      </main>

      <footer className="landing-footer">
        <span>ScrapLink</span>
        <span>Industrial materials, moving forward.</span>
      </footer>
    </div>
  );
};

export default Landing;