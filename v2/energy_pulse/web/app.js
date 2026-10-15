const $ = id => document.getElementById(id);
let lang = 'en';
let state = {assets:[], rules:{}, readings:[], quality:[], incidents:[]};
const copy = {
  en:{eyebrow:'INDUSTRIAL TELEMETRY / DATA QUALITY',title:'Every incident has a source.',intro:'Explore persisted sensor readings, expected slots and the rule that produced an incident. This is a synthetic reference system, not live plant monitoring.',latestRun:'Latest pipeline run',asset:'Asset',signal:'Signal',refresh:'Refresh from API',received:'Valid readings',receivedNote:'For the selected asset and signal',coverage:'Expected-slot coverage',coverageNote:'Received GOOD / expected',alerts:'Incidents',alertsNote:'Versioned threshold episodes',trendLabel:'PERSISTED SILVER',trend:'Time series',chartHint:'UTC · 15-minute observations. Select an incident for raw → clean → Gold lineage.',readingsCaption:'Source-backed readings',time:'Time UTC',value:'Value',quality:'Quality',expectedLabel:'EXPECTED VS RECEIVED',qualityTitle:'Quality by hour',qualityHint:'A missing slot is missing, never a zero measurement.',ruleLabel:'VERSIONED RULES',incidentTitle:'Incidents',traceLabel:'SOURCE → DECISION',traceTitle:'Incident lineage',traceHint:'Select an incident to inspect the original event, normalized row, Gold hour and applied rule.',footer:'Synthetic demonstration · local read-only API · no client or live equipment data',loading:'Loading persisted data…',ready:'Loaded from SQLite through the API.',failed:'API unavailable. Start the local server and retry.',none:'No records for this selection.',select:'Select this incident',closed:'Closed',open:'Open'},
  es:{eyebrow:'TELEMETRÍA INDUSTRIAL / CALIDAD DE DATOS',title:'Cada incidente tiene un origen.',intro:'Explore lecturas persistidas, intervalos esperados y la regla que generó un incidente. Este sistema de referencia usa datos sintéticos; no monitorea una planta en vivo.',latestRun:'Última ejecución',asset:'Activo',signal:'Señal',refresh:'Actualizar desde API',received:'Lecturas válidas',receivedNote:'Activo y señal seleccionados',coverage:'Cobertura esperada',coverageNote:'Recibidas GOOD / esperadas',alerts:'Incidentes',alertsNote:'Episodios de reglas versionadas',trendLabel:'SILVER PERSISTIDO',trend:'Serie temporal',chartHint:'UTC · lecturas cada 15 minutos. Seleccione un incidente para ver su linaje raw → clean → Gold.',readingsCaption:'Lecturas con origen',time:'Hora UTC',value:'Valor',quality:'Calidad',expectedLabel:'ESPERADO VS RECIBIDO',qualityTitle:'Calidad por hora',qualityHint:'Una lectura faltante no equivale a valor cero.',ruleLabel:'REGLAS VERSIONADAS',incidentTitle:'Incidentes',traceLabel:'ORIGEN → DECISIÓN',traceTitle:'Linaje del incidente',traceHint:'Seleccione un incidente para inspeccionar el evento original, la fila normalizada, la hora Gold y la regla aplicada.',footer:'Demostración sintética · API local de solo lectura · sin datos de clientes o equipos reales',loading:'Cargando datos persistidos…',ready:'Datos cargados desde SQLite mediante API.',failed:'API no disponible. Inicie el servidor local y reintente.',none:'Sin registros para esta selección.',select:'Seleccionar incidente',closed:'Cerrado',open:'Abierto'}
};
function t(k){return copy[lang][k]}
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n}
async function api(path){const response=await fetch(path,{cache:'no-store'});if(!response.ok)throw new Error(`${path}: HTTP ${response.status}`);return response.json()}
function selected(){return {assetId:$('asset').value,metric:$('metric').value}}
function renderLanguage(){document.documentElement.lang=lang;document.querySelectorAll('[data-i]').forEach(n=>n.textContent=t(n.dataset.i));$('language').textContent=lang==='en'?'ES':'EN';$('language').setAttribute('aria-label',lang==='en'?'Cambiar a español':'Switch to English')}
function renderRuns(runs){const last=runs.items.find(r=>r.stage==='BUILD'&&r.status==='SUCCESS')||runs.items[0];$('run-id').textContent=last?.run_id||'—';$('run-meta').textContent=last?`${last.finished_at_utc||last.started_at_utc} · ${last.output_count} Gold rows`:'—'}
function renderKpis(){const received=state.readings.filter(r=>r.source_quality==='GOOD').length;const expected=state.quality.reduce((a,r)=>a+r.expected_samples,0);const observed=state.quality.reduce((a,r)=>a+r.received_samples,0);$('received').textContent=received;$('coverage').textContent=expected?`${observed}/${expected} · ${Math.round(observed/expected*100)}%`:'—';$('alerts').textContent=state.incidents.filter(i=>i.metric===selected().metric).length}
function renderChart(){
  const box=$('chart');
  box.replaceChildren();
  const data=state.readings.filter(r=>r.source_quality==='GOOD');
  const metric=selected().metric;
  const rule=state.rules[metric];
  $('chart-unit').textContent=rule?.unit||'—';
  if(!data.length){
    box.append(el('div',t('none'),'empty'));
    box.setAttribute('aria-label',t('none'));
    return;
  }
  const w=800,h=260,p=42;
  const times=data.map(r=>Date.parse(r.observed_at_utc));
  const first=times[0],last=times[times.length-1];
  const values=data.map(r=>r.value);
  const min=Math.min(...values,rule.threshold)-2;
  const max=Math.max(...values,rule.threshold)+2;
  const x=time=>p+(w-2*p)*(first===last?.5:(time-first)/(last-first));
  const y=value=>h-p-(value-min)/(max-min)*(h-2*p);
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
  svg.setAttribute('role','img');
  const gaps=times.slice(1).reduce((count,time,i)=>count+Math.max(0,Math.round((time-times[i])/(15*60*1000))-1),0);
  const description=`${metric} in ${rule.unit}; ${data.length} UTC observations; ${gaps} missing intervals; threshold ${rule.threshold}`;
  svg.setAttribute('aria-label',description);
  box.setAttribute('aria-label',description);
  const add=(tag,attrs)=>{
    const node=document.createElementNS(svg.namespaceURI,tag);
    for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);
    svg.append(node);
    return node;
  };
  add('line',{x1:p,y1:h-p,x2:w-p,y2:h-p,stroke:'#789b98','stroke-width':2});
  add('line',{x1:p,y1:y(rule.threshold),x2:w-p,y2:y(rule.threshold),stroke:'#f79a80','stroke-width':2,'stroke-dasharray':'6 5'});
  const threshold=add('text',{x:p+4,y:y(rule.threshold)-6,fill:'#ffc0a9','font-size':13});
  threshold.textContent=`${rule.operator} ${rule.threshold} ${rule.unit}`;
  for(const [time,position] of [[first,p],[last,w-p]]){
    const tick=add('text',{x:position,y:h-12,fill:'#a8c4bf','font-size':12,'text-anchor':position===p?'start':'end'});
    tick.textContent=new Date(time).toISOString().slice(11,16)+' UTC';
  }
  let segment=[];
  const flush=()=>{
    if(!segment.length)return;
    add('polyline',{points:segment.join(' '),fill:'none',stroke:'#baf47a','stroke-width':3});
    segment=[];
  };
  data.forEach((row,index)=>{
    if(index>0&&times[index]-times[index-1]>15*60*1000)flush();
    segment.push(`${x(times[index])},${y(row.value)}`);
    const breach=rule.operator==='>'?row.value>rule.threshold:row.value<rule.threshold;
    const point=add('circle',{cx:x(times[index]),cy:y(row.value),r:4,fill:breach?'#f79a80':'#baf47a'});
    const title=document.createElementNS(svg.namespaceURI,'title');
    title.textContent=`${row.observed_at_utc} · ${row.value} ${row.unit} · ${row.event_id}`;
    point.append(title);
  });
  flush();
  box.append(svg);
}
function renderTable(){const body=$('readings');body.replaceChildren();for(const r of state.readings){const tr=el('tr');for(const value of [r.observed_at_utc,r.value+' '+r.unit,r.source_quality,r.event_id])tr.append(el('td',value));body.append(tr)}if(!state.readings.length){const tr=el('tr');const td=el('td',t('none'));td.colSpan=4;tr.append(td);body.append(tr)}}
function renderQuality(){const box=$('heatmap');box.replaceChildren();for(const row of state.quality){const b=el('button',`${row.hour_utc.slice(11,16)}\n${row.received_samples}/${row.expected_samples}`,row.quality_status.toLowerCase().replace('_','-'));b.type='button';b.title=`${row.hour_utc} · ${row.asset_id} · ${row.metric}: ${row.quality_status}`;b.setAttribute('aria-label',b.title);b.addEventListener('click',()=>{const target=[...$('readings').querySelectorAll('tr')].find(tr=>tr.textContent.includes(row.hour_utc.slice(0,13)));target?.scrollIntoView({behavior:'smooth',block:'center'});$('status').textContent=b.title});box.append(b)}if(!state.quality.length)box.append(el('p',t('none'),'empty'))}
function renderIncidents(){const box=$('incidents');box.replaceChildren();const items=state.incidents.filter(i=>i.metric===selected().metric);for(const i of items){const b=el('button',undefined,'incident');b.type='button';b.append(el('strong',`${i.metric} ${i.operator} ${i.threshold} ${state.rules[i.metric]?.unit||''}`));b.append(el('small',`${i.opened_at_utc} · ${i.status==='OPEN'?t('open'):t('closed')} · ${i.rule_version}`));b.setAttribute('aria-label',`${t('select')} ${i.incident_id}`);b.addEventListener('click',()=>showLineage(i.incident_id));box.append(b)}if(!items.length)box.append(el('p',t('none'),'empty'))}
async function showLineage(id){const box=$('lineage');box.replaceChildren();try{const d=await api(`/api/incidents/${encodeURIComponent(id)}/lineage`);$('lineage-intro').textContent=`${d.incident.incident_id} · ${d.incident.rule_version}`;const grid=el('div',undefined,'lineage-grid');const card=(heading,lines)=>{const a=el('article');a.append(el('h3',heading));for(const [k,v] of lines)a.append(el('p',`${k}: ${v}`));return a};grid.append(card('Bronze · raw',[['event_id',d.raw.event_id],['sha256',d.raw.payload_sha256],['ingest_run',d.raw.ingest_run_id]]));grid.append(card('Silver · clean',[['value',`${d.measurement.value} ${d.measurement.unit}`],['time',d.measurement.observed_at_utc],['build_run',d.measurement.build_run_id]]));grid.append(card('Gold · hour',[['hour',d.gold?.hour_utc||'—'],['received/expected',d.gold?`${d.gold.received_samples}/${d.gold.expected_samples}`:'—'],['status',d.gold?.quality_status||'—']]));grid.append(card('Rule · incident',[['version',d.incident.rule_version],['condition',`${d.incident.operator} ${d.incident.threshold}`],['state',d.incident.status]]));box.append(grid)}catch(e){box.append(el('p',String(e),'empty'))}}
async function refresh(){const {assetId,metric}=selected();$('status').textContent=t('loading');try{const [m,q,i,r]=await Promise.all([api(`/api/measurements?asset_id=${encodeURIComponent(assetId)}&metric=${encodeURIComponent(metric)}`),api(`/api/quality?asset_id=${encodeURIComponent(assetId)}&metric=${encodeURIComponent(metric)}`),api(`/api/incidents?asset_id=${encodeURIComponent(assetId)}`),api('/api/runs')]);state.readings=m.items;state.quality=q.items;state.incidents=i.items;renderRuns(r);renderKpis();renderChart();renderTable();renderQuality();renderIncidents();$('lineage').replaceChildren();$('lineage-intro').textContent=t('traceHint');$('status').textContent=t('ready')}catch(e){$('status').textContent=`${t('failed')} ${e.message}`;for(const id of ['chart','heatmap','incidents','lineage'])$(id).replaceChildren();$('readings').replaceChildren();for(const id of ['received','coverage','alerts'])$(id).textContent='—'}}
async function init(){renderLanguage();try{const [assets,rules]=await Promise.all([api('/api/assets'),api('/api/rules')]);state.assets=assets.items;state.rules=rules.items;for(const a of state.assets){const o=el('option',`${a.name} · ${a.site_id}`);o.value=a.asset_id;$('asset').append(o)}$('asset').value='PUMP-A102';await refresh()}catch(e){$('status').textContent=`${t('failed')} ${e.message}`}}
$('refresh').addEventListener('click',refresh);$('asset').addEventListener('change',refresh);$('metric').addEventListener('change',refresh);$('language').addEventListener('click',()=>{lang=lang==='en'?'es':'en';renderLanguage();refresh()});init();
