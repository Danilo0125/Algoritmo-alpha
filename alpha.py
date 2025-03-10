from itertools import combinations
import pandas as pd

class Alpha:
    def __init__(self):
        self.trazas = []
        self.directas = {}
        self.causalidad = set()
        self.paralelo = set()
        self.decision = set()
        self.actividades = []
        self.lugares = []
        self.tareas_iniciales = []
        self.tareas_finales = []
        # Nuevos atributos para el algoritmo de 8 pasos
        self.xl = []
        self.yl = []
        self.pl = []
        self.fl = []
        
    def analizar_log(self, cadena_log):
        """Convierte una cadena de log en lista de trazas"""
        self.trazas = []
        
        # Limpiar los corchetes externos si existen
        cadena_log = cadena_log.strip()
        if cadena_log.startswith('[') and cadena_log.endswith(']'):
            cadena_log = cadena_log[1:-1]
        
        # Dividir por patrones de traza "<...>"
        import re
        patron_traza = re.compile(r'<[^>]*>')
        coincidencias_traza = patron_traza.findall(cadena_log)
        
        for cadena_traza in coincidencias_traza:
            # Extraer multiplicador si existe (formato: <...>^n)
            if '^' in cadena_traza:
                parte_traza, parte_contador = cadena_traza.rsplit('^', 1)
                contador = int(parte_contador.strip())
                parte_traza = parte_traza.strip()
            else:
                parte_traza = cadena_traza
                contador = 1
            
            # Limpiar y dividir la traza
            traza = parte_traza.strip('<>').replace(' ', '').split(',')
            # Eliminar elementos vacíos (por ejemplo, de "d,,e" → ['d', '', 'e'] → ['d', 'e'])
            traza = [act for act in traza if act]
            
            # Añadir la traza el número de veces indicado
            self.trazas.extend([traza] * contador)
        
        return self

    def calcular_relaciones(self):
        """Calcula todas las relaciones entre actividades"""
        self.actividades = sorted({act for traza in self.trazas for act in traza})
        self.directas = {}

        # Sucesiones directas
        for traza in self.trazas:
            for i in range(len(traza) - 1):
                par = (traza[i], traza[i + 1])
                self.directas[par] = self.directas.get(par, 0) + 1

        # Inicializar relaciones
        self.causalidad = set()
        self.paralelo = set()
        self.decision = set()

        # Comparar todos los pares posibles
        for x in self.actividades:
            for y in self.actividades:
                if x == y:
                    self.decision.add((x, y))  # Relaciones reflexivas
                    continue

                xy = self.directas.get((x, y), 0)
                yx = self.directas.get((y, x), 0)

                if xy > 0 and yx == 0:
                    self.causalidad.add((x, y))
                elif xy > 0 and yx > 0:
                    self.paralelo.add((x, y))
                elif xy == 0 and yx == 0:
                    self.decision.add((x, y))
        
        # Identificar tareas iniciales y finales
        self._identificar_tareas_iniciales_finales()

        return self  # Permite encadenamiento de métodos
        
    def _identificar_tareas_iniciales_finales(self):
        """Identifica las tareas iniciales y finales en el log"""
        todas_las_tareas = set(self.actividades)
        tareas_con_entrada = {y for x, y in self.causalidad}
        tareas_con_salida = {x for x, y in self.causalidad}
        
        # Tareas iniciales: las que no tienen entrada
        self.tareas_iniciales = sorted(todas_las_tareas - tareas_con_entrada)
        # Tareas finales: las que no tienen salida
        self.tareas_finales = sorted(todas_las_tareas - tareas_con_salida)
        
        return self

    def procesar_log(self, cadena_log):
        """Procesa un log completo: parsea y calcula las relaciones en un solo paso"""
        return self.analizar_log(cadena_log).calcular_relaciones()

    def imprimir_resultados(self):
        """Muestra los resultados formateados con conteos finales (actualmente deshabilitado)"""
        # Contar relaciones únicas (incluyendo reflexivas en decisiones)
        total_directas = len(self.directas)
        total_causalidad = len(self.causalidad)
        total_paralelo = len(self.paralelo)
        total_decision = len(self.decision)

        # Print statements removed
        
        return self  # Permite encadenamiento de métodos
    def maximizar_pares(self, Xl, Tl):
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

    def obtener_relaciones(self):
        """Devuelve las relaciones en formato de diccionario (para compatibilidad)"""
        return {
            'directas': self.directas,
            'causalidad': self.causalidad,
            'paralelo': self.paralelo,
            'decision': self.decision,
            'actividades': self.actividades
        }
    
    def calcular_lugares(self):
        """Calcula los lugares (plazas) considerando paralelismos y maximalidad."""
        actividades = self.actividades
        
        # Generar conjuntos de entrada (A) válidos: paralelos o en decisión
        candidatos_A = []
        for r in range(1, len(actividades)+1):
            for subset in combinations(actividades, r):
                conjunto_subset = set(subset)
                valido = True
                for a1, a2 in combinations(conjunto_subset, 2):
                    if (a1, a2) not in self.decision and (a1, a2) not in self.paralelo:
                        valido = False
                        break
                if valido:
                    candidatos_A.append(frozenset(conjunto_subset))  # Usar frozenset para evitar duplicados
        
        # Generar conjuntos de salida (B) válidos: misma lógica que A
        candidatos_B = []
        for r in range(1, len(actividades)+1):
            for subset in combinations(actividades, r):
                conjunto_subset = set(subset)
                valido = True
                for b1, b2 in combinations(conjunto_subset, 2):
                    if (b1, b2) not in self.decision and (b1, b2) not in self.paralelo:
                        valido = False
                        break
                if valido:
                    candidatos_B.append(frozenset(conjunto_subset))
        
        # Encontrar pares (A, B) donde todas las actividades en A causan las de B
        pares_validos = []
        for A in candidatos_A:
            for B in candidatos_B:
                causal_valido = True
                for a in A:
                    for b in B:
                        if (a, b) not in self.causalidad:
                            causal_valido = False
                            break
                    if not causal_valido:
                        break
                if causal_valido:
                    pares_validos.append((A, B))
        
        # Filtrar pares máximos: eliminar los cubiertos por otros
        pares_maximos = []
        for par in pares_validos:
            A, B = par
            es_maximal = True
            for otro_par in pares_validos:
                otro_A, otro_B = otro_par
                if A.issubset(otro_A) and B.issubset(otro_B) and par != otro_par:
                    es_maximal = False
                    break
            if es_maximal:
                pares_maximos.append((A, B))
        
        # Eliminar duplicados y almacenar
        self.lugares = list({(tuple(sorted(A)), tuple(sorted(B))) for A, B in pares_maximos})
        return self

    def imprimir_lugares(self):
        """Imprime los lugares (plazas) en formato legible (actualmente deshabilitado)"""
        if not hasattr(self, 'lugares'):
            self.calcular_lugares()
        
        # Print statements removed
        return self

    def hay_flechas_repetidas_fila(self, fila, matriz):
        """Verifica si hay flechas repetidas en una fila"""
        repetidos = []
        for col in self.actividades:
            if matriz.loc[fila, col] == '->':
                repetidos.append(col)
        
        if len(repetidos) > 1:
            return (fila, repetidos)
        return None
    
    def hay_flechas_repetidas_columna(self, columna, matriz):
        """Verifica si hay flechas repetidas en una columna"""
        repetidos = []
        for fila in self.actividades:
            if matriz.loc[fila, columna] == '->':
                repetidos.append(fila)
        
        if len(repetidos) > 1:
            return (repetidos, columna)
        return None
    
    def construir_matriz_huella_pandas(self):
        """Construye la matriz de huella como DataFrame de pandas"""
        matriz = pd.DataFrame('', index=self.actividades, columns=self.actividades)
        
        # Llenar con símbolos
        for x, y in self.causalidad:
            matriz.loc[x, y] = '->'
            matriz.loc[y, x] = '<-'
            
        for x, y in self.paralelo:
            matriz.loc[x, y] = '||'
            matriz.loc[y, x] = '||'
            
        for x, y in self.decision:
            matriz.loc[x, y] = '#'
        
        return matriz
    
    def tablita_ideas(self, x):
        """Determina el tipo de unión o división basado en los valores de la matriz"""
        if isinstance(x[0], tuple):
            if (x[0][0], x[0][1]) in self.decision or (x[0][1], x[0][0]) in self.decision:
                return '#'
            elif (x[0][0], x[0][1]) in self.paralelo or (x[0][1], x[0][0]) in self.paralelo:
                return '||'
        else:
            if (x[1][0], x[1][1]) in self.decision or (x[1][1], x[1][0]) in self.decision:
                return '#'
            elif (x[1][0], x[1][1]) in self.paralelo or (x[1][1], x[1][0]) in self.paralelo:
                return '||'
        return None
    
    def su_contrario_tiene_paralelos(self, letras, lista, posicion):
        """Verifica si el contrario tiene paralelos"""
        for i in lista:
            if (letras[0] in i[posicion] or letras[1] in i[posicion]):
                if (self.tablita_ideas(i) == '#'):
                    return False
        return True
    
    def su_complemento_tiene_hashtag(self, letra, complemento, posicion):
        """Verifica si el complemento tiene un hashtag"""
        for i in complemento:
            if (letra in i[posicion]):
                if (self.tablita_ideas(i) == '#'):
                    return True
        return False

    def validos(self, filas, columnas):
        """Determina filas y columnas válidas basado en el tipo de unión o división"""
        validas = []
        for i in filas:
            resul = self.tablita_ideas(i)
            if resul == '#':
                validas.append(i)
            elif resul == '||':
                if (self.su_contrario_tiene_paralelos(i[1], columnas, 1) and 
                    not self.su_complemento_tiene_hashtag(i[0], filas, 0)):
                    validas.append(i)
                    
        for i in columnas:
            resul = self.tablita_ideas(i)
            if resul == '#':
                validas.append(i)
            elif resul == '||':
                if (self.su_contrario_tiene_paralelos(i[0], filas, 0) and 
                    not self.su_complemento_tiene_hashtag(i[1], columnas, 1)):
                    validas.append(i)
                    
        return validas
    
    def descomponer_fila(self, r_filas):
        """Descompone filas complejas en filas más simples"""
        aux = []
        for i in range(len(r_filas)):
            tam = len(r_filas[i][1])
            if tam > 2:
                for j in range(tam - 1):
                    for k in range(j + 1, tam):
                        resultado = (r_filas[i][0], (r_filas[i][1][j], r_filas[i][1][k]))
                        aux.append(resultado)
            else:
                aux.append((r_filas[i][0], tuple(r_filas[i][1])))
                              
        return aux
    
    def decomponer_columna(self, r_columnas):
        """Descompone columnas complejas en columnas más simples"""
        aux = []
        for i in range(len(r_columnas)):
            tam = len(r_columnas[i][0])
            if tam > 2:
                for j in range(tam - 1):
                    for k in range(j + 1, tam):
                        resultado = ((r_columnas[i][0][j], r_columnas[i][0][k]), r_columnas[i][1])
                        aux.append(resultado)
            else:
                aux.append((tuple(r_columnas[i][0]), r_columnas[i][1]))
                              
        return aux
    
    def sacar_complejos(self):
        """Identifica y descompone filas y columnas complejas"""
        r_filas = []
        r_columnas = []
        matriz = self.construir_matriz_huella_pandas()
        
        for l in self.actividades:
            if self.hay_flechas_repetidas_fila(l, matriz) is not None:
                r_filas.append(self.hay_flechas_repetidas_fila(l, matriz)) 
            if self.hay_flechas_repetidas_columna(l, matriz) is not None:
                r_columnas.append(self.hay_flechas_repetidas_columna(l, matriz))
        
        r_filas = self.descomponer_fila(r_filas)
        r_columnas = self.decomponer_columna(r_columnas)
        
        validos = self.validos(r_filas, r_columnas)
        
        return validos
    
    def comer_simples(self, xl):
        """Elimina conexiones simples de XL"""
        sobrevivientes = []
        for i in range(len(xl)):
            es_valido = True
            for j in range(len(xl)):
                if i == j:
                    continue
                if ((isinstance(xl[j][0], tuple) and 
                     (xl[i] == (xl[j][0][0], xl[j][1]) or xl[i] == (xl[j][0][1], xl[j][1]))) or 
                    (isinstance(xl[j][1], tuple) and 
                     (xl[i] == (xl[j][0], xl[j][1][0]) or xl[i] == (xl[j][0], xl[j][1][1])))):
                    es_valido = False
                    break
            if es_valido:
                sobrevivientes.append(xl[i])
                
        return sobrevivientes
    
    def pretty(self, a):
        """Convierte una conexión a un formato de cadena legible"""
        if isinstance(a[0], tuple):
            return f"P({{{a[0][0]},{a[0][1]}}},{{{a[1]}}})"
        elif isinstance(a[1], tuple):
            return f"P({{{a[0]}}},{{{a[1][0]},{a[1][1]}}})"
        return f"P({{{a[0]}}},{{{a[1]}}})"
    
    def convertir_string_yl(self, yl):
        """Convierte YL a una lista de cadenas legibles"""
        pl = []
        for i in yl:
            pl.append(self.pretty(i))
        return pl

    def generar_xl(self):
        """Paso 4: Genera el conjunto XL siguiendo la lógica de Algoritmo_Alpha"""
        # XL contiene todas las conexiones causales directas
        self.xl = list(self.causalidad)
        # Agregar patrones complejos identificados
        self.xl += self.sacar_complejos()
        return self
    
    def generar_yl(self):
        """Paso 5: Genera el conjunto YL (pares máximos) siguiendo la lógica de Algoritmo_Alpha"""
        # YL se obtiene eliminando conexiones simples de XL
        self.yl = self.comer_simples(self.xl)
        return self
    
    def generar_pl(self):
        """Paso 6: Genera el conjunto PL (lugares) siguiendo la lógica de Algoritmo_Alpha"""
        # PL contiene representaciones string de YL más 'iL' y 'oL'
        self.pl = []
        
        # Convertir YL a formato de lugares
        lugares_yl = self.convertir_string_yl(self.yl)
        
        # Crear componentes del lugar (igual que antes pero con formato diferente)
        for item in self.yl:
            if isinstance(item[0], tuple):
                entrada = set(item[0])
            else:
                entrada = {item[0]}
                
            if isinstance(item[1], tuple):
                salida = set(item[1])
            else:
                salida = {item[1]}
                
            self.pl.append((entrada, salida))
            
        # Añadir lugar inicial y final
        lugar_inicial = (set(['iL']), set(self.tareas_iniciales))
        lugar_final = (set(self.tareas_finales), set(['oL']))
        
        self.pl.append(lugar_inicial)
        self.pl.append(lugar_final)
        
        return self

    def generar_fl(self):
        """Paso 7: Genera el conjunto FL (flujos)"""
        self.fl = []
        
        # Generar flujos entre lugares y actividades
        for idx, lugar in enumerate(self.pl):
            entradas, salidas = lugar
            
            # Para cada actividad de entrada al lugar
            for entrada in entradas:
                if entrada != 'iL':  # Ignorar el inicio lógico
                    self.fl.append((entrada, f"p{idx}"))
            
            # Para cada actividad de salida del lugar
            for salida in salidas:
                if salida != 'oL':  # Ignorar el fin lógico
                    self.fl.append((f"p{idx}", salida))
        
        return self
    
    def ejecutar_ocho_pasos(self):
        """Ejecuta los 8 pasos del algoritmo Alpha (sin impresiones)"""
        # Paso 1: Ya tenemos identificadas las actividades
        
        # Paso 2 y 3: Identificar tareas iniciales y finales
        
        # Paso 4: Generar XL
        self.generar_xl()
        
        # Paso 5: Generar YL
        self.generar_yl()
        
        # Paso 6: Generar PL
        self.generar_pl()
        
        # Paso 7: Generar FL
        self.generar_fl()
        
        # Paso 8: Generar la red de Petri (renderización)
        
        # Actualizar lugares para compatibilidad
        self.lugares = [(sorted(list(entradas)), sorted(list(salidas))) for entradas, salidas in self.pl]
        
        return self
        
    def imprimir_todo(self):
        """Imprime todos los resultados del análisis"""
        print("\n=== ANÁLISIS COMPLETO DEL REGISTRO DE EVENTOS ===")
        
        print("\n1. TRAZAS IDENTIFICADAS:")
        for i, traza in enumerate(self.trazas, 1):
            print(f"  Traza {i}: {traza}")
        
        print("\n2. ACTIVIDADES:")
        print(f"  Total: {len(self.actividades)}")
        print(f"  Elementos: {', '.join(self.actividades)}")
        
        print("\n3. TAREAS INICIALES Y FINALES:")
        print(f"  Iniciales: {', '.join(self.tareas_iniciales)}")
        print(f"  Finales: {', '.join(self.tareas_finales)}")
        
        print("\n4. RELACIONES DIRECTAS:")
        for (x, y), contador in sorted(self.directas.items()):
            print(f"  {x} > {y} ({contador} veces)")
            
        print("\n5. RELACIONES DE CAUSALIDAD:")
        for x, y in sorted(self.causalidad):
            print(f"  {x} → {y}")
            
        print("\n6. RELACIONES DE PARALELISMO:")
        for x, y in sorted(self.paralelo):
            print(f"  {x} || {y}")
            
        print("\n7. RELACIONES DE DECISIÓN:")
        for x, y in sorted(self.decision):
            print(f"  {x} # {y}")
            
        print("\n8. MATRIZ DE HUELLA (FOOTPRINT):")
        matriz = self.construir_matriz_huella_pandas()
        print(matriz)
        
        # Si se ha ejecutado el algoritmo Alpha completo
        if hasattr(self, 'xl') and self.xl:
            print("\n9. RESULTADOS ALGORITMO ALPHA (8 PASOS):")
            print("\n   a. XL (conexiones):")
            for item in self.xl:
                print(f"      {item}")
                
            print("\n   b. YL (pares máximos):")
            for item in self.yl:
                print(f"      {item}")
                
            print("\n   c. PL (lugares):")
            for idx, lugar in enumerate(self.pl):
                entradas = ", ".join(sorted(lugar[0]))
                salidas = ", ".join(sorted(lugar[1]))
                print(f"      p{idx}: {{{entradas}}} → {{{salidas}}}")
                
            print("\n   d. FL (flujos):")
            for origen, destino in self.fl:
                print(f"      {origen} → {destino}")
                
        print("\n=== FIN DEL ANÁLISIS ===\n")
        return self

