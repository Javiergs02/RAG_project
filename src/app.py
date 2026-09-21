import os
import streamlit as st
import requests

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Asistente RAG - Documentación Dinámica",
    page_icon="📚",
    layout="wide"
)

# URL del backend (por defecto apunta al servicio 'api' en la red de Docker)
API_URL = os.getenv("API_URL", "http://api:8000")

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "documentos_activos" not in st.session_state:
    st.session_state.documentos_activos = []


# --- FUNCIONES AUXILIARES DE COMUNICACIÓN CON LA API ---
def verificar_estado_api():
    """Consulta si el backend tiene documentos indexados actualmente."""
    try:
        response = requests.get(f"{API_URL}/status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {"status": "error", "chunks_activos": 0}


def enviar_archivos_api(archivos):
    """Envía la lista de PDFs al endpoint /upload para reemplazar la colección."""
    files_payload = [
        ("files", (archivo.name, archivo.getvalue(), "application/pdf"))
        for archivo in archivos
    ]
    response = requests.post(f"{API_URL}/upload", files=files_payload, timeout=120)
    return response


def consultar_api(pregunta):
    """Envía la pregunta del usuario al endpoint /query."""
    response = requests.post(
        f"{API_URL}/query",
        json={"pregunta": pregunta},
        timeout=60
    )
    return response

def enviar_feedback_api(pregunta, respuesta, fuentes, valoracion):
    """Envía la valoración del usuario al backend para guardarla en los logs."""
    try:
        requests.post(
            f"{API_URL}/feedback",
            json={
                "pregunta": pregunta,
                "respuesta": respuesta,
                "fuentes": fuentes,
                "valoracion": valoracion
            },
            timeout=5
        )
    except Exception as e:
        st.error(f"Error de conexión al guardar el voto: {e}")
        # Si el log falla, no queremos bloquear la interfaz al usuario

# --- BARRA LATERAL (SIDEBAR): GESTIÓN DOCUMENTAL ---
with st.sidebar:
    st.header("⚙️ Gestión Documental")
    st.caption("Modo Sesión: Los documentos cargados reemplazarán el contexto anterior.")

    archivos_subidos = st.file_uploader(
        "Subir uno o varios archivos PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="Selecciona los manuales o guías sobre los que deseas consultar."
    )

    if st.button("Indexar y comenzar sesión", type="primary", use_container_width=True):
        if not archivos_subidos:
            st.warning("Selecciona al menos un archivo PDF antes de indexar.")
        else:
            with st.spinner("Extrayendo texto, troceando y generando vectores en ChromaDB..."):
                try:
                    res = enviar_archivos_api(archivos_subidos)
                    if res.status_code == 200:
                        datos = res.json()
                        st.session_state.documentos_activos = datos.get("archivos_procesados", [])
                        total_chunks = datos.get("total_chunks", 0)

                        # Reiniciamos el historial de chat para evitar mezclar sesiones
                        st.session_state.messages = [
                            {
                                "role": "assistant",
                                "content": (
                                    f"✅ **Sesión iniciada con éxito.**\n\n"
                                    f"He indexado {len(st.session_state.documentos_activos)} documento(s) "
                                    f"en un total de **{total_chunks} fragmentos vectoriales**.\n\n"
                                    f"¿Qué deseas consultar sobre este material?"
                                ),
                                "sources": []
                            }
                        ]
                        st.success("¡Base de datos vectorial actualizada!")
                        st.rerun()
                    else:
                        st.error(f"Error al procesar: {res.text}")
                except requests.exceptions.ConnectionError:
                    st.error("No se pudo contactar con la API. Verifica que el contenedor del backend esté activo.")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {str(e)}")

    # Visualización de documentos en la sesión activa
    st.divider()
    st.subheader("📄 Fuentes Activas")
    if st.session_state.documentos_activos:
        for doc in st.session_state.documentos_activos:
            st.markdown(f"- `{doc}`")
    else:
        st.info("No hay documentos indexados en esta sesión.")


# --- ZONA PRINCIPAL: CHAT CONTEXTUAL ---
st.title("Asistente RAG Multi-Documento")
st.markdown("Consulta especificaciones técnicas y operativas con trazabilidad de fuentes.")

# Comprobación de estado si el usuario entra sin haber subido archivos
if not st.session_state.documentos_activos:
    estado_servidor = verificar_estado_api()
    if estado_servidor.get("chunks_activos", 0) == 0:
        st.info("👈 Comienza subiendo uno o más documentos PDF en la barra lateral para iniciar la sesión.")

# Mostrar mensajes anteriores del historial
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📍 Fuentes consultadas"):
                for fuente in msg["sources"]:
                    st.markdown(f"- {fuente}")
        
        # Mostrar botones de feedback solo en las respuestas del asistente
        if msg["role"] == "assistant" and "pregunta_asociada" in msg:
            # st.feedback devuelve 1 (pulgar arriba) o 0 (pulgar abajo)
            feedback = st.feedback("thumbs", key=f"fb_{i}")
            
            # Si el usuario hace clic y no lo hemos registrado aún en esta sesión
            if feedback is not None and not msg.get("feedback_registrado"):
                enviar_feedback_api(
                    pregunta=msg["pregunta_asociada"],
                    respuesta=msg["content"],
                    fuentes=msg.get("sources", []),
                    valoracion=feedback
                )
                # Marcamos para que no se envíe el mismo log múltiples veces
                st.session_state.messages[i]["feedback_registrado"] = True

# Captura de nuevas preguntas
if prompt := st.chat_input("Escribe tu pregunta sobre la documentación cargada..."):
    # Añadir y pintar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("Buscando fragmentos relevantes y redactando respuesta..."):
            try:
                res = consultar_api(prompt)
                if res.status_code == 200:
                    respuesta_data = res.json()
                    contenido_respuesta = respuesta_data.get("respuesta", "")
                    fuentes = respuesta_data.get("fuentes", [])

                    st.markdown(contenido_respuesta)
                    if fuentes:
                        with st.expander("📍 Fuentes consultadas"):
                            for fuente in fuentes:
                                st.markdown(f"- {fuente}")

                    # Guardar respuesta en el historial de sesión (incluyendo la pregunta asociada)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": contenido_respuesta,
                        "sources": fuentes,
                        "pregunta_asociada": prompt,
                        "feedback_registrado": False
                    })
                    st.rerun() # Refresca la UI para que aparezcan los botones de feedback
                elif res.status_code == 400:
                    mensaje_alerta = res.json().get("detail", "Error en la consulta.")
                    st.warning(mensaje_alerta)
                else:
                    st.error(f"Error {res.status_code}: {res.text}")
            except requests.exceptions.ConnectionError:
                st.error("No se pudo conectar con el motor RAG.")
            except Exception as e:
                st.error(f"Error al procesar la solicitud: {str(e)}") 