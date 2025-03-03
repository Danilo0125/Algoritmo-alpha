def parse_log(log_str):
    """
    Convierte una cadena de log en lista de trazas.
    Args:
        log_str (str): Cadena de texto que representa el log. 
                       Las trazas están delimitadas por corchetes y separadas por comas.
                       Cada traza puede tener un sufijo '^n' que indica la cantidad de veces que se repite.
    Returns:
        list: Lista de trazas, donde cada traza es una lista de eventos.
    Ejemplo:
        >>> parse_log("[<a, b, c>^2, <d, e>]")
        [['a', 'b', 'c'], ['a', 'b', 'c'], ['d', 'e']]
    """
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
    """
    Calcula todas las relaciones entre actividades en un conjunto de trazas.
    Args:
        traces (list of list of str): Una lista de trazas, donde cada traza es una lista de actividades.
    Returns:
        dict: Un diccionario que contiene las siguientes claves:
            - 'direct' (dict): Un diccionario con pares de actividades como claves y el conteo de sucesiones directas como valores.
            - 'causality' (set): Un conjunto de tuplas que representan relaciones de causalidad (x -> y).
            - 'parallel' (set): Un conjunto de tuplas que representan relaciones de paralelismo (x || y).
            - 'decision' (set): Un conjunto de tuplas que representan relaciones de decisión (x # y).
            - 'activities' (list): Una lista ordenada de actividades únicas.
    """
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
                decision.add((x, y))  # Relaciones reflexivas
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
    # Contar relaciones únicas (incluyendo reflexivas en decisiones)
    total_direct = len(relations['direct'])
    total_causality = len(relations['causality'])
    total_parallel = len(relations['parallel'])
    total_decision = len(relations['decision'])

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
    for x, y in sorted(relations['decision']):
        print(f"{x} # {y}")

    # Imprimir totales
    print(f"\nTOTALES: {total_direct},{total_causality},{total_parallel},{total_decision}")


def build_footprint_matrix(relations):
    """
    Construye la matriz de footprint a partir de las relaciones proporcionadas.
    Args:
        relations (dict): Un diccionario que contiene las relaciones entre actividades. 
                          Debe tener las siguientes claves:
                          - 'activities': Una lista de actividades.
                          - 'causality': Una lista de tuplas que representan relaciones de causalidad (x -> y).
                          - 'parallel': Una lista de tuplas que representan relaciones de paralelismo (x || y).
                          - 'decision': Una lista de tuplas que representan decisiones (x # y).
    Returns:
        dict: Una matriz de footprint representada como un diccionario de diccionarios. 
              Las claves del diccionario externo son las actividades, y los valores son diccionarios 
              que mapean actividades a sus relaciones ('->', '<-', '||', '#', o '').
    """
    """Construye la matriz de footprint"""
    activities = relations['activities']
    matrix = {}

    # Inicializar la matriz con espacios vacíos
    for x in activities:
        matrix[x] = {y: '' for y in activities}

    # Llenar la matriz con las relaciones
    for x, y in relations['causality']:
        matrix[x][y] = '->'
        matrix[y][x] = '<-'  # Causalidad inversa en la posición espejo

    for x, y in relations['parallel']:
        matrix[x][y] = '||'
        matrix[y][x] = '||'  # Paralelismo es simétrico

    for x, y in relations['decision']:
        if x == y:
            matrix[x][y] = '#'  # Decisiones reflexivas (diagonal)
        else:
            matrix[x][y] = '#'
            matrix[y][x] = '#'  # Decisiones son simétricas

    return matrix


def print_footprint_matrix(matrix, activities):
    """
    Imprime la matriz de footprint.
    Args:
        matrix (dict): Un diccionario donde las claves son nombres de actividades y los valores son diccionarios
                       que representan las relaciones de footprint entre actividades.
        activities (list): Una lista de nombres de actividades que se usarán como encabezados y etiquetas de fila en la matriz.
    Returns:
        None
    """
    """Imprime la matriz de footprint"""
    print("\nMATRIZ DE FOOTPRINT:")
    # Imprimir cabecera
    print("    " + "    ".join(activities))

    # Imprimir filas
    for x in activities:
        row = [x]
        for y in activities:
            row.append(matrix[x][y].center(3))
        print("  ".join(row))


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

            # Generar y mostrar la matriz de footprint
            footprint_matrix = build_footprint_matrix(relations)
            print_footprint_matrix(footprint_matrix, relations['activities'])
        except Exception as e:
            print(f"Error: {e}. Verifique el formato de entrada.")


if __name__ == "__main__":
    main()

# Output:
#L9 <a,b,e,f>, <a,b,e,c,d,b,f>, <a,b,c,e,d,b,f>,<ab,c,d,e,b,f>, <a,e,b,c,d,b,f>
#<a,b,e,f>, <a,b,e,c,d,b,f>, <a,b,c,e,d,b,f>,<ab,c,d,e,b,f>, <a,e,b,c,d,b,f>