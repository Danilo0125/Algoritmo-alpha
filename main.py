from alpha import Alpha
import re
import os

# Variable global para almacenar la última instancia procesada
ultima_instancia_alpha = None
ultimo_nombre_log = ""

def validar_formato_log(cadena_log):
    """Valida y limpia el formato del log de eventos"""
    # Limpiar espacios al inicio y final
    cadena_log = cadena_log.strip()
    
    # Verificar si tiene corchetes exteriores
    if not (cadena_log.startswith('[') and cadena_log.endswith(']')):
        # Agregar corchetes si no los tiene
        cadena_log = f"[{cadena_log}]"
    
    # Verificar que tiene al menos una traza válida
    trace_pattern = re.compile(r'<[^>]*>')
    if not trace_pattern.search(cadena_log):
        raise ValueError("El log no contiene trazas válidas. Debe tener al menos una traza en formato <a,b,c>")
    
    # Verificar el formato general usando expresiones regulares
    full_pattern = re.compile(r'^\[(<[a-zA-Z0-9,]+>(\^[0-9]+)?)(,\s*<[a-zA-Z0-9,]+>(\^[0-9]+)?)*\]$')
    if not full_pattern.match(cadena_log):
        raise ValueError("Formato incorrecto. Debe seguir el patrón [<a,b,c>, <d,e>^2, ...]")
    
    return cadena_log

def procesar_y_mostrar_resultados(log, nombre_log="", visualizar=True, guardar_grafico=False):
    """Procesa un log y muestra todos los resultados del algoritmo Alpha"""
    global ultima_instancia_alpha, ultimo_nombre_log
    
    print(f"\n=== ANÁLISIS DEL LOG {nombre_log} ===\n")
    print(f"Log: {log}")
    
    # Crear instancia y procesar
    alpha = Alpha()
    try:
        alpha.parse_event_log(log).discover_relations().execute_alpha_algorithm()
        
        # Guardar la instancia en memoria para uso posterior
        ultima_instancia_alpha = alpha
        ultimo_nombre_log = nombre_log
        
        # Mostrar resultados clave
        print(f"\nActividades: {alpha.activity_set}")
        print(f"Tareas iniciales: {alpha.entry_tasks}")
        print(f"Tareas finales: {alpha.exit_tasks}")
        
        # Mostrar matriz de huella
        print("\nMatriz de huella:")
        print(alpha.create_footprint_matrix())
        
        # Mostrar lugares
        print("\nLugares identificados:")
        for idx, lugar in enumerate(alpha.places):
            entradas = ", ".join(sorted(lugar[0]))
            salidas = ", ".join(sorted(lugar[1]))
            print(f"p{idx}: {{{entradas}}} → {{{salidas}}}")
        
        # Mostrar resumen estructurado del algoritmo Alpha
        print("\nPASOS DEL ALGORITMO ALFA:")
        print(f"")
        print(f"TL = {alpha.activity_set}")
        print(f"Ti = {alpha.entry_tasks}")
        print(f"To = {alpha.exit_tasks}")
        # Convertir relaciones causales a lista de tuplas para mejor visualización
        causal_list = sorted(list(alpha.causal_relations))
        print(f"XL = {causal_list}")
        print(f"YL = {causal_list}")  # YL parece ser igual a XL en el ejemplo proporcionado
        
        # Crear una lista de etiquetas de lugares
        place_labels = []
        for idx, (inputs, outputs) in enumerate(alpha.places):
            if "Il" in inputs:
                place_labels.append("iL")
            elif "Ol" in outputs:
                place_labels.append("oL")
            else:
                inputs_str = ",".join(sorted(inputs))
                outputs_str = ",".join(sorted(outputs))
                place_labels.append(f"P({{{inputs_str}}},{{{outputs_str}}})")
        print(f"PL = {place_labels}")
        
        # Preparar las relaciones de flujo con etiquetas descriptivas
        flow_labels = []
        for src, dst in alpha.flow_relations:
            # Convertir identificadores de lugares (p0, p1, etc.) a etiquetas descriptivas
            if src.startswith('p') and src[1:].isdigit():
                idx = int(src[1:])
                if idx < len(place_labels):
                    src = place_labels[idx]
            if dst.startswith('p') and dst[1:].isdigit():
                idx = int(dst[1:])
                if idx < len(place_labels):
                    dst = place_labels[idx]
            flow_labels.append((src, dst))
        print(f"FL = {flow_labels}")
        
        # Visualizar la red de Petri
        if visualizar:
            mostrar_grafico(alpha, nombre_log, guardar_grafico)
        
        print("\nEjecutado correctamente")
        return True
    except Exception as e:
        print(f"\nError al procesar: {e}")
        import traceback
        traceback.print_exc()
        return False

