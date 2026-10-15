// Run against a seeded local API: ENERGY_URL=http://127.0.0.1:8876/ node browser.mjs
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const url = process.env.ENERGY_URL || 'http://127.0.0.1:8876/';
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
});
try {
  for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const response = await page.goto(url);
    assert.equal(response.status(), 200);
    await page.getByText('Loaded from SQLite through the API.').waitFor();
    assert.equal(await page.locator('#received').innerText(), '12');
    assert.match(await page.locator('#chart svg').getAttribute('aria-label'), /12 UTC observations/);
    await page.locator('#incidents button').first().click();
    await page.locator('#lineage').getByText('value: 84.3 C').waitFor();
    assert.match(await page.locator('#lineage').innerText(), /EVT-PUMP-A102-20261015T0115Z-TEMPERATURE/);
    await page.locator('#asset').selectOption('CHILL-C301');
    await page.locator('#metric').selectOption('pressure');
    await page.getByText('10/12 · 83%').waitFor();
    assert.equal(await page.locator('#heatmap button.partial').count(), 2);
    assert.match(await page.locator('#chart svg').getAttribute('aria-label'), /2 missing intervals/);
    assert.equal(await page.locator('#chart svg polyline').count(), 2);
    await page.locator('#language').focus();
    await page.keyboard.press('Enter');
    await page.getByText('Cada incidente tiene un origen.').waitFor();
    await page.getByText('Datos cargados desde SQLite mediante API.').waitFor();
    assert.equal(await page.locator('html').getAttribute('lang'), 'es');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await page.close();
  }
  console.log('EnergyPulse browser E2E: desktop and mobile source-backed flow passed');
} finally {
  await browser.close();
}
