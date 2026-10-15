const $ = id => document.getElementById(id);
let evidence = null;
let language = 'en';
let selectedCase = '12-intentional-mismatch';
const words = {
  en: {
    eyebrow:'THREE EXECUTABLE REFERENCE SYSTEMS',title:'Evidence before claims.',
    lede:'Explore a frozen public snapshot from three real local pipelines. Every displayed number comes from persisted synthetic data; the source, contracts and commands are available for independent reproduction.',
    source:'Explore source & runbooks ↗',inspect:'Inspect the evidence ↓',snapshot:'GitHub Pages can show these exported results. The Python APIs run locally and are not represented as a hosted service.',revision:'Source revision',exported:'Exported UTC',
    energyKpi:'accepted Bronze events',analyticsKpi:'validated source rows',migrationKpi:'queries assessed on two engines',
    energyIntro:'A plant analyst must distinguish a breached threshold from missing sensor data and trace each incident to its source event.',openEnergy:'View code and local setup ↗',series:'Observed values, UTC',signal:'Signal',incident:'Incident evidence',energyHint:'A gap stays a gap; the line does not bridge missing 15-minute slots.',energyLimit:'Illustrative rules and assets; no live equipment, safety control or public API.',
    analyticsIntro:'A small ecommerce team needs currency-safe, order-grain definitions and answers backed by executed, parameterized SQL.',openAnalytics:'View code and local setup ↗',metricResult:'Executed metric result',metric:'Metric',currency:'Currency',definition:'Definition & provenance',sql:'Show exact SQL and parameters',analyticsLimit:'No FX conversion or arbitrary SQL. This selection changes the frozen export; the local app reruns queries.',
    migrationIntro:'A migration lead needs proof that a translated query returns the same typed rows, and a visible refusal when equivalence cannot be claimed.',openMigration:'View code and local setup ↗',decisions:'Executed decisions',filter:'Filter',diff:'Record-level evidence',migrationLimit:'PASS applies only to these fixtures and SQLite/DuckDB versions; it does not certify a production cutover.',
    verification:'REPRODUCE / CHALLENGE / EXTEND',closingTitle:'The engineering is inspectable.',closingText:'Each package includes architecture, data dictionary, runbook, negative tests and limitations. Local Python applications execute the data movement; this page is a static snapshot generated from their outputs.',readGuide:'Read the reproduction guide ↗',footer:'Fictional businesses · synthetic data · explicit limitations',loaded:'Frozen evidence loaded from executed local runs.',failed:'Evidence export unavailable or invalid. Re-run the export script and reload.',noData:'No data for this selection.',gap:'missing slots',threshold:'Threshold',raw:'Source event',silver:'Normalized value',gold:'Hourly quality',rule:'Rule and decision',counts:'Source / target rows',review:'Unsupported or unsafe input; no success claim.'
  },
  es: {
    eyebrow:'TRES SISTEMAS DE REFERENCIA EJECUTABLES',title:'Evidencia antes que promesas.',
    lede:'Explore una captura pública de tres pipelines locales reales. Cada cifra proviene de datos sintéticos persistidos; el código, los contratos y los comandos permiten reproducirla.',
    source:'Explorar código y guías ↗',inspect:'Examinar evidencia ↓',snapshot:'GitHub Pages muestra estos resultados exportados. Las API de Python se ejecutan localmente; aquí no se presentan como servicio alojado.',revision:'Revisión del código',exported:'Exportado UTC',
    energyKpi:'eventos Bronze aceptados',analyticsKpi:'filas de origen validadas',migrationKpi:'consultas evaluadas en dos motores',
    energyIntro:'Una analista industrial debe distinguir un umbral superado de la ausencia de datos y rastrear cada incidente a su evento de origen.',openEnergy:'Ver código e instalación local ↗',series:'Valores observados, UTC',signal:'Señal',incident:'Evidencia del incidente',energyHint:'Un hueco sigue siendo un hueco; la línea no une intervalos faltantes de 15 minutos.',energyLimit:'Reglas y activos ilustrativos; sin equipos reales, control de seguridad ni API pública.',
    analyticsIntro:'Un equipo de comercio necesita métricas por moneda y a grano de pedido, respaldadas por SQL parametrizado que sí se ejecutó.',openAnalytics:'Ver código e instalación local ↗',metricResult:'Resultado de métrica ejecutada',metric:'Métrica',currency:'Moneda',definition:'Definición y procedencia',sql:'Mostrar SQL exacto y parámetros',analyticsLimit:'Sin conversión de divisas ni SQL arbitrario. Esta selección cambia la captura; la app local vuelve a ejecutar consultas.',
    migrationIntro:'Quien dirige una migración necesita comprobar que el SQL traducido devuelve las mismas filas tipadas y ver cuándo no se puede afirmar equivalencia.',openMigration:'Ver código e instalación local ↗',decisions:'Decisiones ejecutadas',filter:'Filtro',diff:'Evidencia por registro',migrationLimit:'PASS solo aplica a estos fixtures y versiones SQLite/DuckDB; no certifica un cambio de producción.',
    verification:'REPRODUCIR / CUESTIONAR / AMPLIAR',closingTitle:'La ingeniería se puede inspeccionar.',closingText:'Cada paquete incluye arquitectura, diccionario de datos, guía operativa, pruebas negativas y límites. Las aplicaciones Python locales ejecutan el flujo; esta página es una captura estática de sus resultados.',readGuide:'Leer guía de reproducción ↗',footer:'Negocios ficticios · datos sintéticos · límites explícitos',loaded:'Evidencia congelada cargada desde ejecuciones locales.',failed:'La exportación no está disponible o no es válida. Ejecute el exportador y recargue.',noData:'Sin datos para esta selección.',gap:'intervalos faltantes',threshold:'Umbral',raw:'Evento de origen',silver:'Valor normalizado',gold:'Calidad horaria',rule:'Regla y decisión',counts:'Filas origen / destino',review:'Entrada no compatible o insegura; no se afirma éxito.'
  }
};
const t = key => words[language][key];
function node(tag, text, className){const el=document.createElement(tag);if(text!==undefined)el.textContent=String(text);if(className)el.className=className;return el}
function renderLanguage(){document.documentElement.lang=language;document.querySelectorAll('[data-i]').forEach(el=>el.textContent=t(el.dataset.i));$('language').textContent=language==='en'?'ES':'EN';$('language').setAttribute('aria-label',language==='en'?'Cambiar a español':'Switch to English');if(evidence)$('status').textContent=t('loaded')}
function renderOverview(){
  $('commit').textContent=evidence.source_commit.slice(0,12);
  $('exported').textContent=evidence.exported_at_utc.replace('T',' ').slice(0,19)+' UTC';
  $('energy-count').textContent=evidence.energy.counts.raw_events.toLocaleString(language);
  $('analytics-count').textContent=evidence.analytics.source_count.toLocaleString(language);
  $('migration-count').textContent=evidence.migration.cases.length.toLocaleString(language);
}
function renderEnergy(){
  const [asset,metric]=$('energy-signal').value.split('|');
  const data=evidence.energy.readings.filter(r=>r.asset_id===asset&&r.metric===metric&&r.source_quality==='GOOD');
  const hours=evidence.energy.quality.filter(r=>r.asset_id===asset&&r.metric===metric);
  const box=$('energy-chart');box.replaceChildren();
  const rule=evidence.energy.rules[metric];
  if(!data.length){box.append(node('p',t('noData')));return}
  const times=data.map(r=>Date.parse(r.observed_at_utc));
  const values=data.map(r=>r.value);
  const min=Math.min(...values,rule.threshold)-2,max=Math.max(...values,rule.threshold)+2;
  const w=730,h=220,p=36,first=times[0],last=times.at(-1);
  const x=time=>p+(w-2*p)*(first===last?.5:(time-first)/(last-first));
  const y=value=>h-p-(value-min)/(max-min)*(h-2*p);
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
  const gaps=times.slice(1).reduce((n,time,i)=>n+Math.max(0,Math.round((time-times[i])/900000)-1),0);
  const desc=`${asset} ${metric}: ${data.length} synthetic readings, ${gaps} ${t('gap')}, ${t('threshold')} ${rule.operator} ${rule.threshold} ${rule.unit}`;
  box.setAttribute('aria-label',desc);svg.setAttribute('aria-label',desc);
  const add=(tag,attributes)=>{const el=document.createElementNS(svg.namespaceURI,tag);for(const [k,v] of Object.entries(attributes))el.setAttribute(k,v);svg.append(el);return el};
  add('line',{x1:p,y1:h-p,x2:w-p,y2:h-p,stroke:'#75948f','stroke-width':2});
  add('line',{x1:p,y1:y(rule.threshold),x2:w-p,y2:y(rule.threshold),stroke:'#f3a18b','stroke-width':2,'stroke-dasharray':'5 5'});
  const label=add('text',{x:p+4,y:y(rule.threshold)-6,fill:'#ffc3aa','font-size':13});label.textContent=`${rule.operator} ${rule.threshold} ${rule.unit}`;
  let segment=[];
  const flush=()=>{if(segment.length){add('polyline',{points:segment.join(' '),fill:'none',stroke:'#b9f49a','stroke-width':3});segment=[]}};
  data.forEach((r,i)=>{
    if(i&&times[i]-times[i-1]>900000)flush();
    segment.push(`${x(times[i])},${y(r.value)}`);
    const breach=rule.operator==='>'?r.value>rule.threshold:r.value<rule.threshold;
    const circle=add('circle',{cx:x(times[i]),cy:y(r.value),r:4,fill:breach?'#f3a18b':'#b9f49a'});
    const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=`${r.observed_at_utc} · ${r.value} ${r.unit} · ${r.event_id}`;circle.append(title);
  });flush();box.append(svg);
  const quality=$('energy-quality');quality.replaceChildren();
  for(const hour of hours){const chip=node('span',`${hour.hour_utc.slice(11,16)} UTC · ${hour.received_samples}/${hour.expected_samples}`,hour.quality_status);chip.title=hour.quality_status;quality.append(chip)}
  const incident=evidence.energy.incidents.find(i=>i.asset_id===asset&&i.metric===metric);
  const lineage=$('energy-lineage');lineage.replaceChildren();
  if(!incident){lineage.append(node('p',t('noData')));return}
  const firstReading=data.find(r=>r.event_id===incident.first_event_id);
  const gold=hours.find(h=>h.hour_utc===incident.opened_at_utc.slice(0,13)+':00:00Z');
  const cards=[[t('raw'),`${incident.first_event_id} · SHA-256 ${incident.source_sha256}`],
    [t('silver'),firstReading?`${firstReading.value} ${firstReading.unit} · ${firstReading.observed_at_utc}`:'—'],
    [t('gold'),gold?`${gold.received_samples}/${gold.expected_samples} · ${gold.quality_status}`:'—'],
    [t('rule'),`${incident.rule_version} · ${incident.operator} ${incident.threshold} · ${incident.status} · ${incident.gap_count} ${t('gap')}`]];
  const grid=node('div',undefined,'lineage');for(const [title,value] of cards){const card=node('div');card.append(node('strong',title),node('span',value));grid.append(card)}lineage.append(grid);
}
function renderAnalytics(){
  const metric=$('analytics-metric').value,currency=$('analytics-currency').value;
  const query=evidence.analytics.queries.find(q=>q.metric===metric&&q.currency===currency);
  const bars=$('analytics-bars'),head=$('analytics-head'),body=$('analytics-rows');
  bars.replaceChildren();head.replaceChildren();body.replaceChildren();
  if(!query){bars.append(node('p',t('noData')));return}
  const max=Math.max(1,...query.rows.map(r=>Math.abs(Number(r.value)||0)));
  for(const row of query.rows){const outer=node('div',undefined,'bar-row');const name=[row.period,row.category].filter(Boolean).join(' · ');const track=node('div',undefined,'bar-track');const fill=node('div',undefined,'bar-fill');fill.style.width=`${Math.max(1,Math.abs(Number(row.value)||0)/max*100)}%`;track.append(fill);outer.append(node('span',name),track,node('strong',Number(row.value).toLocaleString(language)));bars.append(outer)}
  const columns=query.rows.length?Object.keys(query.rows[0]):[];
  const tr=node('tr');for(const col of columns)tr.append(node('th',col));head.append(tr);
  for(const row of query.rows){const tr=node('tr');for(const col of columns)tr.append(node('td',row[col]));body.append(tr)}
  $('analytics-definition').textContent=`${query.definition.label} v${evidence.analytics.semantic_version}: ${query.definition.formula}. ${query.definition.grain}; ${query.definition.unit}.`;
  $('analytics-provenance').textContent=`${evidence.analytics.window} · source SHA-256 ${evidence.analytics.source_sha256}`;
  $('analytics-sql').textContent=query.sql_executed;
  $('analytics-params').textContent=`Bound parameters: ${JSON.stringify(query.bound_parameters)}`;
}
function renderMigration(){
  const filter=$('migration-filter').value;
  const cases=filter==='ALL'?evidence.migration.cases:evidence.migration.cases.filter(c=>c.status===filter);
  const box=$('migration-cases');box.replaceChildren();
  for(const item of cases){const button=node('button',undefined,'case'+(item.case_id===selectedCase?' active':''));button.type='button';button.append(node('b',item.status,item.status),node('span',item.case_id));button.addEventListener('click',()=>{selectedCase=item.case_id;renderMigration()});box.append(button)}
  const current=evidence.migration.cases.find(c=>c.case_id===selectedCase);
  const detail=$('migration-detail');detail.replaceChildren();
  if(!current){detail.append(node('p',t('noData')));return}
  detail.append(node('p',`${current.case_id} · ${current.status}`));
  if(current.row_counts)detail.append(node('p',`${t('counts')}: ${current.row_counts.source} / ${current.row_counts.target}`));
  if(current.source_sql){const source=node('details');source.append(node('summary','Source SQL'),node('pre',current.source_sql));detail.append(source)}
  if(current.target_sql){const target=node('details');target.append(node('summary','Translated DuckDB SQL'),node('pre',current.target_sql));detail.append(target)}
  if(current.differences?.length){for(const diff of current.differences.slice(0,5))detail.append(node('div',diff.detail||JSON.stringify(diff),'difference'))}
  else if(current.error)detail.append(node('div',current.error,'difference'));
  else detail.append(node('p',current.status==='PASS'?'Typed result sets agreed under this case contract.':t('review')));
  if(current.engines)detail.append(node('p',`${current.engines.source} → ${current.engines.target}`,'caption'));
}
function renderAll(){renderLanguage();renderOverview();renderEnergy();renderAnalytics();renderMigration()}
async function init(){
  try{
    const response=await fetch('./evidence.json',{cache:'no-store'});
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const data=await response.json();
    if(!data.label?.includes('SYNTHETIC')||!data.energy||!data.analytics||!data.migration)throw new Error('invalid export');
    evidence=data;renderAll();$('status').textContent=t('loaded');
  }catch(error){$('status').textContent=`${t('failed')} ${error.message}`}
}
$('language').addEventListener('click',()=>{language=language==='en'?'es':'en';if(evidence)renderAll();else renderLanguage()});
$('energy-signal').addEventListener('change',renderEnergy);
$('analytics-metric').addEventListener('change',renderAnalytics);
$('analytics-currency').addEventListener('change',renderAnalytics);
$('migration-filter').addEventListener('change',()=>{const filter=$('migration-filter').value;if(filter!=='ALL'&&!evidence.migration.cases.some(c=>c.case_id===selectedCase&&c.status===filter))selectedCase=evidence.migration.cases.find(c=>c.status===filter)?.case_id;renderMigration()});
init();
