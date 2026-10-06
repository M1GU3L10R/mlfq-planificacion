"""
main.py - Programa de consola para el algoritmo MLFQ.

Pide los datos, ejecuta la simulación (mlfq.py) y muestra:
- el orden de ejecución paso a paso (eventos),
- el diagrama de Gantt en texto,
- el procedimiento de cálculo de salida, tiempo en el sistema y espera,
- los promedios.
"""

from mlfq import (Proceso, simular, MAX_PROCESOS, RAFAGA_MIN, RAFAGA_MAX)

# Ejemplo propio del grupo (el mismo de la presentación).
EJEMPLO_PROCESOS = [Proceso("P1", 0, 12), Proceso("P2", 1, 5), Proceso("P3", 3, 3),
                    Proceso("P4", 9, 6), Proceso("P5", 18, 4)]
EJEMPLO_QUANTUMS = [2, 4, 8]
EJEMPLO_S = 20


# --------------------------------------------------------------------------- #
# Entrada de datos
# --------------------------------------------------------------------------- #
def pedir_entero(mensaje, minimo, maximo=None):
    """Pide un entero y repite la pregunta hasta que sea válido."""
    while True:
        texto = input(mensaje).strip()
        try:
            valor = int(texto)
        except ValueError:
            print("  Debe ser un número entero.")
            continue
        if valor < minimo or (maximo is not None and valor > maximo):
            rango = f"entre {minimo} y {maximo}" if maximo is not None else f"de al menos {minimo}"
            print(f"  El valor debe estar {rango}.")
            continue
        return valor


def pedir_datos():
    print("\n--- Ingrese los siguientesdatos de los procesos ---\n")
    n = pedir_entero(f"# Número de procesos (1 a {MAX_PROCESOS}): ", 1, MAX_PROCESOS)
    procesos = []
    for i in range(1, n + 1):
        llegada = pedir_entero(f"  › P{i} - tiempo de llegada: ", 0)
        rafaga = pedir_entero(f"     » P{i} - ráfaga ({RAFAGA_MIN} a {RAFAGA_MAX}): ", RAFAGA_MIN, RAFAGA_MAX)
        procesos.append(Proceso(f"P{i}", llegada, rafaga))

    print("_" * 70)
    print("\n--- Configuración de MLFQ ---\n")
    n_colas = pedir_entero("# Cantidad de colas (1 a 5): ", 1, 5)
    quantums = [pedir_entero(f"  › Quantum de Q{i} (Q1 es la de mayor prioridad): ", 1)
                for i in range(1, n_colas + 1)]
    s = pedir_entero("\nTiempo S (cada cuánto todos vuelven a Q1): ", 1)
    return procesos, quantums, s


# --------------------------------------------------------------------------- #
# Salida por pantalla
# --------------------------------------------------------------------------- #
def mostrar_datos(procesos, quantums, s):
    print("\n" + "=" * 70)
    print("DATOS INGRESADOS")
    print("=" * 70)
    print(f"{'Proceso':<10}{'Llegada':>10}{'Ráfaga':>10}")
    for p in procesos:
        print(f"{p.nombre:<10}{p.llegada:>10}{p.rafaga:>10}")
    print("\nColas y quantum: " + ", ".join(f"Q{i + 1} = {q}" for i, q in enumerate(quantums)))
    print(f"Boost cada S = {s} unidades de tiempo")


def mostrar_eventos(res):
    print("\n" + "=" * 70)
    print("ORDEN DE EJECUCIÓN PASO A PASO")
    print("=" * 70)
    for t, texto in res.eventos:
        print(f"  t = {t:>3}  {texto}")


def mostrar_gantt(res, ancho_bloque=20):
    """Gantt en texto: una celda de 4 caracteres por unidad de tiempo."""
    ticks = []
    for seg in res.segmentos:
        for _ in range(seg.fin - seg.inicio):
            ticks.append((seg.nombre or "--", f"Q{seg.nivel + 1}" if seg.nivel is not None else "  "))

    print("\n" + "=" * 70)
    print("DIAGRAMA DE GANTT")
    print("=" * 70)
    for inicio in range(0, len(ticks), ancho_bloque):
        bloque = ticks[inicio:inicio + ancho_bloque]
        print("Tiempo: " + "".join(f"{inicio + i:<4}" for i in range(len(bloque))) + f"{inicio + len(bloque)}")
        print("CPU:    " + "".join(f"{n:<4}" for n, _ in bloque))
        print("Cola:   " + "".join(f"{q:<4}" for _, q in bloque))
        print()
    print("Segmentos:  " + "  ".join(f"[{seg.inicio}-{seg.fin}] {seg.nombre or 'ocioso'}"
                                      + (f"(Q{seg.nivel + 1})" if seg.nivel is not None else "")
                                      for seg in res.segmentos))


def mostrar_calculos(res):
    print("\n" + "=" * 70)
    print("PROCEDIMIENTO DE CÁLCULO")
    print("=" * 70)
    print("Tiempo en el sistema = salida - llegada")
    print("Tiempo de espera     = salida - llegada - ráfaga")
    print("Tiempo de respuesta  = primer uso de CPU - llegada\n")
    for f in res.filas:
        print(f"{f.nombre}: salida = {f.salida}")
        print(f"    en el sistema = {f.salida} - {f.llegada} = {f.en_sistema}")
        print(f"    espera        = {f.salida} - {f.llegada} - {f.rafaga} = {f.espera}")
        print(f"    respuesta     = {f.llegada + f.respuesta} - {f.llegada} = {f.respuesta}")

    print("\n" + "=" * 70)
    print("TABLA DE RESULTADOS")
    print("=" * 70)
    print(f"{'Proceso':<9}{'Llegada':>8}{'Ráfaga':>8}{'Salida':>8}{'En sist.':>10}{'Espera':>8}{'Resp.':>7}")
    for f in res.filas:
        print(f"{f.nombre:<9}{f.llegada:>8}{f.rafaga:>8}{f.salida:>8}{f.en_sistema:>10}{f.espera:>8}{f.respuesta:>7}")

    n = len(res.filas)
    print("\nPromedios:")
    print(f"  Tiempo en el sistema = ({' + '.join(str(f.en_sistema) for f in res.filas)}) / {n} = {res.prom_en_sistema:.2f}")
    print(f"  Tiempo de espera     = ({' + '.join(str(f.espera) for f in res.filas)}) / {n} = {res.prom_espera:.2f}")
    print(f"  Tiempo de respuesta  = ({' + '.join(str(f.respuesta) for f in res.filas)}) / {n} = {res.prom_respuesta:.2f}")
    print(f"\nTiempo total: {res.tiempo_total}   Utilización de CPU: {res.utilizacion_cpu:.1f}%")

    mayor = max(res.filas, key=lambda f: f.espera)
    print(f"Proceso que más espera: {mayor.nombre} ({mayor.espera} unidades)")


# --------------------------------------------------------------------------- #
# Programa principal
# --------------------------------------------------------------------------- #
def main():
    print("\t","=" * 70)
    print("\t ‖    SIMULADOR DE PLANIFICACIÓN MLFQ (Multi-Level Feedback Queue)    ‖")
    print("\t ‖","-" * 66, "‖")
    print("\t ‖          Bienvenido al simulador de planificación MLFQ.            ‖")         
    print("\t","=" * 70)

    procesos, quantums, s = pedir_datos()

    res = simular(procesos, quantums, s)
    mostrar_datos(procesos, quantums, s)
    mostrar_eventos(res)
    mostrar_gantt(res)
    mostrar_calculos(res)

if __name__ == "__main__":
    main()