export type Kind = 'tender' | 'response' | 'evidence_register' | 'amendment';
export interface Upload { kind: Kind; content_base64: string }
export interface Span { id: string; document_version_id: string; page: number; quote: string }
export interface Doc { id: string; kind: Kind; spans: Span[]; extraction_gaps: number[]; sha256: string }
export interface Requirement { id: string; text: string; source_span_ids: string[] }
export interface Item { id: string; text: string; source_span_ids: string[]; requirement_ids: string[]; evidence_ids: string[]; approval_state: string; approved_revision: number | null }
export interface Change { id: string; source_span_id: string; description: string; requirement_ids: string[]; reviewed: boolean }
export interface Packet { id: string; revision: number; scope_confirmed_revision: number; documents: Doc[]; requirements: Requirement[]; items: Item[]; changes: Change[]; evidence: { evidence_id: string; status: string; note: string }[]; decisions: { id: string; action: string; target_id: string; revision: number; rationale: string }[] }
export interface Review { packet: Packet; gate: { allowed: boolean; blockers: string[]; disclaimer: string }; analysis_mode: string }
export interface Mapping { page: number; requirement_pages: number[]; evidence_ids: string[] }
export interface Draft { page: number; description: string; requirement_ids: string[] }

export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-BidDelta-Request': 'local-review' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : 'Check upload fields and file bounds.';
    throw new Error(detail + (response.status === 409 ? ' Refresh the packet before retrying.' : ''));
  }
  return data as T;
}

export async function upload(file: File, kind: Kind): Promise<Upload> {
  if (!file.size || file.size > 20 * 1024 * 1024) throw new Error('Each file must be nonempty and at most 20 MiB.');
  const content_base64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = () => reject(new Error('Could not read the selected file.'));
    reader.readAsDataURL(file);
  });
  return { kind, content_base64 };
}
