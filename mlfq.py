"""
mlfq.py - Lógica del algoritmo de planificación MLFQ (Multi-Level Feedback Queue).

Este módulo NO pide datos ni imprime nada: recibe los datos, simula y devuelve un
resultado. Así la misma lógica se puede usar desde la consola (main.py).

Reglas implementadas (las 5 del material de clase, OSTEP):
1. Si Prioridad(A) > Prioridad(B), corre A.
2. Si son iguales, corren en Round Robin con el quantum de la cola.
3. Todo proceso nuevo entra a la cola de mayor prioridad (Q1).
4. Al agotar su quantum en un nivel, el proceso baja una cola.
5. Cada S unidades de tiempo, todos los procesos suben a Q1 (boost).

Decisiones del grupo (el video no las define):
- Expulsión: si llega algo a una cola más prioritaria, el proceso en CPU se
interrumpe, va al final de su misma cola y conserva su nivel y su quantum usado.
- El quantum usado se acumula por nivel (aunque se gaste en varios pedazos).
- Un proceso que termina justo al acabar el quantum sale del sistema (no baja).
- En la última cola se hace Round Robin con el quantum de esa cola.
- En el boost, todos (incluido el que está en CPU) pasan a Q1 ordenados por llegada
y se reinicia su quantum usado.
- Desempate: si dos procesos empatan, va primero el que llegó antes.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

MAX_PROCESOS = 5
RAFAGA_MIN, RAFAGA_MAX = 1, 12


# --------------------------------------------------------------------------- #
# Estructuras de datos
# --------------------------------------------------------------------------- #
@dataclass
class Proceso:
    """Datos de entrada de un proceso."""
    nombre: str
    llegada: int
    rafaga: int


@dataclass
class _Estado:
    """Estado interno de un proceso mientras dura la simulación."""
    proceso: Proceso
    indice: int                 # orden en que se ingresó (sirve para desempatar)
    restante: int               # ráfaga que aún le falta
    nivel: int = 0              # 0 = Q1, 1 = Q2, ...
    usado: int = 0              # quantum ya gastado en el nivel actual
    primer_uso: int | None = None
    salida: int | None = None

    @property
    def nombre(self):
        return self.proceso.nombre


@dataclass
class Segmento:
    """Un bloque continuo del diagrama de Gantt."""
    nombre: str | None          # None = CPU ociosa
    inicio: int
    fin: int
    nivel: int | None           # índice de cola (0 = Q1) o None si ociosa


@dataclass
class Fila:
    """Resultados de un proceso."""
    nombre: str
    llegada: int
    rafaga: int
    salida: int
    en_sistema: int
    espera: int
    respuesta: int


@dataclass
class Resultado:
    segmentos: list = field(default_factory=list)
    eventos: list = field(default_factory=list)      # lista de (tiempo, texto)
    trazas: list = field(default_factory=list)       # estado de las colas por tick
    filas: list = field(default_factory=list)
    prom_en_sistema: float = 0.0
    prom_espera: float = 0.0
    prom_respuesta: float = 0.0
    tiempo_total: int = 0
    utilizacion_cpu: float = 0.0


# --------------------------------------------------------------------------- #
# Validación
# --------------------------------------------------------------------------- #
def validar_configuracion(procesos, quantums, s):
    """Lanza ValueError con un mensaje claro si algún dato no es válido."""
    if not 1 <= len(procesos) <= MAX_PROCESOS:
        raise ValueError(f"El número de procesos debe estar entre 1 y {MAX_PROCESOS}.")
    nombres = [p.nombre for p in procesos]
    if len(set(nombres)) != len(nombres):
        raise ValueError("Los nombres de los procesos no pueden repetirse.")
    for p in procesos:
        if p.llegada < 0:
            raise ValueError(f"{p.nombre}: la llegada no puede ser negativa.")
        if not RAFAGA_MIN <= p.rafaga <= RAFAGA_MAX:
            raise ValueError(f"{p.nombre}: la ráfaga debe estar entre {RAFAGA_MIN} y {RAFAGA_MAX}.")
    if len(quantums) < 1:
        raise ValueError("Debe haber al menos una cola.")
    if any(q < 1 for q in quantums):
        raise ValueError("Cada quantum debe ser de al menos 1.")
    if s < 1:
        raise ValueError("El tiempo S debe ser de al menos 1.")


# --------------------------------------------------------------------------- #
# Simulación
# --------------------------------------------------------------------------- #
def simular(procesos, quantums, s):
    """
    Simula MLFQ unidad de tiempo por unidad de tiempo.

    procesos : lista de Proceso
    quantums : lista con el quantum de cada cola, de la más prioritaria a la menos
    prioritaria. Su longitud es la cantidad de colas. Ej.: [2, 4, 8]
    s        : cada cuántas unidades de tiempo se hace el boost
    """
    validar_configuracion(procesos, quantums, s)

    n_colas = len(quantums)
    estados = [_Estado(p, i, p.rafaga) for i, p in enumerate(procesos)]
    # Procesos que aún no han llegado, en orden de llegada (y de ingreso si empatan).
    por_llegar = deque(sorted(estados, key=lambda e: (e.proceso.llegada, e.indice)))
    colas = [deque() for _ in range(n_colas)]

    res = Resultado()
    actual = None          # proceso que tiene la CPU en este momento
    terminados = 0
    t = 0
    ticks = []             # (nombre | None, nivel | None) por cada unidad de tiempo

    def log(texto):
        res.eventos.append((t, texto))

    while terminados < len(estados):

        # ---- 1. BOOST (Regla 5) ------------------------------------------------
        if t > 0 and t % s == 0:
            en_sistema = [e for q in colas for e in q]
            if actual is not None:
                en_sistema.append(actual)
            if en_sistema:
                en_sistema.sort(key=lambda e: (e.proceso.llegada, e.indice))
                for q in colas:
                    q.clear()
                for e in en_sistema:
                    e.nivel, e.usado = 0, 0
                    colas[0].append(e)
                actual = None
                log("BOOST: todos suben a Q1 -> " + ", ".join(e.nombre for e in en_sistema))

        # ---- 2. LLEGADAS (Regla 3) ---------------------------------------------
        while por_llegar and por_llegar[0].proceso.llegada == t:
            e = por_llegar.popleft()
            colas[0].append(e)
            log(f"{e.nombre} llega y entra a Q1 (ráfaga {e.proceso.rafaga})")

        # ---- 3. DECIDIR QUIÉN USA LA CPU (Reglas 1 y 2) ------------------------
        nivel_alto = next((i for i, q in enumerate(colas) if q), None)

        # Expulsión: hay alguien en una cola más prioritaria que la del proceso en CPU.
        if actual is not None and nivel_alto is not None and nivel_alto < actual.nivel:
            colas[actual.nivel].append(actual)
            log(f"{actual.nombre} es expulsado de Q{actual.nivel + 1} "
                f"(le quedan {actual.restante}; usó {actual.usado}/{quantums[actual.nivel]} "
                f"de su quantum) y va al final de Q{actual.nivel + 1}")
            actual = None

        # Si la CPU está libre, se toma el primero de la cola más prioritaria.
        if actual is None and nivel_alto is not None:
            actual = colas[nivel_alto].popleft()
            if actual.primer_uso is None:
                actual.primer_uso = t
            quedan = quantums[actual.nivel] - actual.usado
            log(f"{actual.nombre} toma la CPU en Q{actual.nivel + 1} "
                f"(quantum disponible: {quedan}, ráfaga restante: {actual.restante})")

        # Foto del estado (útil para depurar o para una simulación gráfica).
        res.trazas.append({
            "t": t,
            "cpu": actual.nombre if actual else None,
            "colas": [[e.nombre for e in q] for q in colas],
        })

        # ---- 4. EJECUTAR UNA UNIDAD DE TIEMPO ----------------------------------
        if actual is None:
            ticks.append((None, None))          # CPU ociosa
        else:
            ticks.append((actual.nombre, actual.nivel))
            actual.restante -= 1
            actual.usado += 1

            if actual.restante == 0:            # terminó
                actual.salida = t + 1
                terminados += 1
                res.eventos.append((t + 1, f"{actual.nombre} TERMINA en t = {t + 1}"))
                actual = None
            elif actual.usado >= quantums[actual.nivel]:   # agotó su quantum (Regla 4)
                viejo = actual.nivel
                if viejo < n_colas - 1:
                    actual.nivel += 1
                    texto = f"{actual.nombre} agota su quantum en Q{viejo + 1} y baja a Q{actual.nivel + 1}"
                else:
                    texto = f"{actual.nombre} agota su quantum en Q{viejo + 1} (última cola) y vuelve al final de ella"
                actual.usado = 0
                colas[actual.nivel].append(actual)
                res.eventos.append((t + 1, texto + f" (le quedan {actual.restante})"))
                actual = None
        t += 1

    # ---- Armar el Gantt agrupando unidades consecutivas iguales ---------------
    for i, (nombre, nivel) in enumerate(ticks):
        if res.segmentos and res.segmentos[-1].nombre == nombre and res.segmentos[-1].nivel == nivel:
            res.segmentos[-1].fin = i + 1
        else:
            res.segmentos.append(Segmento(nombre, i, i + 1, nivel))

    # ---- Cálculos pedidos por la guía -----------------------------------------
    for e in estados:
        p = e.proceso
        en_sis = e.salida - p.llegada              # tiempo en el sistema
        res.filas.append(Fila(p.nombre, p.llegada, p.rafaga, e.salida,
        en_sis, en_sis - p.rafaga, e.primer_uso - p.llegada))
    n = len(res.filas)
    res.prom_en_sistema = sum(f.en_sistema for f in res.filas) / n
    res.prom_espera = sum(f.espera for f in res.filas) / n
    res.prom_respuesta = sum(f.respuesta for f in res.filas) / n
    res.tiempo_total = len(ticks)
    ocupadas = sum(1 for nombre, _ in ticks if nombre is not None)
    res.utilizacion_cpu = ocupadas / len(ticks) * 100
    return res
