import { ASSETS, DAYS, generateReadings } from './fixture.mjs';
import { METRICS, selectReadings, detectAnomalies } from './rules.mjs';

const allReadings = generateReadings();
const state = { lang: 'es', assetId: ASSETS[0].id, day: DAYS[0], metric: 'temperature', selected: null, replayIndex: null, timer: null };
const $ = (id) => document.getElementById(id);

const copy = {
  es: {
    skip:'Saltar al contenido',portfolio:'Portafolio',method:'Método y código',eyebrow:'DEMO DE INGENIERÍA DE DATOS · 01 / 03',
    lede:'De una lectura de sensor a una decisión que se puede explicar.',intro:'Una planta industrial ficticia necesita detectar condiciones fuera de rango sin perder la trazabilidad de cada alerta. Explore tres activos, reproduzca lecturas y abra cualquier incidente para ver el valor y el umbral exactos.',
    synthetic:'DATOS SINTÉTICOS',disclosure:'216 lecturas deterministas, 3 activos ficticios, 14–16 sep 2026 UTC. No representa sistemas de clientes ni datos en vivo.',workspace:'Centro de operaciones',asset:'Activo',window:'Ventana',signal:'Señal del gráfico',replay:'Reproducir período',pause:'Pausar replay',download:'Descargar CSV',trend:'TENDENCIA / UMBRAL',chart:'Lecturas por hora',reading:'Lectura',threshold:'Umbral',anomaly:'Anomalía',rule_engine:'REGLAS EXPLÍCITAS',incidents:'Incidentes',incident_intro:'Seleccione un incidente para ver la medición y la regla que lo activó.',explainability:'EXPLICABILIDAD',inspection:'Inspección de incidente',source_readings:'LECTURAS DE ORIGEN',raw:'Mediciones sin agregar',table_intro:'Cada fila proviene del generador reproducible incluido en este proyecto. Horas en UTC.',timestamp:'Fecha / hora UTC',temperature:'Temperatura',vibration:'Vibración',pressure:'Presión',status:'Estado',design:'Diseño que se puede auditar.',m_fixture:'Datos reproducibles',m_fixture_body:'Fixture determinista, tres días y un muestreo por hora. Valores e incidentes inyectados en código público.',m_rules:'Reglas separadas',m_rules_body:'Límites por activo; cada alerta conserva valor, umbral, operador y hora. No hay IA detrás de las alertas.',m_view:'Vista estática',m_view_body:'SVG, filtros, replay y CSV ejecutados en el navegador. Sin backend ni solicitudes de datos externas.',footer:'EnergyPulse es una demostración pública con datos sintéticos. No es un sistema de monitoreo de producción.',readme:'Leer arquitectura y pruebas ↗',allDays:'Todos los días',readings:'lecturas',alertCount:'incidentes',avg:'promedio',range:'rango',samples:'muestras',normal:'Normal',alert:'Alerta',noIncident:'No hay incidentes en esta ventana. Cambie el activo o el día para explorar otros casos.',chooseIncident:'Seleccione un incidente de la lista para inspeccionar su regla exacta.',noData:'No hay lecturas para esta combinación de filtros.',above:'supera',below:'está por debajo de',rule:'Regla aplicada',observed:'Valor observado',limit:'Umbral',source:'Fuente: fixture sintético determinista · muestreo horario UTC',replayAt:'Replay simulado',replayDone:'Replay completo. No se recibieron datos en vivo.',replayReady:'El replay recorre las lecturas de la ventana, una por una.',windowSummary:'Ventana seleccionada',invalid:'No se encontró el activo o la ventana seleccionada.',rows:'filas',csvName:'lecturas-sinteticas',assetZone:'Zona',metricUnits:{temperature:'°C',vibration:'mm/s',pressure:'bar'}
  },
  en: {
    skip:'Skip to content',portfolio:'Portfolio',method:'Method and code',eyebrow:'DATA ENGINEERING DEMO · 01 / 03',
    lede:'From a sensor reading to an explainable decision.',intro:'A fictional industrial facility needs to detect out-of-range conditions while keeping every alert traceable. Explore three assets, replay readings, and open any incident to see its exact value and threshold.',
    synthetic:'SYNTHETIC DATA',disclosure:'216 deterministic readings, 3 fictional assets, 14–16 Sep 2026 UTC. No client systems or live data are represented.',workspace:'Operations center',asset:'Asset',window:'Window',signal:'Chart signal',replay:'Replay period',pause:'Pause replay',download:'Download CSV',trend:'TREND / THRESHOLD',chart:'Hourly readings',reading:'Reading',threshold:'Threshold',anomaly:'Anomaly',rule_engine:'EXPLICIT RULES',incidents:'Incidents',incident_intro:'Select an incident to see the measurement and rule that triggered it.',explainability:'EXPLAINABILITY',inspection:'Incident inspection',source_readings:'SOURCE READINGS',raw:'Unaggregated measurements',table_intro:'Each row comes from the reproducible generator bundled with this project. Times are UTC.',timestamp:'Date / time UTC',temperature:'Temperature',vibration:'Vibration',pressure:'Pressure',status:'Status',design:'A design you can audit.',m_fixture:'Reproducible data',m_fixture_body:'Deterministic fixture, three days and one sample per hour. Values and injected incidents are in public code.',m_rules:'Separate rules',m_rules_body:'Asset-specific limits; every alert retains its value, threshold, operator and time. No AI powers the alerts.',m_view:'Static view',m_view_body:'SVG, filters, replay and CSV run in the browser. No backend or external data requests.',footer:'EnergyPulse is a public demonstration using synthetic data. It is not a production monitoring system.',readme:'Read architecture and tests ↗',allDays:'All days',readings:'readings',alertCount:'incidents',avg:'average',range:'range',samples:'samples',normal:'Normal',alert:'Alert',noIncident:'No incidents in this window. Change the asset or day to explore other cases.',chooseIncident:'Select an incident in the list to inspect its exact rule.',noData:'No readings for this filter combination.',above:'is above',below:'is below',rule:'Applied rule',observed:'Observed value',limit:'Threshold',source:'Source: deterministic synthetic fixture · hourly UTC sampling',replayAt:'Simulated replay',replayDone:'Replay complete. No live data was received.',replayReady:'Replay steps through the window readings, one at a time.',windowSummary:'Selected window',invalid:'Selected asset or window was not found.',rows:'rows',csvName:'synthetic-readings',assetZone:'Zone',metricUnits:{temperature:'°C',vibration:'mm/s',pressure:'bar'}
  }
};
const t = (key) => copy[state.lang][key];
const fmt = (value) => Number.isFinite(value) ? value.toFixed(1) : '—';
const shortTime = (iso) => `${iso.slice(0, 10)} ${iso.slice(11, 16)}`;
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function windowData() {
  const asset = ASSETS.find((item) => item.id === state.assetId);
  if (!asset || (state.day && !DAYS.includes(state.day))) return { asset: null, readings: [], anomalies: [] };
  const readings = selectReadings(allReadings, { assetId: asset.id, day: state.day });
  return { asset, readings, anomalies: detectAnomalies(readings, asset.id) };
}

