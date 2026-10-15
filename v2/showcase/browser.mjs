import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
});
const url = process.env.SHOWCASE_URL || 'http://127.0.0.1:8768/';
try {
  for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    assert.equal((await page.goto(url)).status(), 200);
    await page.getByText('Frozen evidence loaded from executed local runs.').waitFor();
    assert.equal(await page.locator('#energy-count').innerText(), '106');
    assert.equal((await page.locator('#analytics-count').innerText()).replace(/\D/g, ''), '12723');
    assert.equal(await page.locator('#migration-count').innerText(), '17');
    assert.match(await page.locator('#energy-chart').getAttribute('aria-label'), /PUMP-A102 temperature/);
    await page.locator('#energy-signal').selectOption('CHILL-C301|pressure');
    assert.match(await page.locator('#energy-chart').getAttribute('aria-label'), /2 missing slots/);
    assert.equal(await page.locator('#energy-chart polyline').count(), 2);
    await page.locator('#analytics-metric').selectOption('net_sales_by_category');
    await page.locator('#analytics-currency').selectOption('COP');
    assert.match(await page.locator('#analytics-definition').innerText(), /category/);
    assert.match(await page.locator('#analytics-params').textContent(), /COP/);
    await page.locator('#migration-filter').selectOption('FAIL');
    assert.equal(await page.locator('#migration-cases .case').count(), 2);
    assert.match(await page.locator('#migration-detail').innerText(), /A-001\.amount: expected 10\.00; actual 11\.00/);
    await page.locator('#language').focus();
    await page.keyboard.press('Enter');
    await page.getByText('Evidencia congelada cargada desde ejecuciones locales.').waitFor();
    assert.equal(await page.locator('html').getAttribute('lang'), 'es');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    assert.deepEqual(errors, []);
    await page.close();
  }
  const failure = await browser.newPage();
  await failure.route('**/evidence.json', route => route.fulfill({ status: 503, body: '' }));
  await failure.goto(url);
  await failure.getByText(/Evidence export unavailable/).waitFor();
  assert.equal(await failure.locator('#energy-count').innerText(), '—');
  await failure.close();
  console.log('V2 static showcase browser E2E: desktop, mobile, interactions and failure state passed');
} finally {
  await browser.close();
}
