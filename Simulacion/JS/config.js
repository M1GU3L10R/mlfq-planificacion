/*
 * config.js - Constantes y estado compartido
 * Colores de los procesos, el ejemplo del grupo y las variables globales de la simulación.
 */

const COL = ['#2a78d6', '#eb6834', '#1baf7a', '#7a5cd6', '#d4537e'];
const $ = id => document.getElementById(id);
const EJ = { p: [[0, 12], [1, 5], [3, 3], [9, 6], [18, 4]], q: [2, 4, 8], S: 20 };
let R, Q, S, cur = 0, timer = null, chips = {};