function stopReplay() {
  if (state.timer) clearInterval(state.timer);
  state.timer = null;
  $('replay').querySelector('[data-i18n="replay"]').textContent = t('replay');
}

function renderLanguage() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  $('language').textContent = state.lang === 'es' ? 'EN' : 'ES';
  $('language').setAttribute('aria-label', state.lang === 'es' ? 'Switch language to English' : 'Cambiar idioma a español');
  $('asset').innerHTML = ASSETS.map((a) => `<option value="${a.id}">${a.name}</option>`).join('');
  $('day').innerHTML = `<option value="">${t('allDays')}</option>` + DAYS.map((day) => `<option value="${day}">${day}</option>`).join('');
  $('metric').innerHTML = Object.entries(METRICS).map(([key, rule]) => `<option value="${key}">${t(key)} · ${rule.unit}</option>`).join('');
  $('asset').value = state.assetId;
  $('day').value = state.day;
  $('metric').value = state.metric;
  if (state.timer) $('replay').querySelector('[data-i18n="replay"]').textContent = t('pause');
}

function renderMetrics({ asset, readings, anomalies }) {
  const values = readings.map((r) => r[state.metric]);
  const mean = values.length ? values.reduce((a, b) => a + b, 0) / values.length : NaN;
  const bounds = values.length ? `${fmt(Math.min(...values))}–${fmt(Math.max(...values))}` : '—';
  const metric = METRICS[state.metric];
  const cards = [
    { label:t('samples'), value:String(readings.length), note:t('source') },
    { label:t('alertCount'), value:String(anomalies.length), note:asset ? `${asset.name} · ${state.day || t('allDays')}` : '—', accent:true },
    { label:`${t(state.metric)} · ${t('avg')}`, value:fmt(mean), unit:metric.unit, note:t('windowSummary') },
    { label:`${t(state.metric)} · ${t('range')}`, value:bounds, unit:metric.unit, note:t('windowSummary') },
  ];
  $('metrics').innerHTML = cards.map((c) => `<article class="metric-card ${c.accent?'accent':''}"><div class="metric-label">${escapeHtml(c.label)}</div><div class="metric-value">${escapeHtml(c.value)}${c.unit?` <small>${escapeHtml(c.unit)}</small>`:''}</div><div class="metric-note">${escapeHtml(c.note)}</div></article>`).join('');
}

