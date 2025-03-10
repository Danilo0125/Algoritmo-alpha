from alpha import Alpha

def limpiar_y_validar_log(cadena_log):
    """Limpia y valida la cadena de log"""
    return cadena_log.strip()

def main():
    print("ANALIZADOR DE LOGS DE PROCESOS")
    print("Formato de entrada: <a,b,c>, <d,e>^2, <f,g>")
    print("Ejemplo: [<A,B,C,D>^2, <A,C,B,D>^1, <A,E,D>^1]")

    analizador = Alpha()
    
    # Demostración con ejemplo predefinido
    print("\n--- DEMOSTRACIÓN CON EJEMPLO PREDEFINIDO ---")
    cadena_log = "[<A,B,C,D>^2, <A,C,B,D>^1, <A,E,D>^1]"
    print(f"Log: {cadena_log}")
    analizador.procesar_log(cadena_log).imprimir_resultados().imprimir_matriz_huella().calcular_lugares().imprimir_lugares()

    # Modo interactivo
    print("\n--- MODO INTERACTIVO ---")
    while True:
        entrada_log = input("\nIngrese el log (o 'salir' para terminar): ")
        if entrada_log.lower() in ['salir', 'exit', 'quit']:
            break

        try:
            entrada_log = limpiar_y_validar_log(entrada_log)
            
            # Procesar el log y mostrar todos los resultados en cadena
            analizador.procesar_log(entrada_log) \
                    .imprimir_resultados() \
                    .imprimir_matriz_huella_() \
                    .calcular_lugares() \
                    .imprimir_lugares()
            
        except Exception as e:
            print(f"Error: {e}. Verifique el formato de entrada.")

if __name__ == "__main__":
    main()

#L6 <a,f,e,d,b>,<f,a,e,c,b>,<a,f,e,c,b>,<a,f,e,b,d>,<a,f,e,b,c>,<f,a,e,c,b>
#L7 <A,B,C,D,E,F,B,D,C,E,G>,<A,B,D,C,E,G>,<A,B,C,D,E,F,B,C,D,E,F,C,D,C,E,G>