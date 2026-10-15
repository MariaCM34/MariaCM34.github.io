// Pure, deterministic analysis over the bundled synthetic fixture. No SQL is executed.
export const INTENTS = Object.freeze({
  trend: {en:'Monthly net sales',es:'Ventas netas por mes',sql:'SELECT month(date) AS month, SUM(net_amount) AS net_sales FROM synthetic_orders WHERE date BETWEEN :start AND :end GROUP BY month(date) ORDER BY month;'},
  products: {en:'Top products by net sales',es:'Productos por ventas netas',sql:'SELECT product, SUM(net_amount) AS net_sales FROM synthetic_orders WHERE date BETWEEN :start AND :end GROUP BY product ORDER BY net_sales DESC;'},
  cancellations: {en:'Cancellation rate by month',es:'Tasa de cancelación por mes',sql:"SELECT month(date) AS month, COUNT(*) AS orders, SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled FROM synthetic_orders WHERE date BETWEEN :start AND :end GROUP BY month(date) ORDER BY month;"},
  revenue: {en:'Gross and net sales',es:'Ventas brutas y netas',sql:'SELECT SUM(gross_amount) AS gross_sales, SUM(net_amount) AS net_sales FROM synthetic_orders WHERE date BETWEEN :start AND :end;'},
  comparison: {en:'Category comparison',es:'Comparación por categoría',sql:'SELECT category, SUM(net_amount) AS net_sales FROM synthetic_orders WHERE date BETWEEN :start AND :end GROUP BY category ORDER BY net_sales DESC;'}
});

const RULES = [
  ['cancellations', /\b(cancel|cancelled|cancellation|cancelaciones|cancelados|canceladas|anulaci[oó]n|anulados)\b/i],
  ['products', /\b(top|product|products|producto|productos|m[aá]s vendidos)\b/i],
  ['comparison', /\b(categor|category|categories|compare|comparison|compar|segment)/i],
  ['trend', /\b(trend|monthly|month|mes|meses|mensual|tendencia|evoluci[oó]n)\b/i],
  ['revenue', /\b(gross|net|revenue|sales|ventas|ingresos|brutas|brutos|netas|netos)\b/i]
];

export function mapIntent(question) {
  const q = String(question ?? '').trim();
  if (!q || q.length > 180) return null;
  if (/\b(drop|delete|update|insert|alter|truncate|exec|execute|borrar|eliminar)\b/i.test(q)) return null;
  return RULES.find(([, regex]) => regex.test(q))?.[0] ?? null;
}

export function validateDates(start, end) {
  const pattern = /^\d{4}-\d{2}-\d{2}$/;
  const valid = value => pattern.test(value) && !Number.isNaN(Date.parse(`${value}T00:00:00Z`)) && new Date(`${value}T00:00:00Z`).toISOString().slice(0,10) === value;
  if (!valid(start) || !valid(end) || start > end) throw new Error('invalid_date_range');
}

export function analyze(orders, intent, start, end) {
  if (!Object.hasOwn(INTENTS, intent)) throw new Error('unsupported_intent');
  validateDates(start, end);
  if (!Array.isArray(orders)) throw new Error('invalid_data');
  const selected = orders.filter(o => o.date >= start && o.date <= end);
  const money = o => {
    if (!Number.isFinite(o.quantity) || o.quantity < 0 || !Number.isFinite(o.unitPrice) || o.unitPrice < 0 || !Number.isFinite(o.discount) || o.discount < 0) return {gross:0, net:0, invalid:true};
    if (o.status === 'cancelled') return {gross:0,net:0,invalid:false};
    if (o.status === 'returned') return {gross:0,net:-(o.quantity * o.unitPrice - o.discount),invalid:false};
    if (o.status === 'completed') return {gross:o.quantity * o.unitPrice,net:o.quantity * o.unitPrice - o.discount,invalid:false};
    return {gross:0,net:0,invalid:true};
  };
  const invalidRows = selected.filter(o => money(o).invalid).length;
  const aggregate = rows => rows.reduce((a,o) => { const v=money(o); a.gross+=v.gross; a.net+=v.net; a.count++; if(o.status==='cancelled') a.cancelled++; return a; },{gross:0,net:0,count:0,cancelled:0});
  let groups;
  if (intent === 'revenue') groups = [{key:'All selected dates',...aggregate(selected)}];
  else {
    const key = o => intent === 'products' ? o.product : intent === 'comparison' ? o.category : o.date.slice(0,7);
    const grouped = new Map();
    for (const o of selected) { const k=key(o); if (!grouped.has(k)) grouped.set(k,[]); grouped.get(k).push(o); }
    groups = [...grouped].map(([k,rows])=>({key:k,...aggregate(rows)}));
    groups.sort((a,b) => ['trend','cancellations'].includes(intent) ? a.key.localeCompare(b.key) : b.net-a.net || a.key.localeCompare(b.key));
  }
  return {intent, start, end, rowsScanned:selected.length, fixtureRows:orders.length, invalidRows, groups, total:aggregate(selected), filters:`date >= ${start} AND date <= ${end}`};
}
