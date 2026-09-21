import os
import streamlit as st
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Asistente de Amonestaciones FV", page_icon="📋")
st.title("📋 Asistente de Amonestaciones FV")
st.write("Ingresa el párrafo del caso del operario para generar la amonestación basada EXCLUSIVAMENTE en los reglamentos de la empresa.")

# Configurar API Key
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Falta configurar la API Key de Google en los Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# Nombres exactos de los archivos PDF subidos a GitHub
PDF_1_PATH = "Reglamento_Interno.pdf"
PDF_2_PATH = "RIHSI_2026.pdf"

@st.cache_resource
def cargar_documentos():
    """Carga los reglamentos a la API de Gemini en segundo plano."""
    files_uploaded = []
    for pdf_path in [PDF_1_PATH, PDF_2_PATH]:
        if os.path.exists(pdf_path):
            uploaded_file = genai.upload_file(pdf_path)
            files_uploaded.append(uploaded_file)
        else:
            st.error(f"No se encontró el archivo: {pdf_path}. Asegúrate de haberlo subido a GitHub con ese nombre exacto.")
            st.stop()
    return files_uploaded

# Cargar los PDF
documentos_fv = cargar_documentos()

# Instrucciones estrictas del sistema
SYSTEM_INSTRUCTION = """
Eres un asesor legal y auditor interno de la empresa FV. Tu única función es analizar el párrafo del caso presentado por el usuario y redactar los campos para el Formulario de Amonestación basándote EXCLUSIVAMENTE en los reglamentos cargados en este chat.

REGLAS OBLIGATORIAS:
1. Extrae de forma autónoma los nombres, cargos, fechas, evidencias y hechos descritos dentro del párrafo que ingrese el usuario.
2. No utilices conocimientos externos ni asumas faltas o sanciones no contempladas en los documentos.
3. Si la falta expresada en el párrafo no está respaldada en los reglamentos cargados de FV, responde únicamente: "La conducta reportada no se encuentra contemplada en los reglamentos cargados de la empresa FV."
4. Utiliza la siguiente estructura estricta:

De: [Nombre y/o cargo del jefe inmediato extraído del párrafo]
Para: [Nombre y/o cargo del operario extraído del párrafo]
Fecha de firma: [Fecha provista en el párrafo]

Antecedentes y Pruebas:
[Síntesis objetiva de los hechos reportados y las evidencias físicas o documentales extraídas del párrafo]

Base Legal:
[Cita TEXTUAL exacta de los Capítulos, Artículos, Literales e Incisos infringidos de los reglamentos de FV]

Recomendación:
Acción disciplinaria sugerida: [Paso o medida según la escala del reglamento, ej. Amonestación escrita por reincidencia]
Acción correctiva del operario: [Compromiso de conducta puntual e inmediato que debe cumplir el trabajador para evitar reincidencias]
"""

# Configuración del modelo Gemini
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"temperature": 0}
)

# Entrada del caso por el usuario
caso_input = st.text_area("Escribe o pega el caso del operario en un párrafo aquí:", height=150)

if st.button("Generar Amonestación"):
    if not caso_input.strip():
        st.warning("Por favor ingresa los datos del caso.")
    else:
        with st.spinner("Analizando reglamentos de FV..."):
            prompt_content = [*documentos_fv, caso_input]
            response = model.generate_content(prompt_content)
            
            st.markdown("---")
            st.markdown("### Formulario de Amonestación Generado:")
            st.write(response.text)
