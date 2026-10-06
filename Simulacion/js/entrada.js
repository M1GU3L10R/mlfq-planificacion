/*
 * entrada.js - Formulario de datos
 * Construye los campos (procesos, colas, quantum), valida lo que pide la guía y,
 * si todo está bien, llama a simular() y muestra la simulación.
 */

for (let i = 1; i <= 5; i++) $('np').add(new Option(i, i));
for (let i = 1; i <= 4; i++) $('nq').add(new Option(i, i));

function buildProcs(vals) {
  const n = +$('np').value;
  $('procs').innerHTML = Array.from({ length: n }, (_, i) =>
    `<div class="row"><span class="dot" style="background:${COL[i]}"></span><b>P${i + 1}</b>
    <label>llegada <input type="number" min="0" class="a" value="${vals ? vals[i][0] : i * 2}"></label>
    <label>ráfaga (1-12) <input type="number" min="1" max="12" class="b" value="${vals ? vals[i][1] : 4}"></label></div>`).join('');
}
function buildQuants(vals) {
  const n = +$('nq').value;
  $('quants').innerHTML = Array.from({ length: n }, (_, i) =>
    `<label>Quantum Q${i + 1} <input type="number" min="1" class="q" value="${vals ? vals[i] : 2 ** (i + 1)}"></label>`).join('');
}
$('np').onchange = () => buildProcs(); $('nq').onchange = () => buildQuants();
$('ex').onclick = () => {
  $('np').value = 5; $('nq').value = 3; $('S').value = EJ.S; buildProcs(EJ.p); buildQuants(EJ.q); $('err').textContent = '';
};
$('np').value = 3; $('nq').value = 3; buildProcs(); buildQuants();

$('go').onclick = () => {
  const A = [...document.querySelectorAll('.a')].map(x => x.value), B = [...document.querySelectorAll('.b')].map(x => x.value);
  const q = [...document.querySelectorAll('.q')].map(x => x.value), s = $('S').value;
  const ints = [...A, ...B, ...q, s];
  if (ints.some(v => v === '' || !Number.isInteger(+v))) return err('Todos los datos deben ser números enteros.');
  if (A.some(v => +v < 0)) return err('La llegada no puede ser negativa.');
  if (B.some(v => +v < 1 || +v > 12)) return err('Cada ráfaga debe estar entre 1 y 12.');
  if (q.some(v => +v < 1)) return err('Cada quantum debe ser de al menos 1.');
  if (+s < 1) return err('S debe ser de al menos 1.');
  err('');
  Q = q.map(Number); S = +s;
  R = simular(A.map((a, i) => ({ nombre: 'P' + (i + 1), llegada: +a, rafaga: +B[i] })), Q, S);
  $('setup').open = false; $('sim').hidden = false;
  $('scrub').max = R.T; initStage(); stop(); show(0);
};
const err = m => { $('err').textContent = m; return false; };
