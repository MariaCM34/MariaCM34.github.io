import test from 'node:test';
import assert from 'node:assert/strict';
import { samples, convert, compareRows } from './engine.mjs';

test('all three reviewed examples produce their documented outputs', () => {
  for (const sample of samples) assert.equal(convert(sample.input).sample.output, sample.output);
});
test('unsupported dialect constructs are refused, never guessed', () => {
  assert.equal(convert('SELECT * FROM x WITH (NOLOCK);').ok, false);
  assert.equal(convert(samples[0].input + '\nDELETE FROM x;').ok, false);
});
test('quotes and comments remain unchanged in the reviewed example', () => {
  const output = convert(samples[1].input).sample.output;
  assert.match(output, /-- 'ISNULL' in this comment/);
  assert.match(output, /'ISNULL unknown'/);
  assert.match(output, /COALESCE\(region/);
});
test('same rows pass each validation check', () => {
  const rows = [{ id: 1, amount: 5 }, { id: 2, amount: null }];
  assert.ok(compareRows(rows, rows).every(check => check.pass));
});
test('mismatched rows fail the appropriate checks', () => {
  const checks = compareRows([{ id: 1, amount: 5 }], [{ id: 1, amount: 7 }, { id: 1, amount: null }]);
  assert.deepEqual(checks.filter(check => !check.pass).map(check => check.name), ['Row count', 'Amount total', 'Null count', 'Duplicate IDs', 'Record equivalence']);
});
