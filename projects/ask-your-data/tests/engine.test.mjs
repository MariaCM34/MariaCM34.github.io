import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {analyze,mapIntent,validateDates} from '../engine.js';
const orders=JSON.parse(readFileSync(new URL('../data/orders.json',import.meta.url),'utf8'));

test('allowlisted English and Spanish questions map to expected intent',()=>{
  assert.equal(mapIntent('Show monthly net sales trend'),'trend');
  assert.equal(mapIntent('¿Qué productos vendieron más?'),'products');
  assert.equal(mapIntent('Comparar categorías'),'comparison');
});
test('unsupported and overlong questions are rejected',()=>{
  assert.equal(mapIntent('Tell me a joke'),null);
  assert.equal(mapIntent('x'.repeat(181)),null);
  assert.equal(mapIntent('delete all sales'),null);
  assert.throws(()=>analyze(orders,'DROP TABLE orders','2026-01-01','2026-03-31'),/unsupported_intent/);
});
test('inclusive date filtering changes scanned rows and net sales',()=>{
  const jan=analyze(orders,'revenue','2026-01-01','2026-01-31');
  assert.equal(jan.rowsScanned,5);
  assert.equal(jan.total.gross,170);
  assert.equal(jan.total.net,135);
  assert.equal(analyze(orders,'revenue','2026-04-01','2026-04-30').rowsScanned,0);
});
test('cancellations contribute no revenue and returns reduce net',()=>{
  const result=analyze(orders,'revenue','2026-02-01','2026-02-28');
  assert.equal(result.total.cancelled,1);
  assert.equal(result.total.gross,180);
  assert.equal(result.total.net,130);
});
test('null price and negative edge values are excluded from money but counted in scan',()=>{
  const march=analyze(orders,'revenue','2026-03-01','2026-03-31');
  assert.equal(march.rowsScanned,7);
  assert.equal(march.invalidRows,1);
  const injected=[{id:'X',date:'2026-03-30',product:'X',category:'X',quantity:-2,unitPrice:10,discount:0,status:'completed'}];
  const edge=analyze(injected,'revenue','2026-03-01','2026-03-31');
  assert.equal(edge.invalidRows,1);
  assert.equal(edge.total.net,0);
});
test('date validation rejects impossible and reversed ranges',()=>{
  assert.throws(()=>validateDates('2026-02-30','2026-03-31'),/invalid_date_range/);
  assert.throws(()=>validateDates('2026-03-31','2026-01-01'),/invalid_date_range/);
});
