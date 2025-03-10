from itertools import combinations

class Alpha:
    def __init__(self):
        self.traces = []
        self.direct = {}
        self.causality = set()
        self.parallel = set()
        self.decision = set()
        self.activities = []
        
    def parse_log(self, log_str):
        """Convierte una cadena de log en lista de trazas"""
        self.traces = []
        for part in log_str.strip('[]').split(', '):
            part = part.strip()
            if '^' in part:
                trace_part, count = part.rsplit('^', 1)
                count = int(count)
            else:
                trace_part = part
                count = 1

            trace = trace_part.strip('<>').replace(' ', '').split(',')
            self.traces.extend([trace] * count)
        
        return self  # Permite encadenamiento de métodos

    def calculate_relations(self):
        """Calcula todas las relaciones entre actividades"""
        self.activities = sorted({act for trace in self.traces for act in trace})
        self.direct = {}

        # Sucesiones directas
        for trace in self.traces:
            for i in range(len(trace) - 1):
                pair = (trace[i], trace[i + 1])
                self.direct[pair] = self.direct.get(pair, 0) + 1

        # Inicializar relaciones
        self.causality = set()
        self.parallel = set()
        self.decision = set()

        # Comparar todos los pares posibles
        for x in self.activities:
            for y in self.activities:
                if x == y:
                    self.decision.add((x, y))  # Relaciones reflexivas
                    continue

                xy = self.direct.get((x, y), 0)
                yx = self.direct.get((y, x), 0)

                if xy > 0 and yx == 0:
                    self.causality.add((x, y))
                elif xy > 0 and yx > 0:
                    self.parallel.add((x, y))
                elif xy == 0 and yx == 0:
                    self.decision.add((x, y))

        return self  # Permite encadenamiento de métodos

    def process_log(self, log_str):
        """Procesa un log completo: parsea y calcula las relaciones en un solo paso"""
        return self.parse_log(log_str).calculate_relations()

    def print_results(self):
        """Muestra los resultados formateados con conteos finales"""
        # Contar relaciones únicas (incluyendo reflexivas en decisiones)
        total_direct = len(self.direct)
        total_causality = len(self.causality)
        total_parallel = len(self.parallel)
        total_decision = len(self.decision)

        # Imprimir detalle
        print("\nSUCESIONES DIRECTAS (x > y):")
        for (x, y), count in self.direct.items():
            print(f"{x} > {y} ({count} ocurrencias)")

        print("\nCAUSALIDADES (x → y):")
        for x, y in sorted(self.causality):
            print(f"{x} → {y}")

        print("\nPARALELISMO (x || y):")
        for x, y in sorted(self.parallel):
            print(f"{x} || {y}")

        print("\nDECISIONES (x # y):")
        for x, y in sorted(self.decision):
            print(f"{x} # {y}")

        # Imprimir totales
        print(f"\nTOTALES: {total_direct},{total_causality},{total_parallel},{total_decision}")
        
        return self  # Permite encadenamiento de métodos

    def build_footprint_matrix(self):
        """Construye la matriz de footprint"""
        matrix = {}

        # Inicializar la matriz con espacios vacíos
        for x in self.activities:
            matrix[x] = {y: '' for y in self.activities}

        # Llenar la matriz con las relaciones
        for x, y in self.causality:
            matrix[x][y] = '->'
            matrix[y][x] = '<-'  # Causalidad inversa en la posición espejo

        for x, y in self.parallel:
            matrix[x][y] = '||'
            matrix[y][x] = '||'  # Paralelismo es simétrico

        for x, y in self.decision:
            if x == y:
                matrix[x][y] = '#'  # Decisiones reflexivas (diagonal)
            else:
                matrix[x][y] = '#'
                matrix[y][x] = '#'  # Decisiones son simétricas

        return matrix

    def print_footprint_matrix(self):
        """Imprime la matriz de footprint"""
        matrix = self.build_footprint_matrix()
        print("\nMATRIZ DE FOOTPRINT:")
        # Imprimir cabecera
        print("    " + "    ".join(self.activities))

        # Imprimir filas
        for x in self.activities:
            row = [x]
            for y in self.activities:
                row.append(matrix[x][y].center(3))
            print("  ".join(row))
            
        return self  # Permite encadenamiento de métodos

    def maximize_pairs(self, Xl, Tl):
        """Filtra los pares en Xl para obtener solo aquellos que son máximos"""
        Yl = []
        for A in Tl:
            for B in Tl:
                if A != B:
                    A_set = {A}
                    B_set = {B}
                    if all((a, b) in Xl for a in A_set for b in B_set) and \
                       all((a1, a2) in self.decision for a1 in A_set for a2 in A_set if a1 != a2) and \
                       all((b1, b2) in self.decision for b1 in B_set for b2 in B_set if b1 != b2):
                        Yl.append((A_set, B_set))
        return Yl

    def get_relations(self):
        """Devuelve las relaciones en formato de diccionario (para compatibilidad)"""
        return {
            'direct': self.direct,
            'causality': self.causality,
            'parallel': self.parallel,
            'decision': self.decision,
            'activities': self.activities
        }
    
    def compute_places(self):
        """Calcula las plazas (lugares) basadas en pares máximos de relaciones causales"""
        activities = self.activities
        
        # Generar todos los posibles conjuntos de entrada (A) válidos
        candidate_A = []
        for r in range(1, len(activities)+1):
            for subset in combinations(activities, r):
                subset_set = set(subset)
                # Verificar si todos los elementos en A están en decisión (o son el mismo)
                valid = True
                for a1 in subset_set:
                    for a2 in subset_set:
                        if a1 != a2 and (a1, a2) not in self.decision:
                            valid = False
                            break
                    if not valid:
                        break
                if valid:
                    candidate_A.append(subset_set)
        
        # Generar todos los posibles conjuntos de salida (B) válidos
        candidate_B = []
        for r in range(1, len(activities)+1):
            for subset in combinations(activities, r):
                subset_set = set(subset)
                valid = True
                for b1 in subset_set:
                    for b2 in subset_set:
                        if b1 != b2 and (b1, b2) not in self.decision:
                            valid = False
                            break
                    if not valid:
                        break
                if valid:
                    candidate_B.append(subset_set)
        
        # Encontrar todos los pares (A, B) válidos
        valid_pairs = []
        for A in candidate_A:
            for B in candidate_B:
                # Verificar causalidad entre todos los elementos de A y B
                causal_valid = True
                for a in A:
                    for b in B:
                        if (a, b) not in self.causality:
                            causal_valid = False
                            break
                    if not causal_valid:
                        break
                if causal_valid:
                    valid_pairs.append((A, B))
        
        # Filtrar para quedarse solo con los pares máximos
        maximal_pairs = []
        for pair in valid_pairs:
            A, B = pair
            is_maximal = True
            for other_pair in valid_pairs:
                if pair == other_pair:
                    continue
                other_A, other_B = other_pair
                if A.issubset(other_A) and B.issubset(other_B):
                    is_maximal = False
                    break
            if is_maximal:
                maximal_pairs.append((A, B))
        
        # Almacenar las plazas
        self.places = maximal_pairs
        return self

    def print_places(self):
        """Imprime las plazas calculadas"""
        if not hasattr(self, 'places'):
            self.compute_places()
        
        print("\nPLACES (Conjuntos de entrada → Conjuntos de salida):")
        for idx, (A, B) in enumerate(self.places, 1):
            A_str = ", ".join(sorted(A))
            B_str = ", ".join(sorted(B))
            print(f"P{idx}: {{ {A_str} }} → {{ {B_str} }}")
        return self

