"""
main.py - Programa de consola para el algoritmo MLFQ.

Pide los datos, ejecuta la simulación (mlfq.py) y muestra:
    - El orden de ejecución paso a paso (eventos).
    - El diagrama de Gantt en texto.
    - El procedimiento de cálculo de salida, tiempo en el sistema y espera.
    - Los promedios.
"""

import colorama
colorama.just_fix_windows_console()

from mlfq import (Proceso, simular, MAX_PROCESOS, RAFAGA_MIN, RAFAGA_MAX)

# --------------------------------------------------------------------------- #
# Visualizacion de resultados en consola, con colores y formato centrado.
# --------------------------------------------------------------------------- #
RESET, NEGRITA = "\033[0m", "\033[1m"
CYAN, VERDE, AMARILLO, ROJO, GRIS = "\033[36m", "\033[32m", "\033[33m", "\033[31m", "\033[90m"

ANCHO_TOTAL = 70

ESTILOS = [
    ("llega",       CYAN,     "→"),
    ("toma la CPU", VERDE,    "▶"),
    ("agota",       AMARILLO, "▼"),
    ("TERMINA",     ROJO,     "■"),
]

# fondos de color con texto negro, uno por proceso
FONDOS = ["\033[30;46m", "\033[30;42m", "\033[30;43m", "\033[30;45m", "\033[30;44m", "\033[30;47m"]

def b(texto):
    """Devuelve el texto en negrita."""
    return f"{NEGRITA}{texto}{RESET}"


def titulo(texto):
    """Titulo con marco, siempre del ancho exacto."""
    print("\n" + b("=" * ANCHO_TOTAL))
    print(b("‖") + b(texto.center(ANCHO_TOTAL - 2)) + b("‖"))
    print(b("=" * ANCHO_TOTAL) + "\n")


def caja(lineas):
    """Caja con bordes. Las líneas deben ser texto plano (sin códigos de color)."""
    ancho = max(len(l) for l in lineas)
    print("  ┌" + "─" * (ancho + 2) + "┐")

    for l in lineas:
        print(f"  │ {l:<{ancho}} │")
    print("  └" + "─" * (ancho + 2) + "┘")


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
            print(f"  {ROJO}Debe ser un número entero{RESET}")
            continue

        if valor < minimo or (maximo is not None and valor > maximo):
            rango = f"entre {minimo} y {maximo}" if maximo is not None else f"de al menos {minimo}"

            print(f"  {ROJO}El valor debe estar {rango}{RESET}")
            continue

        return valor


def pedir_datos():
    print(f"\n{b('───')} Ingrese los siguientesdatos de los procesos {b('───')}\n")
    n = pedir_entero(f"{b('#')} Número de procesos (1 a {MAX_PROCESOS}): ", 1, MAX_PROCESOS)
    print()

    procesos = []
    for i in range(1, n + 1):
        llegada = pedir_entero(f"  {b('>') } P{i} - tiempo de llegada: ", 0)
        rafaga = pedir_entero(f"     {b('»')} P{i} - ráfaga ({RAFAGA_MIN} a {RAFAGA_MAX}): ", RAFAGA_MIN, RAFAGA_MAX)
        procesos.append(Proceso(f"P{i}", llegada, rafaga))

    print(GRIS + "─" * ANCHO_TOTAL + RESET)
    print(f"\n{b('───')} Configuración de MLFQ {b('───')}\n")
    n_colas = pedir_entero(f"{b('#')} Cantidad de colas (1 a 5): ", 1, 5)
    print()

    quantums = [pedir_entero(f"  {b('>') } Quantum de Q{i} (Q1 es la de mayor prioridad): ", 1)
                for i in range(1, n_colas + 1)]

    print()
    s = pedir_entero(f"{b('#')} Tiempo S (cada cuánto todos vuelven a Q1): ", 1)
    return procesos, quantums, s


# --------------------------------------------------------------------------- #
# Salida por pantalla 
# --------------------------------------------------------------------------- #
def mostrar_datos(procesos, quantums, s):
    titulo("DATOS INGRESADOS")

    anchos = [8, 7, 7]
    def fila_tabla(valores):
        return " │ ".join(f"{v:^{a}}" for v, a in zip(valores, anchos))

    print("  " + b(fila_tabla(["Proceso", "Llegada", "Ráfaga"])))
    print("  " + "─┼─".join("─" * a for a in anchos))

    for p in procesos:
        print("  " + fila_tabla([p.nombre, p.llegada, p.rafaga]))

    print(f"\n  {b('>')} Colas y quantum: " + ", ".join(f"Q{i + 1} = {q}" for i, q in enumerate(quantums)))
    print(f"  {b('>')} Boost cada S = {s} unidades de tiempo")


def mostrar_eventos(res):
    titulo("ORDEN DE EJECUCIÓN PASO A PASO")
    t_anterior = None

    for t, texto in res.eventos:
        if t_anterior is not None and t != t_anterior:
            print()

        color, icono = next(
            ((c, i) for clave, c, i in ESTILOS if clave in texto), 
            (RESET, "·")
        )

        marca_t = f"t = {t:<3}" if t != t_anterior else " " * 7

        nombre, resto = texto.split(" ", 1)

        print(f"  {GRIS}{marca_t}{RESET}  {color}{icono} {NEGRITA}{nombre:<3}{RESET}{color}{resto}{RESET}")
        t_anterior = t


