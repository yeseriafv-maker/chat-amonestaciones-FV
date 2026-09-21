import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time

# Configuración de la página web (Título corregido sin íconos incompatibles)
st.set_page_config(page_title="Asistente de Amonestaciones FV", page_icon="📄")
st.title("Asistente de Amonestaciones FV")
st.write("Ingresa el párrafo del caso del operario para generar la amonestación basada EXCLUSIVAMENTE en los reglamentos de la empresa.")

# Lectura de la clave API
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Falta configurar la API Key de Google en los Secrets de Streamlit.")
    st.stop()

genai.configure(api_key=api_key)

# Nombres de los archivos PDF
PDF_1_PATH = "Reglamento_Interno.pdf"
PDF_2_PATH = "RIHSI_2026.pdf"

@st.cache_resource
def leer_pdf_archivos():
    texto_completo = ""
    for path in [PDF_1_PATH, PDF_2_PATH]:
        try:
            reader = PdfReader(path)
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    texto_completo += texto + "\n"
        except Exception as e:
            st.error(f"Error al leer el archivo {path}: {e}")
            st.stop()
    return texto_completo

# Carga de reglamentos en memoria
contexto_reglamentos = leer_pdf_archivos()

SYSTEM_INSTRUCTION = f"""
Eres un asesor legal y auditor interno de la empresa FV. Tu única función es analizar el párrafo del caso presentado por el usuario y redactar los campos para el Formulario de Amonestación basándote EXCLUSIVAMENTE en los siguientes reglamentos cargados:

--- REGLAMENTOS DE LA EMPRESA FV ---
{contexto_reglamentos}
------------------------------------

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

# Selección dinámica del modelo disponible
@st.cache_resource
def obtener_modelo():
    try:
        modelos_disponibles = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        
        # Buscar en orden de preferencia de modelos de texto rápidos
        for preferido in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.6-flash", "gemini-pro"]:
            for m in modelos_disponibles:
                if preferido in m:
                    return genai.GenerativeModel(
                        model_name=m,
                        system_instruction=SYSTEM_INSTRUCTION,
                        generation_config={"temperature": 0}
                    )
        
        # Si ninguno coincide, seleccionar el primero que soporte generación de contenido
        if modelos_disponibles:
            return genai.GenerativeModel(
                model_name=modelos_disponibles[0],
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config={"temperature": 0}
            )
    except Exception as e:
        st.error(f"Error al obtener lista de modelos de Gemini: {e}")
        st.stop()

model = obtener_modelo()

caso_input = st.text_area("Escribe o pega el caso del operario en un párrafo aquí:", height=150)

if st.button("Generar Amonestación"):
    if not caso_input.strip():
        st.warning("Por favor ingresa los datos del caso.")
    else:
        with st.spinner("Analizando reglamentos de FV..."):
            exito = False
            intentos = 0
            max_intentos = 3
            
            while not exito and intentos < max_intentos:
                try:
                    response = model.generate_content(caso_input)
                    st.markdown("---")
                    st.markdown("### Formulario de Amonestación Generado:")
                    st.write(response.text)
                    exito = True
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "quota" in error_str.lower():
                        intentos += 1
                        if intentos < max_intentos:
                            st.info(f"Límite de frecuencia alcanzado. Esperando 10 segundos para reintentar ({intentos}/{max_intentos})...")
                            time.sleep(10)
                        else:
                            st.error("Se ha alcanzado el límite de solicitudes. Por favor espera unos momentos antes de presionar el botón de nuevo.")
                    else:
                        st.error(f"Error al procesar: {e}")
                        break
