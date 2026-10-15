import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
});
const url = process.env.MIGRATION_URL || 'http://127.0.0.1:8767/';
try {
  for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const response = await page.goto(url);
    assert.equal(response.status(), 200);
    await page.getByText('17 of 17 cases').waitFor();
    await page.locator('#status').selectOption('FAIL');
    await page.getByText('2 of 17 cases').waitFor();
    assert.equal(await page.locator('.case:visible').count(), 2);
    await page.locator('.case:visible').first().getByRole('link').click();
    await page.getByText(/A-001\.amount: expected 10\.00; actual 11\.00/).waitFor();
    assert.match(await page.locator('body').innerText(), /SQLite/);
    assert.match(await page.locator('body').innerText(), /DuckDB/);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await page.close();
  }
  console.log('Migration Assurance browser E2E: desktop and mobile executed-diff flow passed');
} finally {
  await browser.close();
}