if __name__ == "__main__":
    # Ejemplo de uso del algoritmo Alpha
    print("=== EJEMPLO DE USO DEL ALGORITMO ALPHA ===")
    
    # Crear una instancia del algoritmo
    alpha = Alpha()
    
    # Ejemplo de log de eventos
    log_ejemplo = "[<a,b,c,d>^3, <a,c,b,d>^2, <a,e,d>^1]"
    print(f"Log de eventos: {log_ejemplo}\n")
    
    # Procesar el log y ejecutar el algoritmo Alpha completo
    alpha.analizar_log(log_ejemplo).calcular_relaciones().ejecutar_ocho_pasos()
    
    # Mostrar resultados completos
    alpha.imprimir_todo()
    
    # Ejemplo de acceso a resultados específicos
    print("=== ACCESO A RESULTADOS ESPECÍFICOS ===")
    print(f"Actividades: {alpha.actividades}")
    print(f"Tareas iniciales: {alpha.tareas_iniciales}")
    print(f"Tareas finales: {alpha.tareas_finales}")
    print(f"Total de lugares: {len(alpha.pl)}")
    
    # Ejemplo de verificación de relaciones específicas
    a, b = 'a', 'b'
    print(f"\nRelación entre '{a}' y '{b}':")
    if (a, b) in alpha.causalidad:
        print(f"  '{a}' causa '{b}'")
    elif (a, b) in alpha.paralelo:
        print(f"  '{a}' es paralelo a '{b}'")
    elif (a, b) in alpha.decision:
        print(f"  '{a}' está en relación de decisión con '{b}'")
    else:
        print(f"  No hay relación directa entre '{a}' y '{b}'")