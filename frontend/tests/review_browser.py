"""Offline browser -> Vite proxy -> FastAPI -> SQLite vertical-slice check."""
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
    page.reload()
    idle()
    expect(page.get_by_role('heading', name='Packet · revision 2', exact=True)).to_be_visible()
    expect(page.get_by_role('status')).to_have_text('Reviewed gate open')
    expect(page.get_by_text('Fresh review against synthetic new deadline', exact=False)).to_be_visible()
    # Check small-screen layout without starting another semantic journey.
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path='work/p0b-review-mobile.png', full_page=True)
    assert not errors, errors
    assert not external, external
    assert page.get_by_role('alert').count() == 0
    print('PASS: browser upload/preview -> manual mappings -> initial approvals -> amendment -> selective staleness -> impact -> scope -> fresh approval -> gate open -> reload retained.')
    print('PASS: mobile layout has no horizontal overflow; no browser runtime errors or external/provider requests.')
    context.close()
    browser.close()
