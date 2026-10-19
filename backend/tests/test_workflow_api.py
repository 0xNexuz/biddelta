"""Targeted P0-B API slice, entirely synthetic and offline."""
import asyncio
import base64
import httpx
import pytest
from biddelta.api import create_app
from biddelta.fixtures import fixture

HEADERS = {'X-BidDelta-Request': 'local-review', 'Origin': 'http://127.0.0.1:5173'}


def upload(kind, name):
    return {'kind': kind, 'content_base64': base64.b64encode(fixture(name)[0]).decode()}


def initial():
    return {'uploads': [upload('tender', 'tender.pdf'), upload('response', 'response.pdf'),
                        upload('evidence_register', 'evidence.csv')],
            'mappings': [{'page': 1, 'requirement_pages': [1], 'evidence_ids': ['e1']},
                         {'page': 2, 'requirement_pages': [2], 'evidence_ids': []}]}


def client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                             base_url='http://127.0.0.1:8000', headers=HEADERS)


def test_upload_amend_review_and_gate_vertical_slice(tmp_path, monkeypatch):
    monkeypatch.delenv('NEBIUS_API_KEY', raising=False)
    async def check():
        app = create_app(tmp_path / 'review.sqlite3')
        async with client(app) as c:
            session = await c.post('/api/session', json={})
            assert session.json()['inference'] == 'disabled'
            assert 'HttpOnly' in session.headers['set-cookie'] and 'SameSite=strict' in session.headers['set-cookie']
            preview = await c.post('/api/preview', json={'uploads': initial()['uploads']})
            assert preview.status_code == 200
            assert len(preview.json()['documents'][0]['spans']) == 2
            result = await c.post('/api/packets', json=initial())
            assert result.status_code == 201, result.text
            p = result.json()['packet']; url = '/api/packets/' + p['id']
            assert not result.json()['gate']['allowed']
            decision = {'expected_revision': 1, 'rationale': 'Synthetic inventory checked'}
            assert (await c.post(url + '/scope', json=decision)).status_code == 200
            for item in ('i-1', 'i-2'):
                result = await c.post(url + '/items/' + item + '/approve', json=decision)
                assert result.status_code == 200
            assert result.json()['gate']['allowed']
            amendment = {'expected_revision': 1, 'upload': upload('amendment', 'amendment.pdf'),
                         'changes': [{'page': 1, 'description': 'Synthetic deadline changed', 'requirement_ids': ['r-1']}]}
            result = await c.post(url + '/amendments', json=amendment)
            assert result.status_code == 200, result.text
            p = result.json()['packet']
            assert [i['approval_state'] for i in p['items']] == ['stale', 'needs_scope_confirmation']
            assert 'missing_impact_review' in result.json()['gate']['blockers']
            stale = await c.post(url + '/items/i-1/approve', json=decision)
            assert stale.status_code == 409
            decision['expected_revision'] = 2
            assert (await c.post(url + '/scope', json=decision)).status_code == 422
            impact = {**decision, 'affected_item_ids': []}
            path = url + '/changes/' + p['changes'][0]['id'] + '/impact'
            assert (await c.post(path, json=impact)).status_code == 422
            impact['affected_item_ids'] = ['i-1']
            assert (await c.post(path, json=impact)).status_code == 200
            result = await c.post(url + '/scope', json=decision)
            assert [i['approval_state'] for i in result.json()['packet']['items']] == ['stale', 'approved']
            result = await c.post(url + '/items/i-1/approve', json=decision)
            assert result.json()['gate']['allowed']
            saved = await c.get(url)
            assert saved.json() == result.json()
            assert len(saved.json()['packet']['decisions']) == 6
            assert saved.json()['packet']['analyses'] == []
    asyncio.run(check())


def test_session_owner_origin_host_and_authority_boundaries(tmp_path):
    async def check():
        app = create_app(tmp_path / 'owners.sqlite3')
        async with client(app) as owner, client(app) as other:
            assert (await owner.post('/api/packets', json=initial())).status_code == 401
            await owner.post('/api/session', json={})
            response = await owner.post('/api/packets', json=initial())
            url = '/api/packets/' + response.json()['packet']['id']
            await other.post('/api/session', json={})
            assert (await other.get(url)).status_code == 404
            decision = {'expected_revision': 1, 'rationale': 'Other browser'}
            assert (await other.post(url + '/scope', json=decision)).status_code == 404
            assert (await owner.post(url + '/scope', json={**decision, 'actor': 'forged-owner'})).status_code == 422
            assert (await owner.post(url + '/scope', json=decision, headers={'Origin': 'https://evil.invalid'})).status_code == 403
            assert (await owner.post(url + '/scope', json=decision, headers={'X-BidDelta-Request': ''})).status_code == 403
            assert (await owner.get(url, headers={'Host': 'evil.invalid'})).status_code == 400
            assert (await owner.get('/api/fixtures/not-a-fixture')).status_code == 404
            # No rejected operation appended a decision.
            assert (await owner.get(url)).json()['packet']['decisions'] == []
    asyncio.run(check())


