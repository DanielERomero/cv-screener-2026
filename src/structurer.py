import ollama
import json
import re
from typing import Optional, Dict, Any

MODELO = "mistral"

def limpiar_json_raw(texto_raw: str) -> str:
    """
    Intenta extraer el bloque JSON del texto.
    """
    # Buscamos bloques de código markdown primero ```json ... ```
    match_code = re.search(r'```json\s*(\{.*?\})\s*```', texto_raw, re.DOTALL)
    if match_code:
        return match_code.group(1)
    
    # Si no, buscamos el primer bloque que parezca un objeto JSON {...}
    # Usamos non-greedy .*? para parar en la llave de cierre correspondiente
    match = re.search(r'\{.*\}', texto_raw, re.DOTALL)
    if match:
        return match.group(0)
        
    return texto_raw

def estructurar_cv(texto_cv: str) -> Optional[Dict[str, Any]]:
    """
    Usa Mistral para convertir texto de CV en estructura JSON estandarizada.
    """
    # Estructura base para asegurar que siempre devolvemos algo consistente
    schema_template = {
        "nombre": "Desconocido",
        "email": "",
        "telefono": "",
        "skills": [],
        "experiencia": [],
        "educacion": []
    }

    prompt = f"""
    You are an expert HR Data Assistant. Extract structured data from this resume.
    
    OUTPUT JSON ONLY. NO MARKDOWN. NO INTRODUCTIONS.
    Ensure the following keys exist: nombre, email, telefono, skills, experiencia, educacion.
    
    RESUME TEXT:
    {texto_cv[:12000]} 
    """ # Aumentado el límite de caracteres

    print(f"   🤖 Mistral está estructurando la información...")
    try:
        # Primer intento: Configuración estándar (usa GPU si está disponible)
        response = ollama.chat(model=MODELO, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        
        json_str = limpiar_json_raw(content)
        data = json.loads(json_str)
        return {**schema_template, **data}

    except Exception as e:
        # Si falla (ej. error CUDA), intentamos fallback a CPU
        error_msg = str(e)
        if "connect" in error_msg.lower() or "connection" in error_msg.lower():
             print(f"    ⚠️ Error de CONEXIÓN a Ollama: {error_msg}")
             print("       Asegúrate de que Ollama esté corriendo ('ollama serve').")
             return None # No tiene sentido reintentar en CPU si no hay conexión
        
        print(f"    ⚠️ Error en inferencia (posible fallo GPU): {error_msg}")
        
        # Solo reintentamos si no es un error de formato JSON que ya haya pasado la inferencia
        if "JSONDecodeError" not in type(e).__name__:
            print(f"    🔄 Reintentando en modo SOLO CPU (más lento pero más estable)...")
            try:
                # num_gpu=0 fuerza el uso del procesador principal y RAM del sistema
                response = ollama.chat(
                    model=MODELO, 
                    messages=[{'role': 'user', 'content': prompt}],
                    options={'num_gpu': 0} 
                )
                content = response['message']['content']
                json_str = limpiar_json_raw(content)
                data = json.loads(json_str)
                return {**schema_template, **data}
            except Exception as e2:
                print(f"    ❌ Falló también el intento en CPU: {e2}")
                return None
        else:
            print(f"    ❌ Error al procesar el JSON generado: {e}")
            return None