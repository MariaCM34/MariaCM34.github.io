import { samples, convert, compareRows } from './engine.mjs';

const $ = id => document.getElementById(id);
let lang = 'es';
const t = {
  es: { back:'← Portafolio', eyebrow:'Demostración · SQL modernización', intro:'Un laboratorio transparente para revisar tres conversiones pequeñas de T-SQL a SQL compatible con Snowflake. Empresa y datos ficticios; la conversión funciona solo para plantillas revisadas.', notice:'Prueba determinista de alcance limitado · No es un migrador general ni ejecuta SQL', example:'Ejemplo sintético', convert:'Revisar conversión', reset:'Restablecer ejemplo', input:'Entrada T-SQL', editable:'Editable · cambios fuera de plantilla se rechazan', output:'Salida Snowflake', outputHint:'Se muestra después de revisar', changes:'Cambios explicados', risk:'Riesgos no resueltos: tipos y colación, orden en empates, nombres reservados y equivalencia en datos reales. Requieren revisión humana y pruebas en un entorno autorizado.', validation:'Validación de datos sintéticos', scenario:'Escenario', same:'Filas equivalentes', mismatch:'Introducir discrepancia', checkNote:'Esta comparación en JavaScript ilustra controles propuestos; no valida una migración real.', footer:'Arquitectura, límites y comandos reproducibles en el <a href="README.md">README del proyecto</a>. Tres ejemplos revisados; cualquier otra entrada se rechaza.', ready:'Selecciona un ejemplo y revisa la conversión. No se ha ejecutado SQL.', success:'Plantilla reconocida. Conversión determinista mostrada; verifica las diferencias y los riesgos.', unsupported:'Fuera de las tres plantillas revisadas. No se intentó ninguna conversión; revisa el SQL manualmente.', waiting:'Esperando conversión.', statusPass:'Pasa', statusFail:'Falla', warning:'Advertencia' },
  en: { back:'← Portfolio', eyebrow:'Demonstration · SQL modernization', intro:'A transparent lab for reviewing three small T-SQL to Snowflake-compatible SQL conversions. Business and data are fictional; conversion works only for reviewed templates.', notice:'Bounded deterministic proof · Not a general migrator and does not execute SQL', example:'Synthetic example', convert:'Review conversion', reset:'Reset example', input:'T-SQL input', editable:'Editable · changes outside templates are rejected', output:'Snowflake output', outputHint:'Shown after review', changes:'Explained changes', risk:'Unresolved risks: types and collation, tied sort order, reserved names, and equivalence on real data. These need human review and tests in an authorized environment.', validation:'Synthetic data validation', scenario:'Scenario', same:'Equivalent rows', mismatch:'Introduce mismatch', checkNote:'This JavaScript comparison illustrates proposed checks; it does not validate a real migration.', footer:'Architecture, limits, and reproduction commands are in the <a href="README.md">project README</a>. Three reviewed examples; all other input is rejected.', ready:'Select an example and review the conversion. No SQL has been executed.', success:'Reviewed template recognized. Deterministic output is shown; inspect changes and risks.', unsupported:'Outside the three reviewed templates. No conversion was attempted; inspect the SQL manually.', waiting:'Awaiting conversion.', statusPass:'Pass', statusFail:'Fail', warning:'Warning' }
};

for (const sample of samples) $('sample').add(new Option(sample.title, sample.id));
const sourceRows = [{id:1,amount:18},{id:2,amount:null},{id:3,amount:24}];
const mismatchRows = [{id:1,amount:18},{id:2,amount:null},{id:2,amount:27}];

function renderChecks() {
  const rows = $('scenario').value === 'mismatch' ? mismatchRows : sourceRows;
  const labels = lang === 'es' ? ['Número de filas','Total de importes','Valores nulos','IDs duplicados','Equivalencia de registros'] : ['Row count','Amount total','Null count','Duplicate IDs','Record equivalence'];
  $('checks').replaceChildren(...compareRows(sourceRows, rows).map((check, i) => {
    const row = document.createElement('div'); row.className = 'check';
    const name = document.createElement('span'); name.textContent = labels[i];
    const state = document.createElement('span'); state.className = check.pass ? 'pass' : 'fail'; state.textContent = i === 4 ? (check.pass ? t[lang].statusPass : t[lang].statusFail) : `${check.pass ? t[lang].statusPass : t[lang].statusFail} · ${check.source} / ${check.target}`;
    row.append(name, state); return row;
  }));
}
function reset() {
  $('source').value = samples.find(s => s.id === $('sample').value).input;
  $('result').textContent = t[lang].waiting; $('changes').replaceChildren(); $('warning').textContent = '';
  $('status').className = 'status'; $('status').textContent = t[lang].ready;
}
function review() {
  const result = convert($('source').value);
  $('changes').replaceChildren(); $('warning').textContent = '';
  if (!result.ok) { $('result').textContent = '—'; $('status').className = 'status error'; $('status').textContent = t[lang].unsupported; return; }
  $('result').textContent = result.sample.output;
  for (const change of result.sample.changes) { const chip = document.createElement('span'); chip.className = 'chip'; chip.textContent = change; $('changes').append(chip); }
  $('warning').textContent = `${t[lang].warning}: ${result.sample.warning}`;
  $('status').className = 'status'; $('status').textContent = t[lang].success;
}
function setLanguage(next) {
  const wasReviewed = $('result').textContent !== t[lang].waiting;
  lang = next; document.documentElement.lang = next;
  for (const el of document.querySelectorAll('[data-i]')) { const value = t[next][el.dataset.i]; if (value !== undefined) { if (el.dataset.i === 'footer') el.innerHTML = value; else el.textContent = value; } }
  for (const code of ['es','en']) $(code).setAttribute('aria-pressed', String(code === next));
  renderChecks(); if (wasReviewed) review(); else reset();
}
$('sample').addEventListener('change', reset);
$('reset').addEventListener('click', reset);
$('convert').addEventListener('click', review);
$('scenario').addEventListener('change', renderChecks);
for (const code of ['es','en']) $(code).addEventListener('click', () => setLanguage(code));
reset(); renderChecks();