@pytest.mark.parametrize('problem', ['malformed-base64', 'not-pdf', 'unknown-page', 'missing-page', 'unknown-evidence', 'duplicate-kind', 'unknown-amendment-page'])
def test_invalid_upload_or_mapping_rejected_without_partial_packet(tmp_path, problem):
    async def check():
        app = create_app(tmp_path / 'bad.sqlite3')
        async with client(app) as c:
            await c.post('/api/session', json={})
            body = initial()
            if problem == 'malformed-base64': body['uploads'][0]['content_base64'] = '!!!'
            if problem == 'not-pdf': body['uploads'][0]['content_base64'] = base64.b64encode(b'not a PDF').decode()
            if problem == 'unknown-page': body['mappings'][0]['requirement_pages'] = [99]
            if problem == 'missing-page': body['mappings'].pop()
            if problem == 'unknown-evidence': body['mappings'][0]['evidence_ids'] = ['not-real']
            if problem == 'duplicate-kind': body['uploads'][1] = body['uploads'][0]
            if problem == 'unknown-amendment-page':
                result = await c.post('/api/packets', json=body)
                url = '/api/packets/' + result.json()['packet']['id']
                bad = await c.post(url + '/amendments', json={'expected_revision': 1,
                    'upload': upload('amendment', 'amendment.pdf'),
                    'changes': [{'page': 99, 'description': 'Invalid', 'requirement_ids': []}]})
                assert bad.status_code == 422
                assert (await c.get(url)).json() == result.json()
            else:
                result = await c.post('/api/packets', json=body)
                assert result.status_code == 422, result.text
                import sqlite3
                with sqlite3.connect(tmp_path / 'bad.sqlite3') as db:
                    assert db.execute('SELECT count(*) FROM snapshots').fetchone()[0] == 0
    asyncio.run(check())


def test_missing_evidence_and_zero_change_scope_still_block_correctly(tmp_path):
    async def check():
        async with client(create_app(tmp_path / 'evidence.sqlite3')) as c:
            await c.post('/api/session', json={})
            body = initial()
            body['uploads'][2]['content_base64'] = base64.b64encode(b'evidence_id,status,note\ne1,missing,Synthetic gap\n').decode()
            result = await c.post('/api/packets', json=body)
            url = '/api/packets/' + result.json()['packet']['id']
            decision = {'expected_revision': 1, 'rationale': 'Checked source scope'}
            await c.post(url + '/scope', json=decision)
            assert (await c.post(url + '/items/i-1/approve', json=decision)).status_code == 422
            assert 'unresolved_evidence:e1' in (await c.get(url)).json()['gate']['blockers']
            result = await c.post(url + '/amendments', json={'expected_revision': 1,
                        'upload': upload('amendment', 'amendment.pdf'), 'changes': []})
            assert 'scope_confirmation_required' in result.json()['gate']['blockers']
            assert not result.json()['gate']['allowed']
    asyncio.run(check())


def test_request_body_bound_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr('biddelta.api.MAX_BODY', 100)
    async def check():
        async with client(create_app(tmp_path / 'bounds.sqlite3')) as c:
            await c.post('/api/session', json={})
            assert (await c.post('/api/preview', content=b'x' * 101)).status_code == 413
    asyncio.run(check())


def test_quoted_csv_identity_preserved_in_preview_and_packet(tmp_path):
    async def check():
        async with client(create_app(tmp_path / 'quoted.sqlite3')) as c:
            await c.post('/api/session', json={})
            body = initial()
            body['uploads'][2]['content_base64'] = base64.b64encode(b'evidence_id,status,note\n"e,1",asserted,"Quoted, synthetic"\n').decode()
            body['mappings'][0]['evidence_ids'] = ['e,1']
            preview = await c.post('/api/preview', json={'uploads': body['uploads']})
            assert preview.json()['evidence_ids'] == ['e,1']
            result = await c.post('/api/packets', json=body)
            assert result.status_code == 201
            assert result.json()['packet']['evidence'][0]['evidence_id'] == 'e,1'
    asyncio.run(check())
