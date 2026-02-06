import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import ollama

from extractor import extraer_texto_pdf
from structurer import estructurar_cv
# --- NUEVO: Importamos el matcher ---
from matcher import evaluar_candidato 

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    sys.exit("❌ Faltan credenciales .env")

supabase: Client = create_client(url, key)

# --- NUEVO: Definimos el puesto que estamos buscando (Hardcodeado para tesis) ---
JOB_DESCRIPTION = """
Busco un Desarrollador Python Senior para backend.
Requisitos:
- Más de 3 años de experiencia en Python.
- Experiencia obligatoria con Docker y AWS.
- Conocimiento de SQL.
- Inglés intermedio/avanzado.
- Deseable: Experiencia liderando equipos o Tech Lead.
"""
JOB_TITLE = "Python Backend Developer"

def verificar_ollama():
    """Verifica que Ollama esté corriendo y respondiendo."""
    print("🔍 Verificando servicio de Ollama...")
    try:
        ollama.list()
        print("   ✅ Ollama online.")
        return True
    except Exception as e:
        print(f"   ❌ NO se pudo conectar a Ollama. Asegúrate de que esté corriendo ('ollama serve').")
        print(f"   Error: {e}")
        return False

def flujo_principal(ruta_archivo_pdf):
    print(f"\n🔵 --- INICIO DEL PROCESO PARA: {os.path.basename(ruta_archivo_pdf)} ---")

    # 1. Extracción
    print("1️⃣  Extrayendo texto...")
    texto_crudo = extraer_texto_pdf(ruta_archivo_pdf)
    if not texto_crudo or len(texto_crudo) < 50: return

    # 2. Estructuración
    print(f"2️⃣  Estructurando datos...")
    cv_json = estructurar_cv(texto_crudo)
    
    if not cv_json or isinstance(cv_json, str):
        print("   ⚠️ Error en JSON. Saltando.")
        return

    print(f"   ✅ Candidato: {cv_json.get('nombre', 'Desconocido')}")

    # 3. Guardado Candidato
    print("3️⃣  Guardando candidato en DB...")
    candidato_id = None
    try:
        data = {
            "nombre_archivo": os.path.basename(ruta_archivo_pdf),
            "texto_crudo": texto_crudo,
            "cv_datos": cv_json
        }
        # .insert() usualmente devuelve los datos si no se especifica 'presentation' distinto, probamos sin .select()
        res = supabase.table("candidatos").insert(data).execute()
        candidato_id = res.data[0]['id'] # Capturamos el ID para usarlo abajo
    except Exception as e:
        print(f"   ❌ Error DB Candidato: {e}")
        return

    # --- NUEVO: 4. Evaluación (Matching) ---
    if candidato_id:
        print(f"4️⃣  Evaluando contra: {JOB_TITLE}...")
        resultado_eval = evaluar_candidato(cv_json, JOB_DESCRIPTION)
        
        if resultado_eval:
            print(f"   🎯 Score: {resultado_eval.get('score')}/100")
            print(f"   ⚖️  Decisión: {resultado_eval.get('decision')}")
            
            # Guardar Evaluación
            try:
                eval_data = {
                    "candidato_id": candidato_id,
                    "job_role": JOB_TITLE,
                    "score": resultado_eval.get('score'),
                    "decision": resultado_eval.get('decision'),
                    "razonamiento": resultado_eval.get('razonamiento'),
                    "match_details": resultado_eval # Guardamos todo el JSON de detalles
                }
                supabase.table("evaluaciones").insert(eval_data).execute()
                print("   ✨ Evaluación guardada exitosamente.")
            except Exception as e:
                print(f"   ❌ Error guardando evaluación: {e}")

if __name__ == "__main__":
    if not verificar_ollama():
        sys.exit(1)

    archivo_prueba = "cv_prueba.pdf"
    if os.path.exists(archivo_prueba):
        flujo_principal(archivo_prueba)
    else:
        print("❌ Falta el archivo cv_prueba.pdf")