/*
 * control.js - Botones de reproducción
 * Reproducir, pausar, paso adelante/atrás, reiniciar, barra de tiempo y velocidad.
 */

function stop() { clearInterval(timer); timer = null; $('play').textContent = 'Reproducir'; }
function ms() { return 1100 - $('spd').value * 100; }
function start() {
  if (cur >= R.T) show(0);
  $('play').textContent = 'Pausar';
  timer = setInterval(() => { if (cur >= R.T) return stop(); show(cur + 1); if (cur >= R.T) stop(); }, ms());
}
$('play').onclick = () => timer ? stop() : start();
$('spd').oninput = () => { if (timer) { stop(); start(); } };
$('next').onclick = () => { stop(); if (cur < R.T) show(cur + 1); };
$('prev').onclick = () => { stop(); if (cur > 0) show(cur - 1); };
$('rst').onclick = () => { stop(); show(0); };
$('scrub').oninput = e => { stop(); show(+e.target.value); };
