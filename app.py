import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time

# Configuración de la página web
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

# Asignación directa del modelo solicitado por la API de Google
@st.cache_resource
def cargar_modelo():
    modelos_a_probar = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash"]
    for m_name in modelos_a_probar:
        try:
            m = genai.GenerativeModel(
                model_name=m_name,
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config={"temperature": 0}
            )
            return m
        except Exception:
            continue
    # Si ninguno funciona de la lista, intentar el estándar
    return genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config={"temperature": 0}
    )

model = cargar_modelo()

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
                            st.error("Se ha alcanzado el límite de solicitudes por minuto. Espera un momento antes de volver a presionar el botón.")
                            break
                    else:
                        st.error(f"Error al procesar: {e}")
                        break