function renderChart({ asset, readings, anomalies }) {
  $('chart-unit').textContent = METRICS[state.metric].unit;
  if (!readings.length || !asset) { $('chart').innerHTML = `<div class="empty">${t('noData')}</div>`; $('chart').setAttribute('aria-label', t('noData')); return; }
  const rule = METRICS[state.metric];
  const limit = asset[rule.limitKey];
  const values = readings.map((r) => r[state.metric]);
  const min = Math.floor((Math.min(...values, limit) - 3) / 5) * 5;
  const max = Math.ceil((Math.max(...values, limit) + 3) / 5) * 5;
  const left=48,right=704,top=17,bottom=211;
  const x=(i)=>left+(right-left)*(readings.length===1?0.5:i/(readings.length-1));
  const y=(v)=>bottom-(v-min)/(max-min)*(bottom-top);
  const points=readings.map((r,i)=>`${x(i).toFixed(1)},${y(r[state.metric]).toFixed(1)}`).join(' ');
  const polygon=`${left},${bottom} ${points} ${right},${bottom}`;
  const alarmIds=new Set(anomalies.filter((a)=>a.metric===state.metric).map((a)=>a.readingId));
  const marks=readings.map((r,i)=>alarmIds.has(r.id)?`<circle class="alarm" cx="${x(i)}" cy="${y(r[state.metric])}" r="5.5"><title>${shortTime(r.timestamp)} · ${fmt(r[state.metric])} ${rule.unit}</title></circle>`:'').join('');
  const grid=Array.from({length:5},(_,i)=>{const val=min+(max-min)*i/4;return `<line class="gridline" x1="${left}" y1="${y(val)}" x2="${right}" y2="${y(val)}"/><text x="4" y="${y(val)+4}">${fmt(val)}</text>`}).join('');
  const ticks=[0,Math.floor((readings.length-1)/2),readings.length-1].map((i)=>`<text x="${x(i)}" y="242" text-anchor="middle">${readings[i].timestamp.slice(11,16)}${state.day?'':` · ${readings[i].timestamp.slice(5,10)}`}</text>`).join('');
  const cursor=state.replayIndex===null?'':`<line class="cursor" x1="${x(state.replayIndex)}" y1="${top}" x2="${x(state.replayIndex)}" y2="${bottom}"/>`;
  $('chart').innerHTML=`<svg viewBox="0 0 720 254" aria-hidden="true"><defs><linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#9fe8c5" stop-opacity=".25"/><stop offset="100%" stop-color="#9fe8c5" stop-opacity="0"/></linearGradient></defs>${grid}<line class="limit" x1="${left}" y1="${y(limit)}" x2="${right}" y2="${y(limit)}"/><text x="${right}" y="${y(limit)-7}" text-anchor="end">${t('threshold')} ${fmt(limit)}</text><polygon class="area" points="${polygon}"/><polyline class="series" points="${points}"/>${marks}${cursor}${ticks}</svg>`;
  $('chart').setAttribute('aria-label', `${t(state.metric)}: ${readings.length} ${t('readings')}. ${t('threshold')} ${fmt(limit)} ${rule.unit}. ${anomalies.filter((a)=>a.metric===state.metric).length} ${t('alertCount')}.`);
}

function renderIncidents({ anomalies }) {
  $('incident-count').textContent = String(anomalies.length);
  $('incidents').innerHTML = anomalies.length ? anomalies.map((a)=>`<button class="incident-item" type="button" data-id="${a.id}" aria-pressed="${state.selected===a.id}"><strong>${t(a.metric)}</strong><span class="incident-value">${fmt(a.value)} ${a.unit}</span><time datetime="${a.timestamp}">${shortTime(a.timestamp)} UTC</time><span aria-hidden="true">↗</span></button>`).join('') : `<div class="empty">${t('noIncident')}</div>`;
  $('incidents').querySelectorAll('button').forEach((button)=>button.addEventListener('click',()=>{state.selected=button.dataset.id;state.metric=anomalies.find((a)=>a.id===state.selected).metric;$('metric').value=state.metric;render();$('detail').scrollIntoView({behavior:'smooth',block:'nearest'});}));
}

