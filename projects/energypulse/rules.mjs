import { ASSETS } from './fixture.mjs';

export const METRICS = {
  temperature: { unit: '°C', direction: 'above', limitKey: 'temperatureLimit' },
  vibration: { unit: 'mm/s', direction: 'above', limitKey: 'vibrationLimit' },
  pressure: { unit: 'bar', direction: 'below', limitKey: 'pressureFloor' },
};

export function evaluateReading(reading, asset) {
  if (!asset || reading.assetId !== asset.id) return [];
  return Object.entries(METRICS).flatMap(([metric, rule]) => {
    const value = reading[metric];
    const limit = asset[rule.limitKey];
    if (!Number.isFinite(value) || !Number.isFinite(limit)) return [];
    const triggered = rule.direction === 'above' ? value > limit : value < limit;
    return triggered ? [{ id: `${reading.id}-${metric}`, readingId: reading.id, assetId: asset.id,
      timestamp: reading.timestamp, metric, value, limit, unit: rule.unit, direction: rule.direction }] : [];
  });
}

export function selectReadings(readings, { assetId, day }) {
  return readings.filter((r) => r.assetId === assetId && (!day || r.timestamp.slice(0, 10) === day))
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

export function detectAnomalies(readings, assetId) {
  const asset = ASSETS.find((item) => item.id === assetId);
  if (!asset) return [];
  return readings.flatMap((reading) => evaluateReading(reading, asset));
}
