// Every reading is deterministic and synthetic. No external telemetry is loaded.
export const ASSETS = [
  { id: 'pump-a', name: 'Pump A', zone: 'North utility hall', temperatureLimit: 78, vibrationLimit: 5.2, pressureFloor: 48, base: [63, 2.3, 62] },
  { id: 'compressor-b', name: 'Compressor B', zone: 'East line', temperatureLimit: 86, vibrationLimit: 6.2, pressureFloor: 55, base: [70, 3.1, 68] },
  { id: 'chiller-c', name: 'Chiller C', zone: 'Cooling bay', temperatureLimit: 71, vibrationLimit: 4.8, pressureFloor: 43, base: [57, 2.0, 56] },
];

export const DAYS = ['2026-09-14', '2026-09-15', '2026-09-16'];
export const SAMPLE_INTERVAL = '1 hour';

const INCIDENTS = {
  'pump-a|2026-09-14|08': { temperature: 83.4 },
  'pump-a|2026-09-15|13': { pressure: 42.1 },
  'pump-a|2026-09-16|17': { vibration: 5.9 },
  'compressor-b|2026-09-14|12': { vibration: 7.0 },
  'compressor-b|2026-09-15|09': { temperature: 91.2 },
  'compressor-b|2026-09-16|15': { pressure: 50.7 },
  'chiller-c|2026-09-14|18': { pressure: 38.5 },
  'chiller-c|2026-09-15|11': { vibration: 5.4 },
  'chiller-c|2026-09-16|07': { temperature: 75.8 },
};

const round = (n) => Math.round(n * 10) / 10;

export function generateReadings() {
  return ASSETS.flatMap((asset, assetIndex) => DAYS.flatMap((day, dayIndex) =>
    Array.from({ length: 24 }, (_, hour) => {
      const cycle = Math.sin((hour / 24) * Math.PI * 2 + assetIndex * 0.4);
      const drift = Math.cos((hour / 12) * Math.PI + dayIndex) * 0.45;
      const values = {
        temperature: round(asset.base[0] + cycle * 2.2 + drift),
        vibration: round(asset.base[1] + cycle * 0.35 + drift * 0.16),
        pressure: round(asset.base[2] + cycle * 1.7 - drift),
      };
      Object.assign(values, INCIDENTS[`${asset.id}|${day}|${String(hour).padStart(2, '0')}`]);
      return { id: `${asset.id}-${day}-${String(hour).padStart(2, '0')}`, assetId: asset.id,
        timestamp: `${day}T${String(hour).padStart(2, '0')}:00:00Z`, ...values };
    })));
}
