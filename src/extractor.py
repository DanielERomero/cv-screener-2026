# src/extractor.py
import pdfplumber
import sys

def extraer_texto_pdf(ruta_pdf: str) -> str:
    """
    Abre un PDF y extrae el texto crudo.
    Maneja el cierre seguro del archivo usando 'with'.
    """
    texto_completo = ""
    
    try:
        # El context manager 'with' es vital: asegura que el archivo se cierre
        # incluso si el programa falla a la mitad. Evita fugas de memoria.
        with pdfplumber.open(ruta_pdf) as pdf:
            print(f"🔧 Procesando: {ruta_pdf}")
            print(f"📄 Total de páginas: {len(pdf.pages)}")
            
            # Iteramos página por página (como leer un libro real)
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text()
                
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
                    print(f"    Página {i+1} extraída con éxito.")
                else:
                    print(f"    Página {i+1} vacía o es una imagen escaneada.")
                    
    except FileNotFoundError:
        return " Error: No encontré el archivo. Revisa la ruta."
    except Exception as e:
        return f" Error inesperado: {str(e)}"

    return texto_completo

if __name__ == "__main__":
    # Esto permite correr el script desde la consola enviando el archivo como argumento
    if len(sys.argv) < 2:
        print("Uso: uv run python src/extractor.py <ruta_al_pdf>")
    else:
        archivo = sys.argv[1]
        resultado = extraer_texto_pdf(archivo)
        print("\n--- TEXTO EXTRAÍDO ---")
        print(resultado[:500]) # Solo mostramos los primeros 500 caracteres para no saturar
        print("...\n(Resto del texto omitido)")