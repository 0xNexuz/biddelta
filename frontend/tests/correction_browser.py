"""One offline correction walkthrough, including existing upload/amendment flow."""
import re
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

Path('work').mkdir(exist_ok=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=shutil.which('chromium'))
    context = browser.new_context(viewport={'width': 1280, 'height': 960})
    page = context.new_page()
    errors, external = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    def route(request):
        if not request.request.url.startswith(('http://127.0.0.1:', 'http://localhost:')):
            external.append(request.request.url)
            request.abort()
        else:
            request.continue_()
    page.route('**/*', route)
    def idle():
        page.wait_for_function("document.querySelector('[aria-busy]')?.getAttribute('aria-busy') === 'false'")
    def action(name, suffix, rationale=None):
        if rationale:
            page.get_by_label('Review rationale', exact=True).fill(rationale)
        with page.expect_response(lambda r: r.url.endswith(suffix) and r.request.method == 'POST') as response:
            page.get_by_role('button', name=name, exact=True).click()
        assert response.value.status in (200, 201), response.value.text()
        idle()
    page.goto('http://127.0.0.1:5173/')
    idle()
    page.get_by_role('button', name='Use synthetic example files', exact=True).click()
    idle()
    action('Preview uploads', '/preview')
    first = page.locator('article').filter(has=page.get_by_role('heading', name='Response page 1', exact=True))
    second = page.locator('article').filter(has=page.get_by_role('heading', name='Response page 2', exact=True))
    first.get_by_label('Tender page 2', exact=True).uncheck()
    second.get_by_label('Tender page 1', exact=True).uncheck()
    second.get_by_label('e1', exact=True).uncheck()
    action('Create packet with these mappings', '/packets')
    expect(page.get_by_role('status')).to_have_text('Reviewed gate blocked')
    action('Confirm complete scope', '/scope', 'Synthetic initial inventory and mappings checked')
    action('Approve i-1 at revision 1', '/items/i-1/approve', 'Synthetic deadline claim checked')
    action('Approve i-2 at revision 1', '/items/i-2/approve', 'Synthetic quantity claim checked')
    expect(page.get_by_role('status')).to_have_text('Reviewed gate open')
    page.get_by_role('button', name='Preview synthetic amendment', exact=True).click()
    idle()
    page.get_by_label(re.compile('^r-2:')).uncheck()
    action('Record amendment and open review', '/amendments')
    expect(page.get_by_role('heading', name='i-1 · stale', exact=True)).to_be_visible()
    expect(page.get_by_role('heading', name='i-2 · needs scope confirmation', exact=True)).to_be_visible()
    expect(page.get_by_role('status')).to_have_text('Reviewed gate blocked')
    action('Record impact review', '/impact', 'Deadline affects i-1; quantity claim unchanged')
    action('Confirm complete scope', '/scope', 'Synthetic amendment inventory and all scope checked')
    expect(page.get_by_role('heading', name='i-2 · approved', exact=True)).to_be_visible()
    expect(page.get_by_role('status')).to_have_text('Reviewed gate blocked')
    action('Approve i-1 at revision 2', '/items/i-1/approve', 'Fresh review against synthetic new deadline')
    expect(page.get_by_role('status')).to_have_text('Reviewed gate open')
    def correct(status, note):
        page.get_by_role('button', name='Correct e1', exact=True).click()
        page.get_by_label('New evidence status', exact=True).select_option(status)
        page.get_by_label('Correction note', exact=True).fill(note)
        page.get_by_label('Evidence correction rationale', exact=True).fill('Synthetic owner recheck; not authenticated evidence')
        action('Save evidence revision', '/evidence-revisions')
    correct('missing', 'Synthetic evidence withdrawn for correction')
    expect(page.get_by_role('heading', name='i-1 · stale', exact=True)).to_be_visible()
    expect(page.get_by_role('heading', name='i-2 · needs scope confirmation', exact=True)).to_be_visible()
    expect(page.get_by_text('Evidence e1 is missing; correct the assertion before completing review.', exact=True)).to_be_visible()
    expect(page.get_by_role('status')).to_have_text('Reviewed gate blocked')
    action('Confirm complete scope', '/scope', 'Checked missing-evidence scope')
    page.get_by_label('Review rationale', exact=True).fill('Attempted recheck while missing')
    expect(page.get_by_role('button', name='Approve i-1 at revision 3', exact=True)).to_be_disabled()
    correct('asserted', 'Synthetic correction supplied by owner')
    expect(page.get_by_role('heading', name='i-1 · stale', exact=True)).to_be_visible()
    expect(page.get_by_role('status')).to_have_text('Reviewed gate blocked')
    action('Confirm complete scope', '/scope', 'Checked corrected evidence and unaffected quantity scope')
    expect(page.get_by_role('heading', name='i-2 · approved', exact=True)).to_be_visible()
    action('Approve i-1 at revision 4', '/items/i-1/approve', 'Fresh recheck of response against corrected owner assertion')
    expect(page.get_by_role('status')).to_have_text('Reviewed gate open')
    page.get_by_text('Evidence history for e1', exact=True).click()
    expect(page.get_by_text(re.compile('^Evidence revision 2 · missing:'))).to_be_visible()
    expect(page.get_by_text(re.compile('^Evidence revision 3 · asserted:'))).to_be_visible()
    packet_id = page.evaluate("localStorage.getItem('biddelta-packet')")
    persisted = context.request.get(f'http://127.0.0.1:5173/api/packets/{packet_id}').json()['packet']
    assert len(persisted['evidence']) == 3
    assert len({e['source_span_id'] for e in persisted['evidence']}) == 1
    assert persisted['analyses'] == []
    page.reload()
    idle()
    expect(page.get_by_role('heading', name='Packet · revision 4', exact=True)).to_be_visible()
    expect(page.get_by_role('status')).to_have_text('Reviewed gate open')
    expect(page.get_by_text('Fresh recheck of response against corrected owner assertion', exact=False)).to_be_visible()
    # Check small-screen layout without starting another semantic journey.
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path='work/p0b-correction-mobile.png', full_page=True)
    assert not errors, errors
    assert not external, external
    assert page.get_by_role('alert').count() == 0
    print('PASS: existing upload and amendment journey; evidence missing -> scope -> approval blocked -> asserted correction -> scope -> fresh approval -> gate open -> reload revision 4. Evidence history/source retained; no auto approval.')
    print('PASS: mobile layout has no horizontal overflow; no browser runtime errors or external/provider requests.')
    context.close()
    browser.close()
