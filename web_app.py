# Importamos la librería para hacer páginas web
import streamlit as st

# Título de prueba
st.title("Hola Mundo!")

# Un texto simple
st.write("Si puedes ver esto es porque René ha hecho un gran trabajo.")

# Un botón interactivo
if st.button("Haz clic aquí"):
    st.success("LOS AMO A TODOS :)")