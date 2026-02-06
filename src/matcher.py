import ollama
import json
import re

MODELO = "mistral"

def evaluar_candidato(cv_json: dict, job_description: str):
    """
    Compara un CV estructurado (JSON) contra un Job Description (Texto).
    Retorna un diccionario con score, decisión y justificación.
    """
    
    # Convertimos el JSON a string para que el LLM lo pueda leer
    cv_texto = json.dumps(cv_json, indent=2)

    prompt = f"""
    You are a Senior Technical Recruiter. Evaluate this candidate for the Job Description provided.
    
    JOB DESCRIPTION:
    {job_description}

    CANDIDATE PROFILE (JSON):
    {cv_texto}

    TASK:
    1. Analyze if the candidate has the required skills and experience.
    2. Assign a Score from 0 to 100.
    3. Determine a Decision: "Apto" (Score >= 70), "No Apto" (Score < 50), or "Revisar" (50-69).
    4. Provide a brief reasoning citing specific evidence (e.g., "Has Python but lacks AWS").

    OUTPUT FORMAT (Valid JSON only):
    {{
        "score": 85,
        "decision": "Apto",
        "razonamiento": "Strong Python experience...",
        "pros": ["skill1", "skill2"],
        "contras": ["missing_skill1"]
    }}
    
    CRITICAL: Return ONLY JSON. No Markdown.
    """

    print(f"   ⚖️  Evaluando compatibilidad (Match)...")
    
    try:
        response = ollama.chat(model=MODELO, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        
        # Limpieza de Markdown (reutilizamos la lógica simple)
        texto_limpio = re.sub(r'```json\s*', '', content)
        texto_limpio = re.sub(r'```', '', texto_limpio)
        
        # Extracción de JSON
        inicio = texto_limpio.find('{')
        fin = texto_limpio.rfind('}')
        if inicio != -1 and fin != -1:
            json_str = texto_limpio[inicio:fin+1]
            return json.loads(json_str)
        else:
            print("   ⚠️ No encontré JSON en la respuesta de evaluación.")
            return None

    except Exception as e:
        print(f"   ❌ Error en el Matching: {e}")
        return None