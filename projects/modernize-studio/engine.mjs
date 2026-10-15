// A deliberately small, exact-template demonstration. This is not a SQL parser.
export const samples = [
  {
    id: 'daily-sales',
    title: 'Daily sales',
    input: `-- Synthetic retail fixture: daily sales\nSELECT TOP 10 [sale_date], SUM(ISNULL([net_amount], 0)) AS net_sales\nFROM [demo_sales]\nGROUP BY [sale_date]\nORDER BY net_sales DESC;`,
    output: `-- Synthetic retail fixture: daily sales\nSELECT sale_date, SUM(COALESCE(net_amount, 0)) AS net_sales\nFROM demo_sales\nGROUP BY sale_date\nORDER BY net_sales DESC\nLIMIT 10;`,
    changes: ['TOP 10 → LIMIT 10', '[identifier] → identifier', 'ISNULL → COALESCE'],
    warning: 'Check sort ties before comparing a top-10 result.'
  },
  {
    id: 'null-fallback',
    title: 'Null fallback',
    input: `-- 'ISNULL' in this comment and string stays unchanged\nSELECT [order_id], ISNULL([region], 'ISNULL unknown') AS region\nFROM [demo_orders];`,
    output: `-- 'ISNULL' in this comment and string stays unchanged\nSELECT order_id, COALESCE(region, 'ISNULL unknown') AS region\nFROM demo_orders;`,
    changes: ['[identifier] → identifier', 'ISNULL → COALESCE'],
    warning: 'Compare target string collation and null semantics.'
  },
  {
    id: 'active-orders',
    title: 'Active orders',
    input: `-- Synthetic order status\nSELECT [order_id], [customer_id], [amount]\nFROM [demo_orders]\nWHERE [status] = 'active';`,
    output: `-- Synthetic order status\nSELECT order_id, customer_id, amount\nFROM demo_orders\nWHERE status = 'active';`,
    changes: ['[identifier] → identifier'],
    warning: 'Confirm source and target schemas, types, and row-level filters.'
  }
];

export function convert(input) {
  const normalized = String(input).replace(/\r\n/g, '\n').trim();
  const sample = samples.find(item => item.input === normalized);
  if (!sample) {
    return { ok: false, message: 'Outside the three reviewed templates. No conversion was attempted; inspect the SQL manually.' };
  }
  return { ok: true, sample };
}

export function compareRows(source, target) {
  const summarize = rows => ({
    count: rows.length,
    amount: rows.reduce((sum, row) => sum + (Number(row.amount) || 0), 0),
    nulls: rows.filter(row => row.amount == null).length,
    duplicates: rows.length - new Set(rows.map(row => row.id)).size,
    records: rows.map(row => `${row.id}:${row.amount ?? 'NULL'}`).sort().join('|')
  });
  const a = summarize(source), b = summarize(target);
  return [
    { name: 'Row count', pass: a.count === b.count, source: a.count, target: b.count },
    { name: 'Amount total', pass: a.amount === b.amount, source: a.amount, target: b.amount },
    { name: 'Null count', pass: a.nulls === b.nulls, source: a.nulls, target: b.nulls },
    { name: 'Duplicate IDs', pass: a.duplicates === b.duplicates, source: a.duplicates, target: b.duplicates },
    { name: 'Record equivalence', pass: a.records === b.records, source: a.records, target: b.records }
  ];
}