function renderDetail({ anomalies, asset }) {
  const selected=anomalies.find((a)=>a.id===state.selected);
  if (!selected) { $('detail').innerHTML=`<div class="empty">${t('chooseIncident')}</div>`; return; }
  const operator=selected.direction==='above'?'&gt;':'&lt;';
  $('detail').innerHTML=`<div class="detail-content"><div class="detail-result"><strong>${t(selected.metric)} · ${asset.name}</strong><p>${t('assetZone')}: ${asset.zone}</p><p><time datetime="${selected.timestamp}">${shortTime(selected.timestamp)} UTC</time></p><p>${t('source')}</p></div><div class="detail-copy"><div class="detail-rule">${t('rule')}: ${t(selected.metric)} ${operator} ${fmt(selected.limit)} ${selected.unit}</div><p>${t('observed')}: <strong>${fmt(selected.value)} ${selected.unit}</strong> · ${t(selected.direction)} ${t('limit').toLowerCase()} ${fmt(selected.limit)} ${selected.unit}.</p></div></div>`;
}

function renderRows({ readings, anomalies }) {
  const alarmIds=new Set(anomalies.map((a)=>a.readingId));
  $('row-count').textContent=`${readings.length} ${t('rows')}`;
  $('rows').innerHTML=readings.map((r,i)=>`<tr class="${state.replayIndex===i?'highlight':''}"><td><time datetime="${r.timestamp}">${shortTime(r.timestamp)}</time></td><td>${fmt(r.temperature)}</td><td>${fmt(r.vibration)}</td><td>${fmt(r.pressure)}</td><td><span class="${alarmIds.has(r.id)?'status-alarm':'status-normal'}">${alarmIds.has(r.id)?t('alert'):t('normal')}</span></td></tr>`).join('');
  if (!readings.length) $('rows').innerHTML=`<tr><td colspan="5">${t('noData')}</td></tr>`;
}

function render() {
  const data=windowData();
  $('validation').hidden=Boolean(data.asset);
  $('validation').textContent=data.asset?'':t('invalid');
  $('window-summary').textContent=data.asset?`${data.asset.name} · ${state.day||t('allDays')} · UTC · ${data.readings.length} ${t('readings')}`:'—';
  renderMetrics(data);renderChart(data);renderIncidents(data);renderDetail(data);renderRows(data);
  if (state.replayIndex===null) $('replay-status').textContent=t('replayReady');
  else if (data.readings[state.replayIndex]) $('replay-status').textContent=`${t('replayAt')}: ${shortTime(data.readings[state.replayIndex].timestamp)} UTC · ${state.replayIndex+1}/${data.readings.length}`;
}

function downloadCsv() {
  const { readings, asset }=windowData();
  if (!asset) return;
  const lines=['timestamp_utc,asset_id,temperature_c,vibration_mm_s,pressure_bar',...readings.map((r)=>`${r.timestamp},${r.assetId},${r.temperature},${r.vibration},${r.pressure}`)];
  const blob=new Blob([lines.join('\n')+'\n'],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const link=document.createElement('a');link.href=url;link.download=`${t('csvName')}-${asset.id}-${state.day||'all'}.csv`;document.body.append(link);link.click();link.remove();URL.revokeObjectURL(url);
}

function replay() {
  if (state.timer) {stopReplay();return;}
  const {readings}=windowData();
  if (!readings.length) { $('validation').hidden=false;$('validation').textContent=t('noData');return; }
  state.replayIndex=0;render();$('replay').querySelector('[data-i18n="replay"]').textContent=t('pause');
  state.timer=setInterval(()=>{state.replayIndex+=1;if(state.replayIndex>=readings.length){stopReplay();state.replayIndex=readings.length-1;render();$('replay-status').textContent=t('replayDone');return;}render();},400);
}

for (const [id,key] of [['asset','assetId'],['day','day'],['metric','metric']]) $(''+id).addEventListener('change',(event)=>{stopReplay();state[key]=event.target.value;state.selected=null;state.replayIndex=null;render();});
$('language').addEventListener('click',()=>{state.lang=state.lang==='es'?'en':'es';renderLanguage();render();});
$('replay').addEventListener('click',replay);
$('download').addEventListener('click',downloadCsv);
renderLanguage();render();
