from itertools import combinations, product
import pandas as pd
import re

class Alpha:
    def __init__(self):
        self.event_log = []
        self.direct_successions = {}
        self.causal_relations = set()
        self.concurrent_relations = set()
        self.choice_relations = set()
        self.activity_set = []
        self.places = []
        self.entry_tasks = []
        self.exit_tasks = []
        # Conjuntos para el algoritmo Alpha
        self.pattern_pairs = []
        self.maximal_patterns = []
        self.place_labels = []
        self.flow_relations = []
        
    def parse_event_log(self, log_string):
        """Analiza un log de eventos en formato de texto"""
        self.event_log = []
        log_string = log_string.strip()
        
        # Quitar corchetes exteriores si existen
        if log_string.startswith('[') and log_string.endswith(']'):
            log_string = log_string[1:-1]
        
        # Encontrar todas las trazas usando expresiones regulares
        trace_pattern = re.compile(r'<[^>]*>')
        trace_matches = trace_pattern.findall(log_string)
        
        for trace_str in trace_matches:
            # Extraer repeticiones (formato: <...>^n)
            multiplier = 1
            if '^' in trace_str:
                trace_part, multiplier_part = trace_str.rsplit('^', 1)
                multiplier = int(multiplier_part.strip())
                trace_str = trace_part.strip()
            
            # Extraer actividades de la traza
            activities = trace_str.strip('<>').replace(' ', '').split(',')
            activities = [act for act in activities if act]
            
            # Añadir la traza el número de veces indicado
            self.event_log.extend([activities] * multiplier)
        
        return self

    def discover_relations(self):
        """Descubre las relaciones entre actividades en el log"""
        # Extraer conjunto de actividades únicas y ordenadas
        self.activity_set = sorted({act for trace in self.event_log for act in trace})
        self.direct_successions = {}

        # Calcular sucesiones directas
        for trace in self.event_log:
            for i in range(len(trace) - 1):
                pair = (trace[i], trace[i + 1])
                self.direct_successions[pair] = self.direct_successions.get(pair, 0) + 1

        # Inicializar conjuntos de relaciones
        self.causal_relations = set()
        self.concurrent_relations = set()
        self.choice_relations = set()

        # Analizar todos los pares posibles de actividades
        for a, b in product(self.activity_set, self.activity_set):
            if a == b:
                self.choice_relations.add((a, b))  # Reflexivas
                continue

            ab_count = self.direct_successions.get((a, b), 0)
            ba_count = self.direct_successions.get((b, a), 0)

            if ab_count > 0 and ba_count == 0:  # a → b pero no b → a
                self.causal_relations.add((a, b))
            elif ab_count > 0 and ba_count > 0:  # a → b y b → a
                self.concurrent_relations.add((a, b))
            elif ab_count == 0 and ba_count == 0:  # No sucesión directa
                self.choice_relations.add((a, b))
        
        # Identificar tareas de entrada y salida
        self._identify_boundary_tasks()

        return self
        
    def _identify_boundary_tasks(self):
        """Identifica las tareas de entrada y salida en el proceso"""
        all_tasks = set(self.activity_set)
        
        # Tareas con alguna entrada (aparecen como destino en relaciones causales)
        tasks_with_input = {b for _, b in self.causal_relations}
        
        # Tareas con alguna salida (aparecen como origen en relaciones causales)
        tasks_with_output = {a for a, _ in self.causal_relations}
        
        # Las tareas de entrada son las que no tienen ninguna entrada
        self.entry_tasks = sorted(all_tasks - tasks_with_input)
        
        # Las tareas de salida son las que no tienen ninguna salida
        self.exit_tasks = sorted(all_tasks - tasks_with_output)
        
        return self
    
    def create_footprint_matrix(self):
        """Crea la matriz de huella del proceso"""
        matrix = pd.DataFrame('', index=self.activity_set, columns=self.activity_set)
        
        # Rellenar la matriz según los tipos de relaciones
        for a, b in self.causal_relations:
            matrix.loc[a, b] = '->'
            matrix.loc[b, a] = '<-'
            
        for a, b in self.concurrent_relations:
            matrix.loc[a, b] = '||'
            matrix.loc[b, a] = '||'
            
        for a, b in self.choice_relations:
            matrix.loc[a, b] = '#'
        
        return matrix

    def find_multiple_arrows_in_row(self, row, matrix):
        """Encuentra múltiples flechas salientes de una fila"""
        targets = [col for col in self.activity_set if matrix.loc[row, col] == '->']
        return (row, targets) if len(targets) > 1 else None
    
    def find_multiple_arrows_in_column(self, column, matrix):
        """Encuentra múltiples flechas entrantes a una columna"""
        sources = [row for row in self.activity_set if matrix.loc[row, column] == '->']
        return (sources, column) if len(sources) > 1 else None
    
    def determine_pattern_type(self, pattern):
        """Determina si el patrón es de tipo Choice (#) o Paralelo (||)"""
        # Para patrones con entrada múltiple: (a,b) → c
        if isinstance(pattern[0], tuple):
            a, b = pattern[0]
            if (a, b) in self.choice_relations or (b, a) in self.choice_relations:
                return '#'
            if (a, b) in self.concurrent_relations or (b, a) in self.concurrent_relations:
                return '||'
        # Para patrones con salida múltiple: a → (b,c)
        else:
            b, c = pattern[1]
            if (b, c) in self.choice_relations or (c, b) in self.choice_relations:
                return '#'
            if (b, c) in self.concurrent_relations or (c, b) in self.concurrent_relations:
                return '||'
        return None
    
    def has_opposite_parallel_pattern(self, elements, patterns, position):
        """Verifica si existe un patrón paralelo opuesto"""
        for pattern in patterns:
            if elements[0] in pattern[position] or elements[1] in pattern[position]:
                if self.determine_pattern_type(pattern) == '#':
                    return False
        return True
    
    def has_hash_in_complement(self, element, complements, position):
        """Verifica si hay un patrón de elección en el complemento"""
        for comp in complements:
            if element in comp[position]:
                if self.determine_pattern_type(comp) == '#':
                    return True
        return False

    def filter_valid_patterns(self, row_patterns, col_patterns):
        """Filtra los patrones válidos según reglas del algoritmo Alpha"""
        valid_patterns = []
        
        # Procesar patrones de fila
        for pattern in row_patterns:
            pattern_type = self.determine_pattern_type(pattern)
            if pattern_type == '#':
                valid_patterns.append(pattern)
            elif pattern_type == '||':
                if (self.has_opposite_parallel_pattern(pattern[1], col_patterns, 1) and 
                    not self.has_hash_in_complement(pattern[0], row_patterns, 0)):
                    valid_patterns.append(pattern)
        
        # Procesar patrones de columna
        for pattern in col_patterns:
            pattern_type = self.determine_pattern_type(pattern)
            if pattern_type == '#':
                valid_patterns.append(pattern)
            elif pattern_type == '||':
                if (self.has_opposite_parallel_pattern(pattern[0], row_patterns, 0) and 
                    not self.has_hash_in_complement(pattern[1], col_patterns, 1)):
                    valid_patterns.append(pattern)
        
        return valid_patterns
    
    def expand_row_patterns(self, row_patterns):
        """Expande patrones de fila complejos en pares de actividades"""
        expanded_patterns = []
        
        for source, targets in row_patterns:
            if len(targets) > 2:  # Si hay más de dos objetivos
                # Crear todas las combinaciones posibles de pares de objetivos
                for i, j in combinations(targets, 2):
                    expanded_patterns.append((source, (i, j)))
            else:
                # Si solo hay dos objetivos, mantener como está
                expanded_patterns.append((source, tuple(targets)))
        
        return expanded_patterns
    
    def expand_column_patterns(self, col_patterns):
        """Expande patrones de columna complejos en pares de actividades"""
        expanded_patterns = []
        
        for sources, target in col_patterns:
            if len(sources) > 2:  # Si hay más de dos fuentes
                # Crear todas las combinaciones posibles de pares de fuentes
                for i, j in combinations(sources, 2):
                    expanded_patterns.append(((i, j), target))
            else:
                # Si solo hay dos fuentes, mantener como está
                expanded_patterns.append((tuple(sources), target))
        
        return expanded_patterns
    
    def discover_complex_patterns(self):
        """Identifica patrones complejos en la matriz de huella"""
        matrix = self.create_footprint_matrix()
        row_patterns = []
        col_patterns = []
        
        # Buscar patrones en filas y columnas
        for activity in self.activity_set:
            row_result = self.find_multiple_arrows_in_row(activity, matrix)
            if row_result:
                row_patterns.append(row_result)
                
            col_result = self.find_multiple_arrows_in_column(activity, matrix)
            if col_result:
                col_patterns.append(col_result)
        
        # Expandir patrones complejos a pares
        expanded_rows = self.expand_row_patterns(row_patterns)
        expanded_cols = self.expand_column_patterns(col_patterns)
        
        # Filtrar patrones válidos
        valid_patterns = self.filter_valid_patterns(expanded_rows, expanded_cols)
        
        return valid_patterns
    
    def remove_simple_patterns(self, patterns):
        """Elimina patrones simples que están incluidos en patrones complejos"""
        survivors = []
        
        for i, pattern_i in enumerate(patterns):
            is_valid = True
            
            for j, pattern_j in enumerate(patterns):
                if i == j:  # No comparar con sí mismo
                    continue
                    
                # Verificar si pattern_i está incluido en pattern_j
                if isinstance(pattern_j[0], tuple):
                    if (pattern_i == (pattern_j[0][0], pattern_j[1]) or 
                        pattern_i == (pattern_j[0][1], pattern_j[1])):
                        is_valid = False
                        break
                
                if isinstance(pattern_j[1], tuple):
                    if (pattern_i == (pattern_j[0], pattern_j[1][0]) or 
                        pattern_i == (pattern_j[0], pattern_j[1][1])):
                        is_valid = False
                        break
            
            if is_valid:
                survivors.append(pattern_i)
        
        return survivors
    
    def format_place_label(self, pattern):
        """Formatea un patrón como etiqueta legible de lugar"""
        if isinstance(pattern[0], tuple):
            return f"P({{{pattern[0][0]},{pattern[0][1]}}},{{{pattern[1]}}})"
        elif isinstance(pattern[1], tuple):
            return f"P({{{pattern[0]}}},{{{pattern[1][0]},{pattern[1][1]}}})"
        return f"P({{{pattern[0]}}},{{{pattern[1]}}})"
    
    def generate_pattern_pairs(self):
        # Iniciar con las relaciones causales directas
        self.pattern_pairs = list(self.causal_relations)
        
        # Agregar los patrones complejos
        self.pattern_pairs += self.discover_complex_patterns()
        
        return self
    
    def generate_maximal_patterns(self):
        self.maximal_patterns = self.remove_simple_patterns(self.pattern_pairs)
        return self
    
    def generate_place_labels(self):
        # Convertir patrones a lugares formalizados
        self.places = []
        
        # Procesar cada patrón maximal
        for pattern in self.maximal_patterns:
            # Determinar actividades de entrada
            if isinstance(pattern[0], tuple):
                input_set = set(pattern[0])
            else:
                input_set = {pattern[0]}
                
            # Determinar actividades de salida
            if isinstance(pattern[1], tuple):
                output_set = set(pattern[1])
            else:
                output_set = {pattern[1]}
            
            # Guardar el lugar como un par (entradas, salidas)
            self.places.append((input_set, output_set))
        
        # Añadir lugar inicial y final
        initial_place = ({"Il"}, set(self.entry_tasks))
        final_place = (set(self.exit_tasks), {"Ol"})
        
        self.places.append(initial_place)
        self.places.append(final_place)
        
        # Generar etiquetas para visualización
        self.place_labels = [self.format_place_label(pattern) for pattern in self.maximal_patterns]
        self.place_labels.extend(["Il", "Ol"])
        
        return self
    
    def generate_flow_relations(self):
        self.flow_relations = []
        
        # Generar flujos entre lugares y actividades
        for idx, (inputs, outputs) in enumerate(self.places):
            place_id = f"p{idx}"
            
            # Conexiones de entrada al lugar
            for input_act in inputs:
                if input_act != "Il":  # Ignorar la fuente lógica
                    self.flow_relations.append((input_act, place_id))
            
            # Conexiones de salida del lugar
            for output_act in outputs:
                if output_act != "Ol":  # Ignorar el sumidero lógico
                    self.flow_relations.append((place_id, output_act))
        
        return self
    
    def execute_alpha_algorithm(self):
        self.generate_pattern_pairs()
        self.generate_maximal_patterns()
        self.generate_place_labels()
        self.generate_flow_relations()
        self.places = [(sorted(list(inputs)), sorted(list(outputs))) for inputs, outputs in self.places]
        
        return self
    
    def visualize_petri_net(self):
        """Genera una visualización de la red de Petri completa usando NetworkX"""
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
        except ImportError:
            print("Error: Las bibliotecas NetworkX y/o Matplotlib no están instaladas.")
            print("Instálalas con 'pip install networkx matplotlib'.")
            return None
        
        # Crear un grafo dirigido
        G = nx.DiGraph()
        
        # Preparar nodos de actividades y lugares
        activity_nodes = self.activity_set
        place_nodes = [f"p{idx}" for idx in range(len(self.places))]
        
        # Lista para almacenar aristas con etiquetas
        edges = []
        
        # Añadir las relaciones de flujo
        for src, dst in self.flow_relations:
            edges.append((src, dst, f"{src}→{dst}"))
        
        # Agregar aristas al grafo
        G.add_edges_from([(u, v) for u, v, _ in edges])
        
        # Posicionar los nodos
        pos = nx.spring_layout(G, seed=42)  # Usar una semilla fija para reproducibilidad
        
        # Crear una nueva figura y ejes
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Dibujar nodos de lugar (círculos)
        nx.draw_networkx_nodes(G, pos, nodelist=place_nodes, 
                               node_shape='o', node_color='lightblue', 
                               node_size=800, alpha=0.8, ax=ax)
        
        # Dibujar nodos de actividad (cuadrados)
        nx.draw_networkx_nodes(G, pos, nodelist=activity_nodes, 
                               node_shape='s', node_color='lightgreen', 
                               node_size=600, alpha=0.8, ax=ax)
        
        # Dibujar aristas con flechas
        nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=15, 
                               edge_color="black", width=1.0, ax=ax)
        
        # Dibujar etiquetas de nodos con tamaño adecuado
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)
        
        # Crear etiquetas de aristas
        edge_labels = {(u, v): label for u, v, label in edges}
        
        # Dibujar etiquetas de las aristas
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                    font_size=8, font_color="red", ax=ax)
        
        ax.set_title("Red de Petri - Algoritmo Alpha")
        ax.axis('off')  # Ocultar ejes
        
        plt.tight_layout()
        return fig
    
    def visualize_places(self):
        """Genera una visualización de los lugares en la red de Petri usando NetworkX"""
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
        except ImportError:
            print("Error: Las bibliotecas NetworkX y/o Matplotlib no están instaladas.")
            print("Instálalas con 'pip install networkx matplotlib'.")
            return None
        
        # Crear un grafo dirigido
        G = nx.DiGraph()
        
        # Lista para nodos y etiquetas
        nodes = []
        node_labels = {}
        
        # Añadir lugares como nodos
        for idx, (inputs, outputs) in enumerate(self.places):
            place_id = f"p{idx}"
            nodes.append(place_id)
            inputs_str = ", ".join(sorted(inputs))
            outputs_str = ", ".join(sorted(outputs))
            node_labels[place_id] = f"p{idx}: {{{inputs_str}}} → {{{outputs_str}}}"
        
        # Lista para almacenar aristas con etiquetas
        edges = []
        
        # Determinar conexiones entre lugares basados en actividades comunes
        for i, (_, outputs_i) in enumerate(self.places):
            for j, (inputs_j, _) in enumerate(self.places):
                if i != j:
                    common_activities = set(outputs_i).intersection(set(inputs_j))
                    if common_activities:
                        edges.append((f"p{i}", f"p{j}", ", ".join(sorted(common_activities))))
        
        # Agregar aristas al grafo
        G.add_edges_from([(u, v) for u, v, _ in edges])
        G.add_nodes_from(nodes)
        
        # Posicionar los nodos
        pos = nx.spring_layout(G, seed=42)  # Usar una semilla fija para reproducibilidad
        
        # Crear una nueva figura y ejes
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Dibujar nodos
        nx.draw_networkx_nodes(G, pos, nodelist=nodes, 
                               node_shape='o', node_color='lightblue', 
                               node_size=2500, alpha=0.8, ax=ax)
        
        # Dibujar aristas con flechas
        nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=15, 
                               edge_color="black", width=1.0, ax=ax)
        
        # Dibujar etiquetas de nodos personalizadas (más pequeñas para caber en el gráfico)
        for node, label in node_labels.items():
            x, y = pos[node]
            ax.text(x, y, label, fontsize=8, ha='center', va='center', 
                     bbox=dict(facecolor='white', alpha=0.7, boxstyle='round'))
        
        # Crear etiquetas de aristas
        edge_labels = {(u, v): label for u, v, label in edges}
        
        # Dibujar etiquetas de las aristas
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                    font_size=8, font_color="red", ax=ax)
        
        ax.set_title("Lugares identificados - Algoritmo Alpha")
        ax.axis('off')  # Ocultar ejes
        
        plt.tight_layout()
        return fig

