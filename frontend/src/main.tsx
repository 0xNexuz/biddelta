import { createRoot } from 'react-dom/client';
import './style.css';

function Foundation() {
  return <main>
    <p className="eyebrow">BidDelta · Foundation</p>
    <h1>Amendments change decisions.</h1>
    <p>Trace document changes through response claims, evidence, and approvals.</p>
    <section aria-labelledby="status"><h2 id="status">Development status</h2>
      <p>The deterministic review engine is under development. Packet upload and review workflows are not available in this foundation screen.</p>
      <p>Reviewed status does not establish legal compliance or completeness.</p>
    </section>
  </main>;
}

createRoot(document.getElementById('root')!).render(<Foundation />);
