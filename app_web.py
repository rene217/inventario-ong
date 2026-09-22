import streamlit as st
import psycopg2
from datetime import datetime

st.set_page_config(page_title="Inventario ONG", layout="wide")

ocultar_elementos_estilo = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(ocultar_elementos_estilo, unsafe_allow_html=True)

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS (SUPABASE / POSTGRESQL) ---
def conectar_db():
    database_url = st.secrets["DATABASE_URL"]
    conexion = psycopg2.connect(database_url)
    return conexion

def inicializar_base_datos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id SERIAL PRIMARY KEY,
            codigo TEXT,
            cantidad INTEGER,
            nombre TEXT NOT NULL,
            marca TEXT,
            descripcion TEXT NOT NULL,
            observaciones TEXT NOT NULL,
            estado TEXT,
            area TEXT,
            responsable TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            rol TEXT NOT NULL,
            area TEXT NOT NULL
        )
    ''')
    
    # Crear únicamente el usuario Administrador por defecto si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO usuarios (username, password, nombre_completo, rol, area) VALUES (%s, %s, %s, %s, %s)",
            ("admin", "1234", "Administrador General", "Administrador", "Todas")
        )
        conexion.commit()
        
    conexion.close()

inicializar_base_datos()

AREAS_ONG = [
    "Cocina General",
    "Cocina Cursos (Parrilla)",
    "Cocina Cursos (Repostería)",
    "Cocina area de Salud",
    "Clinica Dental",
    "Clinica Médica",
    "Farmacia",
    "Liceo",
    "Módulo Uñas Acrílicas",
    "Módulo Maquillaje",
    "Módulo Costura",
    "Administración"
]

# --- 2. SISTEMA DE LOGIN Y SESIÓN SEGURO ---
st.sidebar.title("Acceso al Sistema")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["username"] = ""
    st.session_state["nombre_completo"] = ""
    st.session_state["rol"] = ""
    st.session_state["area"] = ""

if not st.session_state["autenticado"]:
    st.sidebar.subheader("Por favor, inicia sesión")
    user_ingresado = st.sidebar.text_input("Usuario").strip().lower()
    pass_ingresado = st.sidebar.text_input("Contraseña", type="password")
    
    if st.sidebar.button("Ingresar"):
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute("SELECT username, password, nombre_completo, rol, area FROM usuarios WHERE username = %s", (user_ingresado,))
        user_db = cursor.fetchone()
        conexion.close()
        
        if user_db and user_db[1] == pass_ingresado:
            st.session_state["autenticado"] = True
            st.session_state["username"] = user_db[0]
            st.session_state["nombre_completo"] = user_db[2]
            st.session_state["rol"] = user_db[3]
            st.session_state["area"] = user_db[4]
            st.rerun()
        else:
            st.sidebar.error("Usuario o contraseña incorrectos")
            
    st.title("Sistema de Inventario - ONG")
    st.warning("<- Por favor, inicia sesión en la barra lateral para acceder al sistema. (Credencial inicial por defecto: usuario **admin**, contraseña **1234**).")
    
else:
    st.sidebar.success(f"Bienvenido/a:\n**{st.session_state['nombre_completo']}**\n\nRol: {st.session_state['rol']}")
    if st.session_state['rol'] == "Encargado":
        st.sidebar.info(f"Área(s) Asignada(s):\n{st.session_state['area']}")
        
    with st.sidebar.expander("🔑 Cambiar mi contraseña"):
        with st.form("form_cambiar_pass"):
            nueva_pass1 = st.text_input("Nueva contraseña", type="password")
            nueva_pass2 = st.text_input("Confirmar contraseña", type="password")
            btn_pass = st.form_submit_button("Actualizar Contraseña")
            if btn_pass:
                if nueva_pass1 != nueva_pass2:
                    st.error("Las contraseñas no coinciden.")
                elif len(nueva_pass1) < 4:
                    st.error("La contraseña debe tener al menos 4 caracteres.")
                else:
                    conexion = conectar_db()
                    cursor = conexion.cursor()
                    cursor.execute("UPDATE usuarios SET password = %s WHERE username = %s", (nueva_pass1, st.session_state['username']))
                    conexion.commit()
                    conexion.close()
                    st.success("¡Contraseña actualizada con éxito!")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    st.title("Gestión de Inventario Web - ONG")
    
    if st.session_state['rol'] == "Administrador":
        pestana_ver, pestana_registrar, pestana_tarjetas, pestana_usuarios = st.tabs([
            "Ver y Editar Inventario", "Registrar Objeto", "Tarjeta de Responsabilidad", "Gestionar Usuarios"
        ])
    else:
        pestana_ver, pestana_registrar, pestana_tarjetas = st.tabs([
            "Ver y Editar Inventario", "Registrar Objeto", "Tarjeta de Responsabilidad"
        ])

    # --- PESTAÑA DE VISUALIZACIÓN, EDICIÓN Y ELIMINACIÓN ---
    with pestana_ver:
        st.subheader("Listado general, modificación y baja de bienes")
        
        if st.session_state['rol'] == "Administrador":
            filtro_elegido = st.selectbox("Filtrar por Área:", ["Todas las Áreas"] + AREAS_ONG)
        else:
            areas_permitidas = [a.strip() for a in st.session_state['area'].split(",")]
            if len(areas_permitidas) > 1:
                filtro_elegido = st.selectbox("Tus Áreas Asignadas:", areas_permitidas)
            else:
                filtro_elegido = areas_permitidas[0]
                st.info(f"Mostrando inventario de tu área: **{filtro_elegido}**")
        
        conexion = conectar_db()
        cursor = conexion.cursor()
        
        if filtro_elegido != "Todas las Áreas":
            cursor.execute("SELECT * FROM inventario WHERE area = %s", (filtro_elegido,))
        else:
            cursor.execute("SELECT * FROM inventario")
            
        registros = cursor.fetchall()
        conexion.close()
        
        if registros:
            st.write(f"Se encontraron {len(registros)} registros:")
            
            for reg in registros:
                id_reg = reg[0]
                codigo_reg = reg[1]
                cantidad_reg = reg[2]
                nombre_reg = reg[3]
                marca_reg = reg[4]
                desc_reg = reg[5]
                obs_reg = reg[6]
                estado_reg = reg[7]
                area_reg = reg[8]
                resp_reg = reg[9]
                
                with st.expander(f"[{codigo_reg if codigo_reg else 'S/C'}] {nombre_reg} - Área: {area_reg}"):
                    op_ver, op_editar, op_eliminar = st.tabs(["Detalles", "Editar Registro", "Eliminar"])
                    
                    with op_ver:
                        st.write(f"**Código:** {codigo_reg if codigo_reg else 'Sin código asignado'}")
                        st.write(f"**Cantidad:** {cantidad_reg}")
                        st.write(f"**Marca:** {marca_reg if marca_reg else 'N/A'}")
                        st.write(f"**Descripción:** {desc_reg}")
                        st.write(f"**Observaciones:** {obs_reg}")
                        st.write(f"**Estado:** {estado_reg}")
                        st.write(f"**Responsable:** {resp_reg}")
                    
                    with op_editar:
                        with st.form(f"form_editar_{id_reg}"):
                            nuevo_codigo = st.text_input("Código (opcional)", value=str(codigo_reg) if codigo_reg else "")
                            nueva_cantidad = st.number_input("Cantidad", min_value=1, value=int(cantidad_reg), step=1, key=f"cant_{id_reg}")
                            nuevo_nombre = st.text_input("Nombre del Objeto *", value=str(nombre_reg), key=f"nom_{id_reg}")
                            nueva_marca = st.text_input("Marca (opcional)", value=str(marca_reg) if marca_reg else "", key=f"mar_{id_reg}")
                            
                            if st.session_state['rol'] == "Administrador":
                                try:
                                    index_area = AREAS_ONG.index(area_reg)
                                except ValueError:
                                    index_area = 0
                                nuevo_area = st.selectbox("Área / Módulo *", AREAS_ONG, index=index_area, key=f"area_{id_reg}")
                            else:
                                nuevo_area = area_reg
                                st.write(f"**Área Asignada:** {nuevo_area}")
                            
                            lista_estados = ["Nuevo", "En uso", "Bueno", "Dañado / En reparación", "Obsoleto"]
                            try:
                                index_estado = lista_estados.index(estado_reg)
                            except ValueError:
                                index_estado = 0
                                
                            nuevo_estado = st.selectbox("Estado *", lista_estados, index=index_estado, key=f"est_{id_reg}")
                            nuevo_resp = st.text_input("Responsable *", value=str(resp_reg) if resp_reg else "", key=f"resp_{id_reg}")
                            
                            nueva_desc = st.text_area("Descripción *", value=str(desc_reg) if desc_reg else "", key=f"desc_{id_reg}")
                            nuevas_obs = st.text_area("Observaciones *", value=str(obs_reg) if obs_reg else "", key=f"obs_{id_reg}")
                            
                            btn_guardar_cambios = st.form_submit_button("Guardar Cambios")
                            
                            if btn_guardar_cambios:
                                if not nuevo_nombre.strip() or not nueva_desc.strip() or not nuevas_obs.strip() or not nuevo_resp.strip():
                                    st.error("Error: Todos los campos marcados son obligatorios.")
                                else:
                                    try:
                                        conexion = conectar_db()
                                        cursor = conexion.cursor()
                                        cursor.execute('''
                                            UPDATE inventario 
                                            SET codigo = %s, cantidad = %s, nombre = %s, marca = %s, descripcion = %s, observaciones = %s, estado = %s, area = %s, responsable = %s
                                            WHERE id = %s
                                        ''', (nuevo_codigo, int(nueva_cantidad), nuevo_nombre, nueva_marca, nueva_desc, nuevas_obs, nuevo_estado, nuevo_area, nuevo_resp, id_reg))
                                        conexion.commit()
                                        conexion.close()
                                        st.success("¡Registro actualizado correctamente!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error al actualizar: {e}")
                            
                    with op_eliminar:
                        st.warning("¿Estás seguro de eliminar este objeto del inventario?")
                        if st.button("Sí, eliminar definitivamente", key=f"btn_del_{id_reg}"):
                            try:
                                conexion = conectar_db()
                                cursor = conexion.cursor()
                                cursor.execute("DELETE FROM inventario WHERE id = %s", (id_reg,))
                                conexion.commit()
                                conexion.close()
                                st.success("¡Objeto eliminado del inventario!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al eliminar: {e}")
        else:
            st.info("No hay objetos registrados todavía o en esta área.")

    # --- PESTAÑA DE REGISTRO ---
    with pestana_registrar:
        st.subheader("Registrar nuevo bien en el inventario")
        st.caption("Nota: El Código y la Marca son opcionales. Todo lo demás es obligatorio.")
        
        with st.form("form_registro"):
            col1, col2 = st.columns(2)
            
            with col1:
                txt_codigo = st.text_input("Código (Opcional)")
                txt_cantidad = st.number_input("Cantidad *", min_value=1, value=1, step=1)
                txt_nombre = st.text_input("Nombre del Objeto *")
                txt_marca = st.text_input("Marca (Opcional)")
                
            with col2:
                txt_estado = st.selectbox("Estado *", ["Nuevo", "En uso", "Bueno", "Dañado / En reparación", "Obsoleto"])
                
                if st.session_state['rol'] == "Administrador":
                    txt_area = st.selectbox("Área / Módulo *", AREAS_ONG)
                else:
                    areas_permitidas = [a.strip() for a in st.session_state['area'].split(",")]
                    if len(areas_permitidas) > 1:
                        txt_area = st.selectbox("Selecciona Área de Registro *", areas_permitidas)
                    else:
                        txt_area = areas_permitidas[0]
                        st.write(f"**Área de Registro:** {txt_area}")
                    
                txt_responsable = st.text_input("Responsable (Tarjeta) *")
                
            txt_descripcion = st.text_area("Descripción *")
            txt_observaciones = st.text_area("Observaciones *")
            
            btn_enviar = st.form_submit_button("Guardar Objeto en el Inventario")
            
            if btn_enviar:
                if not txt_nombre.strip() or not txt_descripcion.strip() or not txt_observaciones.strip() or not txt_responsable.strip():
                    st.error("Faltan campos obligatorios. Por favor llena el Nombre, Descripción, Observaciones y Responsable.")
                else:
                    try:
                        conexion = conectar_db()
                        cursor = conexion.cursor()
                        cursor.execute('''
                            INSERT INTO inventario (codigo, cantidad, nombre, marca, descripcion, observaciones, estado, area, responsable)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (txt_codigo, int(txt_cantidad), txt_nombre, txt_marca, txt_descripcion, txt_observaciones, txt_estado, txt_area, txt_responsable))
                        conexion.commit()
                        conexion.close()
                        st.success("🎉 ¡Objeto guardado exitosamente en el inventario de la ONG!")
                    except Exception as e:
                        st.error(f"Ocurrió un error al guardar: {e}")

    # --- PESTAÑA DE TARJETA DE RESPONSABILIDAD ---
    with pestana_tarjetas:
        st.subheader("Generación de Tarjeta de Responsabilidad")
        
        if st.session_state['rol'] == "Administrador":
            area_tarjeta = st.selectbox("Seleccionar Área para la Tarjeta:", AREAS_ONG, key="sel_tarjeta_admin")
        else:
            areas_permitidas = [a.strip() for a in st.session_state['area'].split(",")]
            if len(areas_permitidas) > 1:
                area_tarjeta = st.selectbox("Selecciona el Área para la Tarjeta:", areas_permitidas, key="sel_tarjeta_multi")
            else:
                area_tarjeta = areas_permitidas[0]
                st.write(f"Generando tarjeta para tu área: **{area_tarjeta}**")
            
        if st.button("Generar Tarjeta de Responsabilidad"):
            fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
            nombre_usuario_actual = st.session_state['nombre_completo']
            
            conexion = conectar_db()
            cursor = conexion.cursor()
            cursor.execute("SELECT codigo, cantidad, nombre, marca, estado, responsable FROM inventario WHERE area = %s", (area_tarjeta,))
            bienes_area = cursor.fetchall()
            conexion.close()
            
            st.markdown("---")
            st.markdown(f"###  TARJETA DE RESPONSABILIDAD DE BIENES")
            st.markdown(f"**Área / Módulo:** {area_tarjeta}")
            st.markdown(f"**Generado por el Encargado:** {nombre_usuario_actual}")
            st.markdown(f"**Fecha y hora de emisión:** {fecha_actual}")
            st.markdown("---")
            
            if bienes_area:
                for idx, bien in enumerate(bienes_area, 1):
                    st.markdown(f"""
                    **{idx}. Objeto:** {bien[2]}  
                    * **Código:** {bien[0] if bien[0] else 'S/C'} | **Cantidad:** {bien[1]} | **Marca:** {bien[3] if bien[3] else 'N/A'}  
                    * **Estado:** {bien[4]} | **Custodio / Responsable:** {bien[5]}  
                    --------------------------------------------------
                    """)
                st.info("Tip: Presiona `Ctrl + P` en tu navegador para imprimir esta tarjeta o guardarla como PDF de manera limpia.")
            else:
                st.warning("No hay bienes registrados en esta área para generar una tarjeta.")

    # --- PESTAÑA DE GESTIÓN DE USUARIOS (SOLO PARA ADMIN) ---
    if st.session_state['rol'] == "Administrador":
        with pestana_usuarios:
            st.subheader("👥 Gestión de Usuarios y Accesos")
            st.markdown("Aquí puedes registrar nuevos usuarios o dar de baja a los existentes cuando sea necesario.")
            
            with st.form("form_nuevo_usuario"):
                st.markdown("#### Registrar Nuevo Usuario")
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    nuevo_user = st.text_input("Nombre de Usuario (para iniciar sesión, sin espacios)")
                    nuevo_pass = st.text_input("Contraseña inicial", type="password")
                    nuevo_nombre_completo = st.text_input("Nombre Completo (Ej. María Pérez)")
                with col_u2:
                    nuevo_rol = st.selectbox("Rol", ["Encargado", "Administrador"])
                    nuevo_area_asignada = st.multiselect("Área(s) Asignada(s)", AREAS_ONG)
                    
                btn_crear_user = st.form_submit_button("Crear Cuenta de Usuario")
                
                if btn_crear_user:
                    if not nuevo_user.strip() or not nuevo_pass.strip() or not nuevo_nombre_completo.strip():
                        st.error("Todos los campos de usuario son obligatorios.")
                    else:
                        areas_texto = ", ".join(nuevo_area_asignada) if nuevo_area_asignada else "Ninguna"
                        try:
                            conexion = conectar_db()
                            cursor = conexion.cursor()
                            cursor.execute("INSERT INTO usuarios (username, password, nombre_completo, rol, area) VALUES (%s, %s, %s, %s, %s)",
                                         (nuevo_user.strip().lower(), nuevo_pass, nuevo_nombre_completo, nuevo_rol, areas_texto))
                            conexion.commit()
                            conexion.close()
                            st.success(f"¡Usuario '{nuevo_nombre_completo}' creado con éxito!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear usuario (es posible que el nombre de usuario ya exista): {e}")

            st.markdown("---")
            st.markdown("#### Lista de Usuarios Actuales")
            conexion = conectar_db()
            cursor = conexion.cursor()
            cursor.execute("SELECT id, username, nombre_completo, rol, area FROM usuarios")
            lista_usuarios = cursor.fetchall()
            conexion.close()
            
            for u in lista_usuarios:
                id_u, uname, fullname, urol, uarea = u
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.write(f"**Nombre:** {fullname} | **Usuario:** `{uname}` | **Rol:** {urol} | **Áreas:** {uarea}")
                with col_btn:
                    if uname != "admin":
                        if st.button("Eliminar", key=f"del_user_{id_u}"):
                            conexion = conectar_db()
                            cursor = conexion.cursor()
                            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_u,))
                            conexion.commit()
                            conexion.close()
                            st.success(f"Usuario {fullname} eliminado.")
                            st.rerun()
                    else:
                        st.caption("Principal")