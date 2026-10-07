/*
 * dibujo.js - Todo lo que se dibuja
 * initStage() arma el escenario (colas, CPU, fichas) una sola vez.
 * show(t) muestra el instante t: mueve las fichas, y actualiza Gantt, registro de eventos y tabla.
 */

const LX = 84, STEP = 52, LH = 54, GAP = 8;
function initStage() {
  const n = Q.length, laneY = i => 64 + i * (LH + GAP), finY = 64 + n * (LH + GAP), H = finY + LH + 10;
  let s = `<rect class="lane lw" x="0" y="0" width="540" height="${LH}" rx="8"/><text class="m" x="8" y="22">Por llegar</text>`;
  for (let i = 0; i < n; i++) s += `<rect class="lane l${i}" x="0" y="${laneY(i)}" width="540" height="${LH}" rx="8"/>
    <text x="8" y="${laneY(i) + 22}" style="font-weight:600">Q${i + 1}</text><text class="m" x="8" y="${laneY(i) + 38}">q = ${Q[i]}</text>`;
  s += `<rect class="lane lw" x="0" y="${finY}" width="750" height="${LH}" rx="8"/><text class="m" x="8" y="${finY + 22}">Terminados</text>
    <rect class="lane lw" x="570" y="64" width="180" height="${Math.max(120, LH)}" rx="10" stroke-width="2"/>
    <text style="font-weight:600" x="660" y="86" text-anchor="middle">CPU</text>
    <rect x="590" y="150" width="140" height="8" rx="4" fill="var(--line)"/><rect id="qb" x="590" y="150" width="0" height="8" rx="4" fill="#2a78d6"/>
    <text class="m" id="qt" x="660" y="174" text-anchor="middle"></text>`;
  chips = {};
  R.rows.forEach((r, i) => {
    s += `<g class="chip" id="c${r.nombre}"><rect width="44" height="38" rx="8" fill="${COL[i]}"/><text x="22" y="16" text-anchor="middle">${r.nombre}</text>
      <text x="22" y="31" text-anchor="middle" style="font-size:10px;font-weight:400" id="r${r.nombre}"></text></g>`;
  });
  $('stage').setAttribute('viewBox', `0 0 760 ${H}`); $('stage').innerHTML = s;
  R.rows.forEach(r => chips[r.nombre] = $('c' + r.nombre));
  chips.laneY = laneY; chips.finY = finY;
}
function place(name, x, y) { chips[name].style.transform = `translate(${x}px,${y}px)`; }

function show(t) {
  cur = t; const sn = R.snaps[t], done = t >= R.T;
  $('scrub').value = t;
  $('tt').textContent = done ? `t = ${t} (fin: todos terminaron)` : `t = ${t}`;
  const left = S - (t % S);
  $('bt').innerHTML = `Próximo boost en ${left} (cada S = ${S})<div class="bar"><i style="width:${(S - left) / S * 100}%"></i></div>`;
  R.rows.forEach(r => {
    const nm = r.nombre; let x = LX, y = GAP;
    if (sn.cpu === nm) { x = 638; y = 100; }
    else if (sn.pend.includes(nm)) { x = LX + sn.pend.indexOf(nm) * STEP; y = GAP; }
    else if (sn.fin.includes(nm)) { x = LX + sn.fin.indexOf(nm) * STEP; y = chips.finY + GAP; }
    else { const qi = sn.colas.findIndex(q => q.includes(nm)); x = LX + sn.colas[qi].indexOf(nm) * STEP; y = chips.laneY(qi) + GAP; }
    place(nm, x, y); $('r' + nm).textContent = 'r = ' + sn.rest[nm];
  });
  if (sn.cpu) {
    const q = Q[sn.nivel];
    $('qb').setAttribute('width', 140 * sn.usado / q); $('qt').textContent = `Q${sn.nivel + 1} · quantum usado ${sn.usado}/${q}`;
  } else { $('qb').setAttribute('width', 0); $('qt').textContent = done ? 'Sin procesos' : 'CPU ociosa'; }

  $('gantt').innerHTML = R.ticks.slice(0, t).map((k, i) => {
    const bo = i > 0 && i % S === 0 ? ' bo' : '';
    return k.n ? `<div class="c${bo}" style="background:${COL[+k.n.slice(1) - 1]}"><b>${k.n}</b><i>Q${k.q + 1}</i><u>${i}</u></div>`
      : `<div class="c idle${bo}"><b>--</b><i>&nbsp;</i><u>${i}</u></div>`;
  }).join('') || '<span class="m">Aún no se ha ejecutado nada.</span>';

  let h = '';
  Object.keys(R.ev).map(Number).filter(k => k <= t).sort((a, b) => a - b).forEach(k =>
    R.ev[k].forEach(e => h += `<div class="k-${e.k}${k === t ? ' now' : ''}"><b>t = ${k}</b> &nbsp;${e.m}</div>`));
  $('log').innerHTML = h || '<div>Presiona Reproducir o Adelante.</div>'; $('log').scrollTop = 1e6;

  const maxE = Math.max(1, ...R.rows.map(r => r.esp));
  let tb = '<tr><th>Proceso</th><th>Llegada</th><th>Ráfaga</th><th>Restante</th><th>Salida</th><th>En el sistema<br>(salida − llegada)</th><th>Espera<br>(salida − llegada − ráfaga)</th><th>Respuesta</th></tr>';
  R.rows.forEach((r, i) => {
    const f = sn.fin.includes(r.nombre);
    tb += `<tr><td><span class="dot" style="background:${COL[i]}"></span>${r.nombre}</td><td class="n">${r.llegada}</td><td class="n">${r.rafaga}</td><td class="n">${sn.rest[r.nombre]}</td>
    <td class="n">${f ? r.salida : '—'}</td><td class="n">${f ? `${r.salida} − ${r.llegada} = ${r.sis}` : '—'}</td>
    <td class="n">${f ? `${r.salida} − ${r.llegada} − ${r.rafaga} = ${r.esp}<span class="w" style="width:${r.esp / maxE * 50}px"></span>` : '—'}</td>
    <td class="n">${r.primer <= t && (r.primer < t || sn.cpu === r.nombre) ? `${r.primer} − ${r.llegada} = ${r.resp}` : '—'}</td></tr>`;
  });
  if (done) tb += `<tr class="avg"><td colspan="5">Promedios</td><td class="n">${R.avgSis.toFixed(2)}</td><td class="n">${R.avgEsp.toFixed(2)}</td><td class="n">${R.avgResp.toFixed(2)}</td></tr>`;
  $('tbl').innerHTML = tb;
  const w = R.rows.reduce((a, b) => b.esp > a.esp ? b : a);
  $('sum').textContent = done ? `Utilización de CPU: ${R.util.toFixed(1)}%. Proceso que más espera: ${w.nombre} (${w.esp} unidades).` : '';
}
