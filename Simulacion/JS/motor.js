/*
 * motor.js - Lógica del algoritmo MLFQ
 * No toca la pantalla. simular(procesos, quantums, S) recorre el tiempo unidad por unidad
 * y devuelve todo lo necesario para dibujar: una "foto" de las colas en cada instante (snaps),
 * la línea de tiempo del Gantt (ticks), los eventos (ev) y los resultados (rows y promedios).
 * Es la misma lógica de mlfq.py: por eso ambos dan los mismos resultados.
 *
 * Orden de las 4 fases en cada unidad de tiempo:
 *   1. Boost (Regla 5)   2. Llegadas (Regla 3)   3. Decidir quién usa la CPU (Reglas 1 y 2)
 *   4. Ejecutar una unidad (terminar o bajar de cola por quantum, Regla 4)
 */

function simular(procs, quantums, S) {
  const n = quantums.length;
  const E = procs.map((p, i) => ({ ...p, i, rest: p.rafaga, nivel: 0, usado: 0, primer: null, salida: null }));
  const porLlegar = [...E].sort((a, b) => a.llegada - b.llegada || a.i - b.i);
  const colas = Array.from({ length: n }, () => []);
  const ev = {}, ticks = [], snaps = [], fins = [];
  let actual = null, t = 0, fin = 0;
  const log = (tt, k, m) => (ev[tt] = ev[tt] || []).push({ k, m });
  const snap = () => ({
    t, cpu: actual ? actual.nombre : null, nivel: actual ? actual.nivel : null, usado: actual ? actual.usado : 0,
    colas: colas.map(q => q.map(e => e.nombre)), pend: porLlegar.map(e => e.nombre), fin: [...fins],
    rest: Object.fromEntries(E.map(e => [e.nombre, e.rest]))
  });
  while (fin < E.length) {
    if (t > 0 && t % S === 0) {
      const all = colas.flat(); if (actual) all.push(actual);
      if (all.length) {
        all.sort((a, b) => a.llegada - b.llegada || a.i - b.i);
        colas.forEach(q => q.length = 0);
        all.forEach(e => { e.nivel = 0; e.usado = 0; colas[0].push(e); });
        actual = null;
        log(t, 'boost', 'BOOST: todos suben a Q1 → ' + all.map(e => e.nombre).join(', '));
      }
    }
    while (porLlegar.length && porLlegar[0].llegada === t) {
      const e = porLlegar.shift(); colas[0].push(e);
      log(t, 'llega', `${e.nombre} llega y entra a Q1 (ráfaga ${e.rafaga})`);
    }
    const hi = colas.findIndex(q => q.length);
    if (actual && hi >= 0 && hi < actual.nivel) {
      colas[actual.nivel].push(actual);
      log(t, 'exp', `${actual.nombre} es expulsado de Q${actual.nivel + 1} (usó ${actual.usado}/${quantums[actual.nivel]}, le quedan ${actual.rest}) y va al final de Q${actual.nivel + 1}`);
      actual = null;
    }
    if (!actual && hi >= 0) {
      actual = colas[hi].shift();
      if (actual.primer === null) actual.primer = t;
      log(t, 'cpu', `${actual.nombre} toma la CPU en Q${actual.nivel + 1} (quantum disponible ${quantums[actual.nivel] - actual.usado}, ráfaga restante ${actual.rest})`);
    }
    snaps.push(snap());
    if (!actual) ticks.push({ n: null, q: null });
    else {
      ticks.push({ n: actual.nombre, q: actual.nivel });
      actual.rest--; actual.usado++;
      if (actual.rest === 0) {
        actual.salida = t + 1; fin++; fins.push(actual.nombre);
        log(t + 1, 'fin', `${actual.nombre} TERMINA en t = ${t + 1}`); actual = null;
      } else if (actual.usado >= quantums[actual.nivel]) {
        const v = actual.nivel;
        if (v < n - 1) actual.nivel++;
        log(t + 1, 'baja', v < n - 1 ? `${actual.nombre} agota su quantum en Q${v + 1} y baja a Q${actual.nivel + 1} (le quedan ${actual.rest})`
          : `${actual.nombre} agota su quantum en la última cola y vuelve al final de ella (le quedan ${actual.rest})`);
        actual.usado = 0; colas[actual.nivel].push(actual); actual = null;
      }
    }
    t++;
  }
  snaps.push(snap());
  const rows = E.map(e => ({ nombre: e.nombre, llegada: e.llegada, rafaga: e.rafaga, salida: e.salida,
    sis: e.salida - e.llegada, esp: e.salida - e.llegada - e.rafaga, resp: e.primer - e.llegada, primer: e.primer }));
  const avg = k => rows.reduce((s, r) => s + r[k], 0) / rows.length;
  const ocup = ticks.filter(x => x.n).length;
  return { ticks, snaps, ev, rows, T: ticks.length, avgSis: avg('sis'), avgEsp: avg('esp'), avgResp: avg('resp'), util: ocup / ticks.length * 100 };
}
