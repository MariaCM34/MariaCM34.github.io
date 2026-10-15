import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
});
const url = process.env.ANALYTICS_URL || 'http://127.0.0.1:8766/';
try {
  for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const response = await page.goto(url);
    assert.equal(response.status(), 200);
    await page.getByText(/accepted source rows/).waitFor();
    await page.locator('#run').click();
    await page.locator('#result:not([hidden])').waitFor();
    assert.match(await page.locator('#sql').innerText(), /FROM fct_order_lines/);
    assert.ok(await page.locator('#tbody tr').count() > 0);
    assert.ok(await page.locator('#chart').locator('div').count() > 0);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await page.locator('#metric').selectOption('net_sales_by_category');
    await page.locator('#category').selectOption('tools');
    await page.locator('#run').click();
    await page.locator('#result:not([hidden])').waitFor();
    assert.match(await page.locator('#params').innerText(), /tools/);
    assert.match(await page.locator('#definition').innerText(), /category/);
    await page.locator('#end').fill('2026-04-01');
    await page.locator('#run').click();
    await page.locator('#message.error').waitFor();
    assert.equal(await page.locator('#result').isHidden(), true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await page.close();
  }
  console.log('Governed Analytics browser E2E: desktop and mobile executed-query flow passed');
} finally {
  await browser.close();
}
