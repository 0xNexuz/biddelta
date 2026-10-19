import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { api, upload, type Doc, type Draft, type Kind, type Mapping, type Review, type Upload } from './api';
import './style.css';

const kinds: Kind[] = ['tender', 'response', 'evidence_register'];
const names: Record<Kind, string> = { tender: 'Tender PDF', response: 'Draft response PDF', evidence_register: 'Evidence CSV', amendment: 'Amendment PDF' };
const toggle = <T,>(values: T[], value: T) => values.includes(value) ? values.filter(v => v !== value) : [...values, value];

function App() {
  const [ready, setReady] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [files, setFiles] = useState<Partial<Record<Kind, File>>>({});
  const [prepared, setPrepared] = useState<{ uploads: Upload[]; documents: Doc[]; evidence_ids: string[] } | null>(null);
  const [mappings, setMappings] = useState<Mapping[]>([]), [review, setReview] = useState<Review | null>(null);
  const [amendment, setAmendment] = useState<{ upload: Upload; document: Doc } | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]), [noChanges, setNoChanges] = useState(false);
  const [rationale, setRationale] = useState(''), [impacts, setImpacts] = useState<Record<string, string[]>>({});
  const [synthetic, setSynthetic] = useState(false);
  async function run(task: () => Promise<void>) {
    setBusy(true); setError('');
    try { await task(); } catch (e) { setError(e instanceof Error ? e.message : 'Request failed.'); }
    finally { setBusy(false); }
  }
  function accept(next: Review) {
    setReview(next); localStorage.setItem('biddelta-packet', next.packet.id);
    setRationale(''); setImpacts({});
  }
  useEffect(() => { void run(async () => {
    await api('/session', {}); setReady(true);
    const id = localStorage.getItem('biddelta-packet');
    if (id) accept(await api<Review>(`/packets/${encodeURIComponent(id)}`));
  }); }, []);
  async function previewInitial() {
    const selected = kinds.map(kind => { const f = files[kind]; if (!f) throw new Error(`Select ${names[kind]}.`); return f; });
    if (selected.reduce((n, f) => n + f.size, 0) > 50 * 1024 * 1024) throw new Error('Packet exceeds 50 MiB.');
    const uploads = await Promise.all(kinds.map((kind, i) => upload(selected[i], kind)));
    const { documents, evidence_ids } = await api<{ documents: Doc[]; evidence_ids: string[] }>('/preview', { uploads });
    const tender = documents.find(d => d.kind === 'tender')!, response = documents.find(d => d.kind === 'response')!;
    const evidence = evidence_ids;
    setPrepared({ uploads, documents, evidence_ids });
    setMappings(response.spans.map(s => ({ page: s.page, requirement_pages: tender.spans.map(t => t.page), evidence_ids: evidence })));
  }
  async function previewAmendment(file: File) {
    const u = await upload(file, 'amendment');
    const { documents } = await api<{ documents: Doc[] }>('/preview', { uploads: [u] });
    setAmendment({ upload: u, document: documents[0] }); setNoChanges(false);
    setDrafts(documents[0].spans.map(s => ({ page: s.page, description: s.quote, requirement_ids: review!.packet.requirements.map(r => r.id) })));
  }
  const packet = review?.packet;
  const span = (id: string) => packet?.documents.flatMap(d => d.spans).find(s => s.id === id);
  const hasGaps = prepared?.documents.some(d => d.extraction_gaps.length);
  const evidence = prepared?.evidence_ids ?? [];
  async function decide(path: string, extra = {}) {
    if (!rationale.trim()) throw new Error('Enter a review rationale first.');
    accept(await api<Review>(`/packets/${packet!.id}${path}`, { expected_revision: packet!.revision, rationale: rationale.trim(), ...extra }));
  }
  return <main>
    <header><p className="eyebrow">BidDelta · Local review</p><h1>Keep amendments accountable.</h1>
      <p>Offline, human-reviewed page candidates. No model inference. Local use only.</p>
      {synthetic && <p className="notice">Synthetic example files — not a real tender or model result.</p>}
    </header>
    {error && <p role="alert" className="error">{error}</p>}
    {!ready && <button disabled={busy} onClick={() => void run(async () => { await api('/session', {}); setReady(true); })}>Start local session</button>}
    <div aria-busy={busy}>
    {!packet && ready && <section><h2>1. Upload a packet</h2>
      <p>Text PDFs only. Five files including amendments, 60 PDF pages total, 20 MiB per file and 50 MiB per packet. CSV header: evidence_id,status,note. Status: asserted, missing or conflict.</p>
      <fieldset disabled={busy}><legend>Original source files</legend>
        {kinds.map(kind => <label key={kind}>{names[kind]}<input type="file" accept={kind === 'evidence_register' ? '.csv' : '.pdf'} onChange={e => { setFiles({ ...files, [kind]: e.target.files?.[0] }); setPrepared(null); setSynthetic(false); }} />{files[kind]?.name}</label>)}
        <button onClick={() => void run(async () => {
          const loaded: Partial<Record<Kind, File>> = {};
          for (const kind of kinds) {
            const filename = kind === 'evidence_register' ? 'evidence.csv' : `${kind}.pdf`;
            const res = await fetch(`/api/fixtures/${filename}`); if (!res.ok) throw new Error('Could not load synthetic files.');
            loaded[kind] = new File([await res.blob()], `synthetic-${filename}`);
          }
          setFiles(loaded); setPrepared(null); setSynthetic(true);
        })}>Use synthetic example files</button>
        <button onClick={() => void run(previewInitial)}>Preview uploads</button>
      </fieldset>
      {prepared && <><h3>2. Confirm page dependencies</h3>
        <p>Every readable tender page is a requirement candidate; every response page is an item. All dependencies start selected conservatively. Review and correct these mappings before creating the packet. These are not detected semantic claims.</p>
        {hasGaps && <p className="error">Empty/unreadable pages remain extraction gaps and block scope confirmation.</p>}
        {prepared.documents.filter(d => d.kind !== 'response').map(d => <details key={d.id}><summary>{names[d.kind]} · extracted sources</summary>{d.spans.map(s => <pre key={s.id}>Page/record {s.page}: {s.quote}</pre>)}</details>)}
        <fieldset disabled={busy}><legend>Response mappings</legend>
        {mappings.map((m, index) => <article key={m.page}><h4>Response page {m.page}</h4><pre>{prepared.documents.find(d => d.kind === 'response')?.spans.find(s => s.page === m.page)?.quote}</pre>
          <p>Depends on tender pages:</p>{prepared.documents.find(d => d.kind === 'tender')?.spans.map(s => <label className="check" key={s.page}><input type="checkbox" checked={m.requirement_pages.includes(s.page)} onChange={() => setMappings(mappings.map((x, i) => i === index ? { ...x, requirement_pages: toggle(x.requirement_pages, s.page) } : x))} />Tender page {s.page}</label>)}
          <p>Evidence dependencies (owner assertions):</p>{evidence.map(id => <label className="check" key={id}><input type="checkbox" checked={m.evidence_ids.includes(id)} onChange={() => setMappings(mappings.map((x, i) => i === index ? { ...x, evidence_ids: toggle(x.evidence_ids, id) } : x))} />{id}</label>)}
        </article>)}
        <button disabled={!mappings.length || mappings.some(m => !m.requirement_pages.length)} onClick={() => void run(async () => { accept(await api<Review>('/packets', { uploads: prepared.uploads, mappings })); setPrepared(null); })}>Create packet with these mappings</button>
        </fieldset></>}
    </section>}
    {packet && review && <>
      <section><div className="row"><h2>Packet · revision {packet.revision}</h2><button disabled={busy} onClick={() => void run(async () => accept(await api<Review>(`/packets/${packet.id}`)))}>Refresh packet</button></div>
        <p className={review.gate.allowed ? 'notice' : 'blocked'} role="status">{review.gate.allowed ? 'Reviewed gate open' : 'Reviewed gate blocked'}</p>
        <ul>{review.gate.blockers.map(b => <li key={b}>{b.replaceAll('_', ' ')}</li>)}</ul>
        <p>{review.gate.disclaimer} Downloadable export is not available in this slice.</p>
        <label>Review rationale<textarea value={rationale} onChange={e => setRationale(e.target.value)} maxLength={4000} placeholder="Record what you checked and why." /></label>
        <fieldset disabled={busy || !rationale.trim()}><legend>Scope review</legend><p>Confirm only after checking the complete source inventory, all response scope, and all changes. This carries unaffected approvals forward; affected items need fresh review.</p>
          <button disabled={packet.changes.some(c => !c.reviewed) || packet.documents.some(d => d.extraction_gaps.length > 0)} onClick={() => void run(() => decide('/scope'))}>Confirm complete scope</button>
        </fieldset>
      </section>
      <section><h2>Response items</h2>{packet.items.map(item => <article key={item.id}><h3>{item.id} · {item.approval_state.replaceAll('_', ' ')}</h3><pre>{item.text}</pre><p>Requirements: {item.requirement_ids.join(', ')} · Evidence: {item.evidence_ids.join(', ') || 'none linked'}</p>
        <details><summary>Response source</summary>{item.source_span_ids.map(id => <pre key={id}>{span(id)?.quote}</pre>)}</details>
        <button disabled={busy || !rationale.trim() || packet.scope_confirmed_revision !== packet.revision || packet.changes.some(c => !c.reviewed) || item.approval_state === 'approved'} onClick={() => void run(() => decide(`/items/${item.id}/approve`))}>Approve {item.id} at revision {packet.revision}</button>
      </article>)}</section>
      <section><h2>Changes and impact review</h2>{packet.changes.length === 0 && <p>No amendment changes recorded. Scope review still requires a complete inventory check.</p>}
      {packet.changes.map(c => {
        const required = packet.items.filter(i => i.requirement_ids.some(id => c.requirement_ids.includes(id))).map(i => i.id);
        const selected = impacts[c.id] ?? required;
        return <article key={c.id}><h3>{c.reviewed ? 'Impact reviewed' : 'Impact review required'}</h3><p>{c.description}</p><details><summary>Amendment source · page {span(c.source_span_id)?.page}</summary><pre>{span(c.source_span_id)?.quote}</pre></details>
          {!c.reviewed && <fieldset disabled={busy}><legend>Affected response items</legend>{packet.items.map(i => <label className="check" key={i.id}><input type="checkbox" checked={selected.includes(i.id)} disabled={required.includes(i.id)} onChange={() => setImpacts({ ...impacts, [c.id]: toggle(selected, i.id) })} />{i.id}{required.includes(i.id) ? ' (known dependency)' : ''}</label>)}
          <p>Unchecked items are explicitly reviewed as unaffected. Known dependencies cannot be removed.</p>
          <button disabled={!rationale.trim()} onClick={() => void run(() => decide(`/changes/${c.id}/impact`, { affected_item_ids: selected }))}>Record impact review</button></fieldset>}
        </article>;
      })}</section>
      <section><h2>Add an amendment</h2><fieldset disabled={busy || packet.documents.filter(d => d.kind === 'amendment').length >= 2}><legend>Amendment source and change inventory</legend>
        <label>Amendment PDF<input type="file" accept=".pdf" onChange={e => { const f = e.target.files?.[0]; setAmendment(null); if (f) void run(() => previewAmendment(f)); }} /></label>
        <button onClick={() => void run(async () => { const res = await fetch('/api/fixtures/amendment.pdf'); if (!res.ok) throw new Error('Fixture unavailable'); await previewAmendment(new File([await res.blob()], 'synthetic-amendment.pdf')); setSynthetic(true); })}>Preview synthetic amendment</button>
        {amendment && <><p>Manual change inventory. Each readable page starts as a change candidate. Review descriptions and affected requirements before recording.</p>
          <label className="check"><input type="checkbox" checked={noChanges} onChange={e => setNoChanges(e.target.checked)} />I found no supported changes; complete scope review will still be required.</label>
          {amendment.document.extraction_gaps.length > 0 && <p className="error">Unreadable pages will block scope review.</p>}
          {!noChanges && drafts.map((d, index) => <article key={d.page}><h3>Amendment page {d.page}</h3><pre>{amendment.document.spans.find(s => s.page === d.page)?.quote}</pre><label>Change description<textarea maxLength={8000} value={d.description} onChange={e => setDrafts(drafts.map((x, i) => i === index ? { ...x, description: e.target.value } : x))} /></label>
            {packet.requirements.map(r => <label className="check" key={r.id}><input type="checkbox" checked={d.requirement_ids.includes(r.id)} onChange={() => setDrafts(drafts.map((x, i) => i === index ? { ...x, requirement_ids: toggle(x.requirement_ids, r.id) } : x))} />{r.id}: {r.text.slice(0, 100)}</label>)}
          </article>)}
          <button disabled={!noChanges && (!drafts.length || drafts.some(d => !d.description.trim()))} onClick={() => void run(async () => { accept(await api<Review>(`/packets/${packet.id}/amendments`, { expected_revision: packet.revision, upload: amendment.upload, changes: noChanges ? [] : drafts })); setAmendment(null); })}>Record amendment and open review</button>
        </>}
      </fieldset></section>
      <section><h2>Source inventory and evidence</h2>{packet.documents.map(d => <details key={d.id}><summary>{names[d.kind]} · {d.id.slice(0, 8)}{d.extraction_gaps.length > 0 ? ' · extraction gaps' : ''}</summary><p>SHA-256: {d.sha256}</p>{d.spans.map(s => <pre key={s.id}>Page/record {s.page}: {s.quote}</pre>)}</details>)}
        {packet.evidence.map(e => <p key={e.evidence_id}>{e.evidence_id} · {e.status} · {e.note}</p>)}
      </section>
      <section><h2>Review history</h2>{packet.decisions.map(d => <p key={d.id}>Revision {d.revision} · {d.action} · {d.target_id}: {d.rationale}</p>)}</section>
      <button disabled={busy} onClick={() => { localStorage.removeItem('biddelta-packet'); setReview(null); setPrepared(null); setAmendment(null); setFiles({}); setSynthetic(false); setError(''); }}>Start another packet (history retained)</button>
    </>}
    </div>
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