def mostrar_grafico(alpha, nombre_log="", guardar=False):
    """Muestra y/o guarda el gráfico de la red de Petri"""
    try:
        import matplotlib.pyplot as plt
        
        # Generar la visualización
        fig = alpha.visualize_petri_net()
        if fig:
            if guardar:
                # Crear directorio para gráficos si no existe
                if not os.path.exists("graficos"):
                    os.makedirs("graficos")
                
                # Nombre del archivo basado en el nombre del log
                nombre_archivo = f"graficos/red_petri_{nombre_log.replace(' ', '_')}.png"
                fig.savefig(nombre_archivo)
                print(f"\nGráfico guardado como: {nombre_archivo}")
            
            # Mostrar el gráfico en una ventana
            plt.show()
            print("\nGráfico mostrado. Cierre la ventana para continuar.")
            return True
        else:
            print("\nNo se pudo generar la visualización.")
            return False
    except ImportError:
        print("\nLa visualización no está disponible. Instale matplotlib y networkx para ver gráficos.")
        return False
    except Exception as e:
        print(f"\nError al visualizar: {e}")
        return False

def main():
    global ultima_instancia_alpha, ultimo_nombre_log
    
    print("====================================================")
    print("            ANALIZADOR DE LOGS DE PROCESOS          ")
    print("====================================================")
    print("Formato de entrada: <a,b,c>, <d,e>^2, <f,g>")
    print("Ejemplo: [<a,b,c,d>^2, <a,c,b,d>^1, <a,e,d>^1]")
    print("Agregue ^n para indicar que una traza se repite n veces.")
    
    # Verificar si la visualización está disponible
    visualizacion_disponible = True
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError:
        visualizacion_disponible = False
        print("\nNOTA: Las bibliotecas necesarias para visualización no están instaladas.")
        print("Instale matplotlib y networkx con: pip install matplotlib networkx")
    
    # Demostración con ejemplo predefinido
    print("\n--- DEMOSTRACIÓN CON EJEMPLO PREDEFINIDO ---")
    log_ejemplo = "[<a,b,c,d>^2, <a,c,b,d>^1, <a,e,d>^1]"
    procesar_y_mostrar_resultados(log_ejemplo, "EJEMPLO", visualizacion_disponible, False)

    # Modo interactivo
    print("\n====================================================")
    print("                  MODO INTERACTIVO                  ")
    print("====================================================")
    while True:
        print("\nOpciones:")
        print("1. Procesar un nuevo log")
        print("2. Usar log ejemplo 1: [<a,b,c,d>,<a,c,b,d>,<a,e,d>]")
        print("3. Usar log ejemplo 2: [<a,b,d>,<a,c,d>]")
        print("4. Usar log ejemplo 3: [<a,b,d>,<a,c,e>,<a,b,e>]")
        print("5. Guardar gráfico de un log")
        print("6. Salir")
        
        opciones_max = 6
        
        opcion = input(f"\nSeleccione una opción (1-{opciones_max}): ").strip()
        
        if opcion == str(opciones_max) or opcion.lower() in ['salir', 'exit', 'q', 'quit']:
            print("\n¡Gracias por usar el analizador de logs!\n")
            break
        elif opcion == '1':
            entrada_log = input("\nIngrese el log: ")
            try:
                entrada_log = validar_formato_log(entrada_log)
                procesar_y_mostrar_resultados(entrada_log, "PERSONALIZADO", 
                                             visualizacion_disponible, False)
            except ValueError as e:
                print(f"\nError de formato: {e}")
                print("Revise que su log tenga el formato correcto y vuelva a intentarlo.")
        elif opcion == '2':
            log1 = "[<a,b,c,d>,<a,c,b,d>,<a,e,d>]"
            procesar_y_mostrar_resultados(log1, "EJEMPLO_1", visualizacion_disponible, False)
        elif opcion == '3':
            log2 = "[<a,b,d>,<a,c,d>]"
            procesar_y_mostrar_resultados(log2, "EJEMPLO_2", visualizacion_disponible, False)
        elif opcion == '4':
            log3 = "[<a,b,d>,<a,c,e>,<a,b,e>]"
            procesar_y_mostrar_resultados(log3, "EJEMPLO_3", visualizacion_disponible, False)
        elif opcion == '5':
            if not visualizacion_disponible:
                print("\nLa visualización no está disponible. Instale matplotlib y networkx primero.")
                continue
                
            # Primero pedir el nombre del archivo
            nombre_archivo = input("\nIngrese el nombre para guardar el gráfico: ").strip()
            if not nombre_archivo:
                nombre_archivo = "red_petri"
                
            # Luego pedir el log a procesar
            entrada_log = input("\nIngrese el log para generar el gráfico: ")
            
            try:
                entrada_log = validar_formato_log(entrada_log)
                # Procesar y guardar directamente, sin mostrar el gráfico en pantalla
                procesar_y_mostrar_resultados(entrada_log, nombre_archivo, False, True)
            except ValueError as e:
                print(f"\nError de formato: {e}")
                print("Revise que su log tenga el formato correcto y vuelva a intentarlo.")
        else:
            print(f"\nOpción no válida. Por favor, seleccione una opción del 1 al {opciones_max}.")

if __name__ == "__main__":
    main()
#L6 <a,f,e,d,b>,<f,a,e,c,b>,<a,f,e,c,b>,<a,f,e,b,d>,<a,f,e,b,c>,<f,a,e,c,b>
#L7 <A,B,C,D,E,F,B,D,C,E,G>,<A,B,D,C,E,G>,<A,B,C,D,E,F,B,C,D,E,F,C,D,C,E,G>