def mostrar_gantt(res, ancho_bloque=20):
    """Gantt en texto: una celda de 4 caracteres por unidad de tiempo."""
    # un color distinto para cada proceso
    colores = {f.nombre: FONDOS[i % len(FONDOS)] for i, f in enumerate(res.filas)}

    ticks = []
    for seg in res.segmentos:
        for _ in range(seg.fin - seg.inicio):
            ticks.append((seg.nombre or "--", f"Q{seg.nivel + 1}" if seg.nivel is not None else "  "))

    titulo("DIAGRAMA DE GANTT")

    for inicio in range(0, len(ticks), ancho_bloque):
        bloque = ticks[inicio:inicio + ancho_bloque]

        tiempos = "".join(f"{inicio + i:<4}" for i in range(len(bloque))) + f"{inicio + len(bloque)}"
        cpu = "".join(f"{colores.get(n, GRIS)}{n:^4}{RESET}" for n, _ in bloque)
        colas = "".join(f"{GRIS}{q:^4}{RESET}" for _, q in bloque)

        print(f"  {GRIS}Tiempo:{RESET} {tiempos}")
        print(f"  {b('CPU:'):<{7 + len(NEGRITA) + len(RESET)}} {cpu}")
        print(f"  {GRIS}Cola:{RESET}   {colas}")
        print()

    print(b(">") + " Segmentos:")
    for seg in res.segmentos:
        nombre = seg.nombre or "ocioso"
        cola = f" (Q{seg.nivel + 1})" if seg.nivel is not None else ""
        print(f"    {colores.get(seg.nombre, GRIS)} {nombre} {RESET} [{seg.inicio}-{seg.fin}]{cola}")


def mostrar_calculos(res):
    titulo("PROCEDIMIENTO DE CÁLCULO")

    print(b("  Fórmulas:"))
    caja([
        "Tiempo en el sistema = salida - llegada",
        "Tiempo de espera     = salida - llegada - ráfaga",
        "Tiempo de respuesta  = primer uso de CPU - llegada",
    ])
    print()

    for f in res.filas:
        print(f"  {b('>')} {b(f.nombre)}: salida = {f.salida}")
        print(f"      en el sistema = {f.salida} - {f.llegada} = {f.en_sistema}")
        print(f"      espera        = {f.salida} - {f.llegada} - {f.rafaga} = {f.espera}")
        print(f"      respuesta     = {f.llegada + f.respuesta} - {f.llegada} = {f.respuesta}\n")

    titulo("TABLA DE RESULTADOS")

    anchos = [8, 7, 7, 7, 8, 7, 6]
    encabezados = ["Proceso", "Llegada", "Ráfaga", "Salida", "En sist.", "Espera", "Resp."]

    def fila_tabla(valores):
        return " │ ".join(f"{v:^{a}}" for v, a in zip(valores, anchos))

    print("  " + b(fila_tabla(encabezados)))
    print("  " + "─┼─".join("─" * a for a in anchos))
    for f in res.filas:
        print("  " + fila_tabla([f.nombre, f.llegada, f.rafaga, f.salida, f.en_sistema, f.espera, f.respuesta]))

    n = len(res.filas)
    print(f"\n  {b('Promedios:')}")
    print(f"    {b('»')} Tiempo en el sistema = ({' + '.join(str(f.en_sistema) for f in res.filas)}) / {n} = {VERDE}{res.prom_en_sistema:.2f}{RESET}")
    print(f"    {b('»')} Tiempo de espera     = ({' + '.join(str(f.espera) for f in res.filas)}) / {n} = {VERDE}{res.prom_espera:.2f}{RESET}")
    print(f"    {b('»')} Tiempo de respuesta  = ({' + '.join(str(f.respuesta) for f in res.filas)}) / {n} = {VERDE}{res.prom_respuesta:.2f}{RESET}")

    print(f"\n  Tiempo total: {b(res.tiempo_total)}   Utilización de CPU: {b(f'{res.utilizacion_cpu:.1f}%')}")

    mayor = max(res.filas, key=lambda f: f.espera)
    print(f"  {ROJO}Proceso que más espera: {b(mayor.nombre)}{ROJO} ({mayor.espera} unidades){RESET}\n")
    print(b("=" * ANCHO_TOTAL))


# --------------------------------------------------------------------------- #
# Programa principal
# --------------------------------------------------------------------------- #
def main():
    print()
    print(b("╔" + "═" * (ANCHO_TOTAL - 2) + "╗"))
    print(b("║") + b("SIMULADOR DE PLANIFICACIÓN MLFQ".center(ANCHO_TOTAL - 2)) + b("║"))
    print(b("║") + "(Multi-Level Feedback Queue)".center(ANCHO_TOTAL - 2) + b("║"))
    print(b("╚" + "═" * (ANCHO_TOTAL - 2) + "╝"))

    procesos, quantums, s = pedir_datos()

    res = simular(procesos, quantums, s)
    mostrar_datos(procesos, quantums, s)
    mostrar_eventos(res)
    mostrar_gantt(res)
    mostrar_calculos(res)
    
if __name__ == "__main__":
    main()