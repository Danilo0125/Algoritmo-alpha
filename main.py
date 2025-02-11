def parse_log(log_str):
    """Convierte una cadena de log en lista de trazas"""
    traces = []
    for part in log_str.strip('[]').split(', '):
        part = part.strip()
        if '^' in part:
            trace_part, count = part.rsplit('^', 1)
            count = int(count)
        else:
            trace_part = part
            count = 1

        trace = trace_part.strip('<>').replace(' ', '').split(',')
        traces.extend([trace] * count)
    return traces


def calculate_relations(traces):
    """Calcula todas las relaciones entre actividades"""
    activities = sorted({act for trace in traces for act in trace})
    direct = {}

    # Sucesiones directas
    for trace in traces:
        for i in range(len(trace) - 1):
            pair = (trace[i], trace[i + 1])
            direct[pair] = direct.get(pair, 0) + 1

    # Inicializar relaciones
    causality = set()
    parallel = set()
    decision = set()

    # Comparar todos los pares posibles
    for x in activities:
        for y in activities:
            if x == y:
                decision.add((x, y))
                continue

            xy = direct.get((x, y), 0)
            yx = direct.get((y, x), 0)

            if xy > 0 and yx == 0:
                causality.add((x, y))
            elif xy > 0 and yx > 0:
                parallel.add((x, y))
            elif xy == 0 and yx == 0:
                decision.add((x, y))

    return {
        'direct': direct,
        'causality': causality,
        'parallel': parallel,
        'decision': decision,
        'activities': activities
    }


def print_results(relations):
    """Muestra los resultados formateados con conteos finales"""
    # Contar relaciones únicas (excluyendo reflexivas en decisiones)
    total_direct = len(relations['direct'])
    total_causality = len(relations['causality'])
    total_parallel = len(relations['parallel'])
    total_decision = len([pair for pair in relations['decision'] if pair[0] != pair[1]])

    # Imprimir detalle
    print("\nSUCESIONES DIRECTAS (x > y):")
    for (x, y), count in relations['direct'].items():
        print(f"{x} > {y} ({count} ocurrencias)")

    print("\nCAUSALIDADES (x → y):")
    for x, y in sorted(relations['causality']):
        print(f"{x} → {y}")

    print("\nPARALELISMO (x || y):")
    for x, y in sorted(relations['parallel']):
        print(f"{x} || {y}")

    print("\nDECISIONES (x # y):")
    decisions = [pair for pair in relations['decision'] if pair[0] != pair[1]]
    for x, y in sorted(decisions):
        print(f"{x} # {y}")

    # Imprimir totales
    print(f"\nTOTALES: {total_direct},{total_causality},{total_parallel},{total_decision}")


def main():
    print("ANALIZADOR DE LOGS DE PROCESOS")
    print("Formato de entrada: <a,b,c>, <d,e>^2, <f,g>")

    while True:
        log_input = input("\nIngrese el log (o 'salir' para terminar): ")
        if log_input.lower() == 'salir':
            break

        try:
            traces = parse_log(log_input)
            relations = calculate_relations(traces)
            print_results(relations)
        except Exception as e:
            print(f"Error: {e}. Verifique el formato de entrada.")


if __name__ == "__main__":
    main()