if __name__ == "__main__":
    # Ejemplo de uso de ProcessMiner
    print("=== DEMOSTRACIÓN DE PROCESS MINER ===")
    
    # Crear instancia del minero de procesos
    miner = Alpha()
    
    # Ejemplo de log de eventos
    log_ejemplo = "[<a,b,c,d>^3, <a,c,b,d>^2, <a,e,d>^1]"
    print(f"Log de eventos de entrada: {log_ejemplo}\n")
    
    # Ejecutar el algoritmo completo
    miner.parse_event_log(log_ejemplo).discover_relations().execute_alpha_algorithm()
    
    # Mostrar resultados principales
    print(f"Actividades descubiertas: {miner.activity_set}")
    print(f"Tareas de entrada: {miner.entry_tasks}")
    print(f"Tareas de salida: {miner.exit_tasks}")
    
    # Mostrar matriz de huella
    print("\nMatriz de huella del proceso:")
    print(miner.create_footprint_matrix())
    
    # Mostrar lugares descubiertos
    print("\nLugares en la red de Petri:")
    for idx, (inputs, outputs) in enumerate(miner.places):
        inputs_str = ", ".join(sorted(inputs))
        outputs_str = ", ".join(sorted(outputs))
        print(f"p{idx}: {{{inputs_str}}} → {{{outputs_str}}}")