"""Offline evidence correction/recheck through the authenticated local API."""
import asyncio
import base64
import pytest
from biddelta.api import create_app
from biddelta.store import Store
from test_workflow_api import client, initial


def correction(revision=1, status='missing', **extra):
    return {'expected_revision': revision, 'evidence_id': 'e1', 'status': status,
            'note': 'Synthetic owner correction', 'rationale': 'Synthetic source rechecked', **extra}


async def create(c):
    await c.post('/api/session', json={})
    result = await c.post('/api/packets', json=initial())
    assert result.status_code == 201
    view = result.json()
    return '/api/packets/' + view['packet']['id'], view


async def approve_initial(c, url):
    body = {'expected_revision': 1, 'rationale': 'Synthetic initial review'}
    assert (await c.post(url + '/scope', json=body)).status_code == 200
    for item in ('i-1', 'i-2'):
        result = await c.post(url + '/items/' + item + '/approve', json=body)
        assert result.status_code == 200
    return result.json()


def test_correction_history_invalidation_scope_and_fresh_approval(tmp_path, monkeypatch):
    monkeypatch.delenv('NEBIUS_API_KEY', raising=False)
    async def check():
        path = tmp_path / 'evidence.sqlite3'
        async with client(create_app(path)) as c:
            url, _ = await create(c)
            original = await approve_initial(c, url)
            assert original['gate']['allowed']
            result = await c.post(url + '/evidence-revisions', json=correction())
            assert result.status_code == 200
            revised = result.json(); p = revised['packet']
            assert p['revision'] == 2
            assert [i['approval_state'] for i in p['items']] == ['stale', 'needs_scope_confirmation']
            assert p['evidence'][0] == original['packet']['evidence'][0]
            assert p['decisions'][:-1] == original['packet']['decisions']
            assert p['decisions'][-1]['action'] == 'evidence'
            assert p['audit'][-1]['action'] == 'evidence'
            assert 'unresolved_evidence:e1' in revised['gate']['blockers']
            assert not revised['gate']['allowed']
            decision = {'expected_revision': 2, 'rationale': 'Rechecked synthetic scope'}
            assert (await c.post(url + '/items/i-1/approve', json=decision)).status_code == 422
            result = await c.post(url + '/scope', json=decision)
            assert [i['approval_state'] for i in result.json()['packet']['items']] == ['stale', 'approved']
            assert (await c.post(url + '/items/i-1/approve', json=decision)).status_code == 422
            result = await c.post(url + '/evidence-revisions', json=correction(2, 'asserted', note='Synthetic correction supplied'))
            p = result.json()['packet']
            assert p['revision'] == 3
            assert [i['approval_state'] for i in p['items']] == ['stale', 'needs_scope_confirmation']
            assert [e['revision'] for e in p['evidence']] == [1, 2, 3]
            assert len({e['source_span_id'] for e in p['evidence']}) == 1
            assert 'unresolved_evidence:e1' not in result.json()['gate']['blockers']
            assert not result.json()['gate']['allowed']  # Asserted never means approved.
            decision['expected_revision'] = 3
            assert (await c.post(url + '/scope', json=decision)).status_code == 200
            result = await c.post(url + '/items/i-1/approve', json=decision)
            assert result.json()['gate']['allowed']
            final = result.json()
            # An older editor cannot overwrite newer evidence or fresh review decisions.
            assert (await c.post(url + '/evidence-revisions', json=correction(2))).status_code == 409
            assert (await c.get(url)).json() == final
            stored = Store(path).get(p['id'], p['owner_id'])
            assert stored.evidence[-1].status == 'asserted'
            csv = next(d for d in stored.documents if d.kind == 'evidence_register')
            assert Store(path).source_bytes(p['id'], csv.id, p['owner_id']) == base64.b64decode(initial()['uploads'][2]['content_base64'])
    asyncio.run(check())


@pytest.mark.parametrize('status', ['missing', 'conflict'])
def test_unresolved_correction_blocks_completion(tmp_path, status):
    async def check():
        async with client(create_app(tmp_path / 'blocked.sqlite3')) as c:
            url, _ = await create(c)
            result = await c.post(url + '/evidence-revisions', json=correction(status=status))
            assert result.status_code == 200
            decision = {'expected_revision': 2, 'rationale': 'Synthetic scope checked'}
            await c.post(url + '/scope', json=decision)
            assert (await c.post(url + '/items/i-1/approve', json=decision)).status_code == 422
            assert 'unresolved_evidence:e1' in (await c.get(url)).json()['gate']['blockers']
    asyncio.run(check())


def test_correction_ownership_and_request_boundary(tmp_path):
    async def check():
        app = create_app(tmp_path / 'owners.sqlite3')
        async with client(app) as c, client(app) as other:
            url, original = await create(c)
            route = url + '/evidence-revisions'
            assert (await other.post(route, json=correction())).status_code == 401
            await other.post('/api/session', json={})
            assert (await other.post(route, json=correction())).status_code == 404
            assert (await c.post(route, json=correction(), headers={'Origin': 'https://evil.invalid'})).status_code == 403
            assert (await c.post(route, json=correction(), headers={'X-BidDelta-Request': ''})).status_code == 403
            assert (await c.get(url)).json() == original
    asyncio.run(check())


@pytest.mark.parametrize('extra', [{'evidence_id': 'unknown'}, {'status': 'approved'},
    {'note': '  '}, {'rationale': '  '}, {'source_span_id': 'forged'}, {'actor': 'forged'}],
    ids=['unknown-evidence', 'invalid-status', 'empty-note', 'empty-rationale', 'forged-source', 'forged-owner'])
def test_invalid_correction_preserves_state(tmp_path, extra):
    async def check():
        async with client(create_app(tmp_path / 'invalid.sqlite3')) as c:
            url, original = await create(c)
            result = await c.post(url + '/evidence-revisions', json=correction(**extra))
            assert result.status_code == 422
            assert (await c.get(url)).json() == original
    asyncio.run(check())


def test_two_editors_cannot_overwrite_same_evidence_revision(tmp_path):
    async def check():
        async with client(create_app(tmp_path / 'race.sqlite3')) as c:
            url, _ = await create(c)
            results = await asyncio.gather(
                c.post(url + '/evidence-revisions', json=correction(status='missing')),
                c.post(url + '/evidence-revisions', json=correction(status='conflict')))
            assert sorted(r.status_code for r in results) == [200, 409]
            packet = (await c.get(url)).json()['packet']
            assert packet['revision'] == 2 and len(packet['evidence']) == 2
            assert len(packet['decisions']) == 1
    asyncio.run(check())
