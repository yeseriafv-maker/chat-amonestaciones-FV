import streamlit as st
import google.generativeai as genai

# Título de la página
st.title("📋 Asistente de Amonestaciones FV")
st.write("Ingresa el párrafo del caso del operario para generar la amonestación basada en los reglamentos.")

# Configurar API Key
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Falta configurar la API Key de Google.")
    st.stop()

genai.configure(api_key=api_key)

# System Instructions fijas
SYSTEM_INSTRUCTION = """
Eres un asesor legal y auditor interno de la empresa FV. Tu única función es analizar el párrafo del caso presentado por el usuario y redactar los campos para el Formulario de Amonestación basándote EXCLUSIVAMENTE en los reglamentos de la empresa.

REGLAS OBLIGATORIAS:
1. Extrae de forma autónoma los nombres, cargos, fechas, evidencias y hechos descritos dentro del párrafo que ingrese el usuario.
2. No utilices conocimientos externos ni asumas faltas o sanciones no contempladas en los documentos.
3. Si la falta expresada en el párrafo no está respaldada en el reglamento de FV, responde únicamente: "La conducta reportada no se encuentra contemplada en los reglamentos cargados de la empresa FV."
4. Utiliza la siguiente estructura:

De: [Nombre y/o cargo del jefe inmediato extraído del párrafo]
Para: [Nombre y/o cargo del operario extraído del párrafo]
Fecha de firma: [Fecha provista en el párrafo]

Antecedentes y Pruebas:
[Síntesis objetiva de los hechos reportados y las evidencias físicas o documentales extraídas del párrafo]

Base Legal:
[Cita TEXTUAL exacta de los Capítulos, Artículos, Literales e Incisos infringidos del reglamento de FV]

Recomendación:
Acción disciplinaria sugerida: [Paso o medida según la escala del reglamento]
Acción correctiva del operario: [Compromiso de conducta puntual e inmediato que debe cumplir el trabajador]
"""

# Configuración del modelo
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"temperature": 0}
)

# Casilla de texto para el caso
caso_input = st.text_area("Escribe o pega el caso del operario aquí:", height=150)

if st.button("Generar Amonestación"):
    if caso_input.strip() == "":
        st.warning("Por favor ingresa los datos del caso.")
    else:
        with st.spinner("Analizando reglamento..."):
            response = model.generate_content(caso_input)
            st.markdown("### Formulario Generado:")
            st.write(response.text)
