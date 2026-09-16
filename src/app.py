import streamlit as st
import requests

st.set_page_config(page_title="RAG Asistente Médico", page_icon="🤖")

st.title("🤖 Asistente de Manuales - Simuladores Médicos")
st.write("Hazme cualquier pregunta sobre el funcionamiento o mantenimiento de los simuladores.")

# Inicializar el historial de chat
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Mostrar el historial
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])

# Campo de entrada de texto
if prompt := st.chat_input("Ej: ¿Cómo se cambia la batería?"):
    # Mostrar la pregunta del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.mensajes.append({"rol": "user", "contenido": prompt})

    # Llamada a nuestra API de FastAPI
    with st.chat_message("assistant"):
        with st.spinner("Consultando los manuales..."):
            try:
                # OJO: Usamos "api" porque es el nombre del servicio en Docker
                respuesta_api = requests.post(
                    "http://api:8000/ask", 
                    json={"pregunta": prompt}
                )
                
                if respuesta_api.status_code == 200:
                    datos = respuesta_api.json()
                    texto_respuesta = datos["answer"]
                    
                    # Añadir fuentes si existen
                    if datos["sources"]:
                        texto_respuesta += f"\n\n**Fuentes:** {', '.join(map(str, datos['sources']))}"
                    
                    st.markdown(texto_respuesta)
                    st.session_state.mensajes.append({"rol": "assistant", "contenido": texto_respuesta})
                else:
                    st.error("Error al comunicarse con el motor RAG.")
            except Exception as e:
                st.error(f"Fallo de conexión: {e}")