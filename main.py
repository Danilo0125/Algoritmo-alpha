from alpha import Alpha

def clean_and_validate_log(log_str):
    """Limpia y valida la cadena de log"""
    return log_str.strip()

def main():
    print("ANALIZADOR DE LOGS DE PROCESOS")
    print("Formato de entrada: <a,b,c>, <d,e>^2, <f,g>")
    print("Ejemplo: [<A,B,C,D>^2, <A,C,B,D>^1, <A,E,D>^1]")

    analyzer = Alpha()
    
    # Demostración con ejemplo predefinido
    print("\n--- DEMOSTRACIÓN CON EJEMPLO PREDEFINIDO ---")
    log_str = "[<A,B,C,D>^2, <A,C,B,D>^1, <A,E,D>^1]"
    print(f"Log: {log_str}")
    analyzer.process_log(log_str).print_results().print_footprint_matrix().compute_places().print_places()

    # Modo interactivo
    print("\n--- MODO INTERACTIVO ---")
    while True:
        log_input = input("\nIngrese el log (o 'salir' para terminar): ")
        if log_input.lower() in ['salir', 'exit', 'quit']:
            break

        try:
            log_input = clean_and_validate_log(log_input)
            
            # Procesar el log y mostrar todos los resultados en cadena
            analyzer.process_log(log_input) \
                    .print_results() \
                    .print_footprint_matrix() \
                    .compute_places() \
                    .print_places()
            
        except Exception as e:
            print(f"Error: {e}. Verifique el formato de entrada.")

if __name__ == "__main__":
    main()