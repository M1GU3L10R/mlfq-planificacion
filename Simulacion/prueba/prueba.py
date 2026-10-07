"""
main.py - Programa de consola para el algoritmo MLFQ.
Diseño centrado mediante bloque contenedor fijo sobre la terminal.
"""

import shutil
from mlfq import (Proceso, simular, MAX_PROCESOS, RAFAGA_MIN, RAFAGA_MAX)

ANCHO_BLOQUE = 70  # Ancho estándar para el contenido central


def obtener_margen():
    """Calcula el número de espacios a la izquierda para centrar el bloque de 70 caracteres."""
    ancho_terminal = shutil.get_terminal_size((80, 20)).columns
    return " " * max(0, (ancho_terminal - ANCHO_BLOQUE) // 2)


def cprint(texto=""):
    """Imprime una línea añadiendo el margen izquierdo para centrar el contenido."""
    margen = obtener_margen()
    for linea in str(texto).splitlines():
        print(f"{margen}{linea}")


def cinput(prompt=""):
    """Pide datos por teclado manteniendo la pregunta dentro del bloque centrado."""
    margen = obtener_margen()
    return input(f"{margen}{prompt}")


def pedir_entero(mensaje, minimo, maximo=None):
    """Pide un entero y repite la pregunta hasta que sea válido."""
    while True:
        texto = cinput(mensaje).strip()
        try:
            valor = int(texto)
        except ValueError:
            cprint("  Debe ser un número entero.")
            continue
        if valor < minimo or (maximo is not None and valor > maximo):
            rango = f"entre {minimo} y {maximo}" if maximo is not None else f"de al menos {minimo}"
            cprint(f"  El valor debe estar {rango}.")
            continue
        return valor


def pedir_datos():
    cprint("\n" + "--- Ingrese los datos de los procesos ---".center(ANCHO_BLOQUE) + "\n")
    n = pedir_entero(f"# Número de procesos (1 a {MAX_PROCESOS}): ", 1, MAX_PROCESOS)
    procesos = []
    for i in range(1, n + 1):
        llegada = pedir_entero(f"  › P{i} - tiempo de llegada: ", 0)
        rafaga = pedir_entero(f"    » P{i} - ráfaga ({RAFAGA_MIN} a {RAFAGA_MAX}): ", RAFAGA_MIN, RAFAGA_MAX)
        procesos.append(Proceso(f"P{i}", llegada, rafaga))

    cprint("_" * ANCHO_BLOQUE)
    cprint("\n" + "--- Configuración de MLFQ ---".center(ANCHO_BLOQUE) + "\n")
    n_colas = pedir_entero("# Cantidad de colas (1 a 5): ", 1, 5)
    quantums = [pedir_entero(f"  › Quantum de Q{i} (Q1 es la de mayor prioridad): ", 1)
                for i in range(1, n_colas + 1)]
    
    # Se imprime la línea en blanco con cprint() antes del prompt
    cprint()
    s = pedir_entero("Tiempo S (cada cuánto todos vuelven a Q1): ", 1)
    return procesos, quantums, s


# --------------------------------------------------------------------------- #
# Salida centrada por pantalla
# --------------------------------------------------------------------------- #
def mostrar_datos(procesos, quantums, s):
    cprint("\n" + "=" * ANCHO_BLOQUE)
    cprint("DATOS INGRESADOS".center(ANCHO_BLOQUE))
    cprint("=" * ANCHO_BLOQUE)
    
    cprint(f"{'Proceso':<10}{'Llegada':>10}{'Ráfaga':>10}".center(ANCHO_BLOQUE))
    for p in procesos:
        cprint(f"{p.nombre:<10}{p.llegada:>10}{p.rafaga:>10}".center(ANCHO_BLOQUE))
    
    texto_colas = "Colas y quantum: " + ", ".join(f"Q{i + 1} = {q}" for i, q in enumerate(quantums))
    texto_boost = f"Boost cada S = {s} unidades de tiempo"
    
    cprint("\n" + texto_colas.center(ANCHO_BLOQUE))
    cprint(texto_boost.center(ANCHO_BLOQUE))


def mostrar_eventos(res):
    cprint("\n" + "=" * ANCHO_BLOQUE)
    cprint("ORDEN DE EJECUCIÓN PASO A PASO".center(ANCHO_BLOQUE))
    cprint("=" * ANCHO_BLOQUE)
    for t, texto in res.eventos:
        cprint(f"  t = {t:>3}  {texto}")


def mostrar_gantt(res, ancho_bloque=15):
    """Gantt en texto centrado."""
    ticks = []
    for seg in res.segmentos:
        for _ in range(seg.fin - seg.inicio):
            ticks.append((seg.nombre or "--", f"Q{seg.nivel + 1}" if seg.nivel is not None else "  "))

    cprint("\n" + "=" * ANCHO_BLOQUE)
    cprint("DIAGRAMA DE GANTT".center(ANCHO_BLOQUE))
    cprint("=" * ANCHO_BLOQUE)
    
    for inicio in range(0, len(ticks), ancho_bloque):
        bloque = ticks[inicio:inicio + ancho_bloque]
        linea_tiempo = "Tiempo: " + "".join(f"{inicio + i:<4}" for i in range(len(bloque))) + f"{inicio + len(bloque)}"
        linea_cpu    = "CPU:    " + "".join(f"{n:<4}" for n, _ in bloque)
        linea_cola   = "Cola:   " + "".join(f"{q:<4}" for _, q in bloque)
        
        cprint(linea_tiempo)
        cprint(linea_cpu)
        cprint(linea_cola)
        cprint()

    texto_segmentos = "Segmentos:  " + "  ".join(f"[{seg.inicio}-{seg.fin}] {seg.nombre or 'ocioso'}"
                                                 + (f"(Q{seg.nivel + 1})" if seg.nivel is not None else "")
                                                 for seg in res.segmentos)
    cprint(texto_segmentos)


def mostrar_calculos(res):
    cprint("\n" + "=" * ANCHO_BLOQUE)
    cprint("PROCEDIMIENTO DE CÁLCULO".center(ANCHO_BLOQUE))
    cprint("=" * ANCHO_BLOQUE)
    cprint("Tiempo en el sistema = salida - llegada".center(ANCHO_BLOQUE))
    cprint("Tiempo de espera     = salida - llegada - ráfaga".center(ANCHO_BLOQUE))
    cprint("Tiempo de respuesta  = primer uso de CPU - llegada\n".center(ANCHO_BLOQUE))
    
    for f in res.filas:
        cprint(f"{f.nombre}: salida = {f.salida}")
        cprint(f"    en el sistema = {f.salida} - {f.llegada} = {f.en_sistema}")
        cprint(f"    espera        = {f.salida} - {f.llegada} - {f.rafaga} = {f.espera}")
        cprint(f"    respuesta     = {f.llegada + f.respuesta} - {f.llegada} = {f.respuesta}\n")

    cprint("=" * ANCHO_BLOQUE)
    cprint("TABLA DE RESULTADOS".center(ANCHO_BLOQUE))
    cprint("=" * ANCHO_BLOQUE)
    
    encabezado = f"{'Proceso':<9}{'Llegada':>8}{'Ráfaga':>8}{'Salida':>8}{'En sist.':>10}{'Espera':>8}{'Resp.':>7}"
    cprint(encabezado.center(ANCHO_BLOQUE))
    
    for f in res.filas:
        fila = f"{f.nombre:<9}{f.llegada:>8}{f.rafaga:>8}{f.salida:>8}{f.en_sistema:>10}{f.espera:>8}{f.respuesta:>7}"
        cprint(fila.center(ANCHO_BLOQUE))

    n = len(res.filas)
    cprint("\nPromedios:")
    cprint(f"  Tiempo en el sistema = ({' + '.join(str(f.en_sistema) for f in res.filas)}) / {n} = {res.prom_en_sistema:.2f}")
    cprint(f"  Tiempo de espera     = ({' + '.join(str(f.espera) for f in res.filas)}) / {n} = {res.prom_espera:.2f}")
    cprint(f"  Tiempo de respuesta  = ({' + '.join(str(f.respuesta) for f in res.filas)}) / {n} = {res.prom_respuesta:.2f}")
    
    resumen_global = f"Tiempo total: {res.tiempo_total}   Utilización de CPU: {res.utilizacion_cpu:.1f}%"
    cprint(f"\n{resumen_global}".center(ANCHO_BLOQUE))

    mayor = max(res.filas, key=lambda f: f.espera)
    cprint(f"Proceso que más espera: {mayor.nombre} ({mayor.espera} unidades)".center(ANCHO_BLOQUE))


# --------------------------------------------------------------------------- #
# Programa principal
# --------------------------------------------------------------------------- #
def main():
    titulo_1 = "SIMULADOR DE PLANIFICACIÓN MLFQ (Multi-Level Feedback Queue)"
    titulo_2 = "Bienvenido al simulador de planificación MLFQ."
    
    cprint("=" * ANCHO_BLOQUE)
    cprint(f"‖ {titulo_1.center(ANCHO_BLOQUE - 4)} ‖")
    cprint(f"‖ {'-' * (ANCHO_BLOQUE - 4)} ‖")
    cprint(f"‖ {titulo_2.center(ANCHO_BLOQUE - 4)} ‖")
    cprint("=" * ANCHO_BLOQUE)

    procesos, quantums, s = pedir_datos()

    res = simular(procesos, quantums, s)
    mostrar_datos(procesos, quantums, s)
    mostrar_eventos(res)
    mostrar_gantt(res)
    mostrar_calculos(res)

if __name__ == "__main__":
    main()