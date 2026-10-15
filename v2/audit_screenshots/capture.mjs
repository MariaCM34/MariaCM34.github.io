// Capture source-backed local UI states for the release-readiness review.
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const output = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({headless: true,
  ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {})});
const captures = [
  ['energy', 'http://127.0.0.1:8876/', async (page, mobile) => {
    await page.getByText('Loaded from SQLite through the API.').waitFor();
    if (mobile) {
      await page.locator('#asset').selectOption('CHILL-C301');
      await page.locator('#metric').selectOption('pressure');
      await page.getByText('10/12 · 83%').waitFor();
    } else {
      await page.locator('#incidents button').first().click();
      await page.locator('#lineage').getByText('value: 84.3 C').waitFor();
    }
  }],
  ['analytics', 'http://127.0.0.1:8766/', async page => {
    await page.getByText(/accepted source rows/).waitFor();
    await page.locator('#run').click();
    await page.locator('#result:not([hidden])').waitFor();
  }],
  ['migration', 'http://127.0.0.1:8767/', async page => {
    await page.getByText('17 of 17 cases').waitFor();
    await page.locator('#status').selectOption('FAIL');
    await page.locator('.case:visible').first().getByRole('link').click();
    await page.getByText(/A-001\.amount: expected 10\.00; actual 11\.00/).waitFor();
  }],
  ['showcase', 'http://127.0.0.1:8768/', async page => {
    await page.getByText('Frozen evidence loaded from executed local runs.').waitFor();
  }],
];
try {
  for (const [name, url, prepare] of captures) {
    for (const [size, viewport] of Object.entries({desktop: {width: 1280, height: 900}, mobile: {width: 390, height: 844}})) {
      const page = await browser.newPage({viewport, deviceScaleFactor: 1});
      const response = await page.goto(url);
      if (response.status() !== 200) throw new Error(`${name}: HTTP ${response.status()}`);
      await prepare(page, size === 'mobile');
      await page.screenshot({path: path.join(output, `${name}-${size}.png`), fullPage: true});
      console.log(`${name}-${size}: ${await page.title()}; no overflow=${await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)}`);
      await page.close();
    }
  }
} finally {
  await browser.close();
}
