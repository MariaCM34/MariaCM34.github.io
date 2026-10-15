import test from 'node:test';
import assert from 'node:assert/strict';
import { ASSETS, DAYS, generateReadings } from '../fixture.mjs';
import { detectAnomalies, evaluateReading, selectReadings } from '../rules.mjs';

const readings = generateReadings();

test('fixture is deterministic, complete and timestamped in UTC', () => {
  assert.deepEqual(generateReadings(), readings);
  assert.equal(readings.length, 3 * 3 * 24);
  assert.equal(new Set(readings.map((r) => r.id)).size, readings.length);
  assert.ok(readings.every((r) => r.timestamp.endsWith('Z')));
});

test('injected threshold breach produces an explainable anomaly', () => {
  const item = readings.find((r) => r.id === 'pump-a-2026-09-14-08');
  assert.deepEqual(evaluateReading(item, ASSETS[0]).map(({ metric, value, limit, direction }) => ({ metric, value, limit, direction })),
    [{ metric: 'temperature', value: 83.4, limit: 78, direction: 'above' }]);
});

test('normal values and equality to a threshold do not trigger false positives', () => {
  const normal = readings.find((r) => r.id === 'pump-a-2026-09-14-07');
  assert.equal(evaluateReading(normal, ASSETS[0]).length, 0);
  assert.equal(evaluateReading({ ...normal, temperature: 78, vibration: 5.2, pressure: 48 }, ASSETS[0]).length, 0);
});

test('empty time window yields no readings or alerts', () => {
  const empty = selectReadings(readings, { assetId: 'pump-a', day: '2026-09-20' });
  assert.deepEqual(empty, []);
  assert.deepEqual(detectAnomalies(empty, 'pump-a'), []);
});

test('asset selection isolates exactly one asset and its incidents', () => {
  const pump = selectReadings(readings, { assetId: 'pump-a', day: DAYS[0] });
  const chiller = selectReadings(readings, { assetId: 'chiller-c', day: DAYS[0] });
  assert.equal(pump.length, 24);
  assert.equal(chiller.length, 24);
  assert.ok(pump.every((r) => r.assetId === 'pump-a'));
  assert.ok(chiller.every((r) => r.assetId === 'chiller-c'));
  assert.deepEqual(detectAnomalies(pump, 'pump-a').map((a) => a.metric), ['temperature']);
  assert.deepEqual(detectAnomalies(chiller, 'chiller-c').map((a) => a.metric), ['pressure']);
});

test('all injected incidents are found, with no unrelated alerts', () => {
  const counts = ASSETS.map((asset) => detectAnomalies(selectReadings(readings, { assetId: asset.id, day: '' }), asset.id).length);
  assert.deepEqual(counts, [3, 3, 3]);
});
