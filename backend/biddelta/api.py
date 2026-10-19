"""Loopback-only offline review API. Never calls a model/provider."""
from pathlib import Path
import csv
import io
import secrets
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .engine import Engine
from .store import Store
from .fixtures import fixture
from .workflow import (Amendment, CreatePacket, Decision, ImpactDecision, Preview,
                       EvidenceCorrection, add_amendment, correct_evidence, create_packet)

MAX_BODY = 72 * 1024 * 1024  # Base64 expansion of bounded packet + metadata.
ORIGINS = {f'http://{host}:{port}' for host in ('127.0.0.1', 'localhost') for port in (5173, 8000)}
COOKIE = 'biddelta_session'


def create_app(db_path: str | Path | None = None) -> FastAPI:
    if db_path is None:
        directory = Path('.biddelta')
        directory.mkdir(mode=0o700, exist_ok=True)
        db_path = directory / 'packets.sqlite3'
    path = Path(db_path)
    if not path.exists():
        path.touch(mode=0o600)
    engine = Engine(Store(path))
    sessions: dict[str, str] = {}
    app = FastAPI(title='BidDelta local review', version='0.2.0')
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost'])

    @app.middleware('http')
    async def local_boundary(request: Request, call_next):
        if request.url.path.startswith('/api/'):
            origin = request.headers.get('origin')
            if origin is not None and origin not in ORIGINS:
                return JSONResponse({'detail': 'Untrusted request origin'}, status_code=403)
            if request.method not in ('GET', 'HEAD'):
                if request.headers.get('x-biddelta-request') != 'local-review':
                    return JSONResponse({'detail': 'Local review request header required'}, status_code=403)
                size, chunks = 0, []
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > MAX_BODY:
                        return JSONResponse({'detail': 'Request exceeds upload bounds'}, status_code=413)
                    chunks.append(chunk)
                request._body = b''.join(chunks)
        return await call_next(request)

    @app.exception_handler(ValueError)
    async def invalid_request(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=409 if 'Stale packet revision' in str(exc) else 422)

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse({'detail': 'Not found'}, status_code=404)

    @app.exception_handler(PermissionError)
    async def forbidden(request, exc):
        # Do not disclose another owner's packet existence.
        return JSONResponse({'detail': 'Not found'}, status_code=404)

    def owner(request: Request):
        token = request.cookies.get(COOKIE)
        if token not in sessions:
            raise HTTPException(401, 'Start a local review session')
        return sessions[token]

    def view(packet_id, actor):
        packet = engine.store.get(packet_id, actor)
        gate = engine.gate_for_packet(packet)
        return {'packet': packet, 'gate': gate, 'analysis_mode': 'offline-human-review'}

    @app.get('/health')
    def health():
        return {'status': 'ok', 'milestone': 'P0-B-slice-1', 'inference': 'unverified'}

    @app.post('/api/session')
    def session(request: Request, response: Response):
        token = request.cookies.get(COOKIE)
        if token not in sessions:
            if len(sessions) >= 256:
                raise HTTPException(503, 'Local session capacity reached; restart deliberately')
            token = secrets.token_urlsafe(32)
            sessions[token] = secrets.token_hex(16)
        response.set_cookie(COOKIE, token, httponly=True, samesite='strict', max_age=86400)
        return {'mode': 'local-owner', 'inference': 'disabled'}

    @app.get('/api/fixtures/{name}')
    def example(name: str, actor=Depends(owner)):
        content, media_type = fixture(name)
        return Response(content, media_type=media_type,
                        headers={'Content-Disposition': f'attachment; filename="synthetic-{name}"'})

    @app.post('/api/preview')
    def preview(body: Preview, actor=Depends(owner)):
        extracted = [u.extract() for u in body.uploads]
        docs = [doc for doc, _ in extracted]
        engine._limits(docs)
        evidence_ids = []
        for doc, content in extracted:
            if doc.kind == 'evidence_register':
                evidence_ids = [row[0] for row in list(csv.reader(io.StringIO(content.decode('utf-8-sig'))))[1:]]
        return {'documents': docs, 'evidence_ids': evidence_ids, 'analysis_mode': 'offline-human-review'}

    @app.post('/api/packets', status_code=201)
    def create(body: CreatePacket, actor=Depends(owner)):
        packet = create_packet(engine, actor, body)
        return view(packet.id, actor)

    @app.get('/api/packets/{packet_id}')
    def get(packet_id: str, actor=Depends(owner)):
        return view(packet_id, actor)

    @app.post('/api/packets/{packet_id}/amendments')
    def amend(packet_id: str, body: Amendment, actor=Depends(owner)):
        add_amendment(engine, packet_id, actor, body)
        return view(packet_id, actor)

    @app.post('/api/packets/{packet_id}/changes/{change_id}/impact')
    def impact(packet_id: str, change_id: str, body: ImpactDecision, actor=Depends(owner)):
        engine.review_impact(packet_id, actor, body.expected_revision, change_id, body.affected_item_ids, body.rationale)
        return view(packet_id, actor)

    @app.post('/api/packets/{packet_id}/evidence-revisions')
    def evidence_correction(packet_id: str, body: EvidenceCorrection, actor=Depends(owner)):
        correct_evidence(engine, packet_id, actor, body)
        return view(packet_id, actor)

    @app.post('/api/packets/{packet_id}/scope')
    def scope(packet_id: str, body: Decision, actor=Depends(owner)):
        engine.confirm_scope(packet_id, actor, body.expected_revision, body.rationale)
        return view(packet_id, actor)

    @app.post('/api/packets/{packet_id}/items/{item_id}/approve')
    def approve(packet_id: str, item_id: str, body: Decision, actor=Depends(owner)):
        engine.approve(packet_id, actor, body.expected_revision, item_id, body.rationale)
        return view(packet_id, actor)

    return app


app = create_app()
