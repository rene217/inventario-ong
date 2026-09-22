import sqlite3
import tkinter as ttk_lib
from tkinter import messagebox, ttk

# 1. Asegurar que la base de datos exista
def inicializar_base_datos():
    conexion = sqlite3.connect('inventario_ong.db')
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            cantidad INTEGER,
            nombre TEXT NOT NULL,
            marca TEXT,
            descripcion TEXT,
            observaciones TEXT,
            estado TEXT,
            area TEXT,
            responsable TEXT
        )
    ''')
    conexion.commit()
    conexion.close()

# 2. Función para guardar los datos
def guardar_objeto():
    codigo = entry_codigo.get()
    cantidad = entry_cantidad.get()
    nombre = entry_nombre.get()
    marca = entry_marca.get()
    descripcion = entry_descripcion.get()
    observaciones = entry_observaciones.get()
    estado = combo_estado.get()
    area = combo_area.get()
    responsable = entry_responsable.get().strip()

    if not nombre or not cantidad:
        messagebox.showerror("Error", "El Nombre y la Cantidad son obligatorios.")
        return

    try:
        conexion = sqlite3.connect('inventario_ong.db')
        cursor = conexion.cursor()
        cursor.execute('''
            INSERT INTO inventario (codigo, cantidad, nombre, marca, descripcion, observaciones, estado, area, responsable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (codigo, int(cantidad), nombre, marca, descripcion, observaciones, estado, area, responsable))
        
        conexion.commit()
        conexion.close()

        messagebox.showinfo("Éxito", "¡Objeto registrado correctamente en el inventario!")
        limpiar_campos()
        actualizar_tabla()
        actualizar_lista_responsables()

    except ValueError:
        messagebox.showerror("Error", "La cantidad debe ser un número entero.")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")

# Función para limpiar el formulario
def limpiar_campos():
    entry_codigo.delete(0, ttk_lib.END)
    entry_cantidad.delete(0, ttk_lib.END)
    entry_nombre.delete(0, ttk_lib.END)
    entry_marca.delete(0, ttk_lib.END)
    entry_descripcion.delete(0, ttk_lib.END)
    entry_observaciones.delete(0, ttk_lib.END)
    entry_responsable.delete(0, ttk_lib.END)
    combo_estado.set('')
    combo_area.set('')

# Lista oficial de áreas y módulos
AREAS_ONG = [
    "Cocina General (Personal y Alimentos Jóvenes)",
    "Cocina Cursos (Repostería y Parrilla)",
    "Cocina Salud (Personal de Salud)",
    "Salud (Clínica, Farmacia, Dental, etc.)",
    "Liceo",
    "Módulo Uñas Acrílicas",
    "Módulo Maquillaje",
    "Módulo Costura",
    "Administración"
]

# Función para cargar y filtrar datos en la tabla general
def actualizar_tabla(filtro_area=None):
    for row in tree.get_children():
        tree.delete(row)

    conexion = sqlite3.connect('inventario_ong.db')
    cursor = conexion.cursor()

    if filtro_area and filtro_area != "Todas las Áreas":
        cursor.execute("SELECT id, codigo, cantidad, nombre, marca, estado, area, responsable FROM inventario WHERE area = ?", (filtro_area,))
    else:
        cursor.execute("SELECT id, codigo, cantidad, nombre, marca, estado, area, responsable FROM inventario")

    registros = cursor.fetchall()
    conexion.close()

    for reg in registros:
        tree.insert("", ttk_lib.END, values=reg)

def filtrar_por_area(event):
    area_seleccionada = combo_filtro_area.get()
    actualizar_tabla(area_seleccionada)

# --- FUNCIONES PARA TARJETAS DE RESPONSABILIDAD ---
def obtener_responsables():
    conexion = sqlite3.connect('inventario_ong.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT DISTINCT responsable FROM inventario WHERE responsable IS NOT NULL AND responsable != ''")
    res = [row[0] for row in cursor.fetchall()]
    conexion.close()
    return res

def actualizar_lista_responsables():
    lista = obtener_responsables()
    combo_responsable['values'] = lista

def generar_tarjeta_responsabilidad(event=None):
    responsable_elegido = combo_responsable.get()
    if not responsable_elegido:
        messagebox.showwarning("Aviso", "Por favor selecciona un responsable.")
        return

    # Limpiar cuadro de texto de la tarjeta
    texto_tarjeta.delete("1.0", ttk_lib.END)

    conexion = sqlite3.connect('inventario_ong.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT codigo, cantidad, nombre, marca, estado, area, observaciones FROM inventario WHERE responsable = ?", (responsable_elegido,))
    bienes = cursor.fetchall()
    conexion.close()

    # Redactar el reporte formal
    reporte = f"==================================================\n"
    reporte += f"       TARJETA DE RESPONSABILIDAD DE BIENES       \n"
    reporte += f"==================================================\n"
    reporte += f"Responsable: {responsable_elegido}\n"
    reporte += f"Fecha de emisión: Generado por el Sistema\n"
    reporte += f"--------------------------------------------------\n\n"
    reporte += f"Los siguientes bienes se encuentran bajo la custodia y responsabilidad del colaborador:\n\n"

    if not bienes:
        reporte += "No hay bienes registrados bajo este responsable.\n"
    else:
        contador = 1
        for b in bienes:
            codigo, cantidad, nombre, marca, estado, area, observaciones = b
            reporte += f"{contador}. [{cantidad}] {nombre}\n"
            reporte += f"   - Marca: {marca if marca else 'N/A'}\n"
            reporte += f"   - Código: {codigo if codigo else 'Sin código'}\n"
            reporte += f"   - Estado: {estado if estado else 'N/A'}\n"
            reporte += f"   - Área: {area}\n"
            if observaciones:
                reporte += f"   - Obs: {observaciones}\n"
            reporte += f"   ----------------------------------------------\n"
            contador += 1

    reporte += f"\n\n____________________________________\n"
    reporte += f"Firma de Recibido / Conformidad del Encargado\n"

    texto_tarjeta.insert(ttk_lib.END, reporte)

def guardar_tarjeta_como_txt():
    responsable_elegido = combo_responsable.get()
    contenido = texto_tarjeta.get("1.0", ttk_lib.END).strip()
    if not contenido or not responsable_elegido:
        messagebox.showwarning("Aviso", "Primero genera una tarjeta para poder guardarla.")
        return

    nombre_archivo = f"Tarjeta_{responsable_elegido.replace(' ', '_')}.txt"
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        messagebox.showinfo("Éxito", f"¡Tarjeta guardada exitosamente como '{nombre_archivo}' en tu carpeta!")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")


# --- VENTANA PRINCIPAL Y PESTAÑAS ---
inicializar_base_datos()

root = ttk_lib.Tk()
root.title("Sistema de Inventario - ONG")
root.geometry("950x700")
root.config(bg="#f0f2f5")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# PESTAÑA 1: REGISTRO
pestana_registro = ttk.Frame(notebook)
notebook.add(pestana_registro, text="Registrar Objeto")

ttk_lib.Label(pestana_registro, text="Registro de Mobiliario y Equipo", font=("Arial", 14, "bold"), fg="#333").pack(pady=10)

marco_form = ttk_lib.Frame(pestana_registro, bg="#f0f2f5")
marco_form.pack(pady=5)

def crear_campo(marco, label_texto, fila):
    label = ttk_lib.Label(marco, text=label_texto, font=("Arial", 10, "bold"), bg="#f0f2f5")
    label.grid(row=fila, column=0, sticky="w", pady=4, padx=5)
    entry = ttk_lib.Entry(marco, font=("Arial", 10), width=40)
    entry.grid(row=fila, column=1, pady=4, padx=5)
    return entry

entry_codigo = crear_campo(marco_form, "Código (opcional):", 0)
entry_cantidad = crear_campo(marco_form, "Cantidad:", 1)
entry_nombre = crear_campo(marco_form, "Nombre del Objeto:", 2)
entry_marca = crear_campo(marco_form, "Marca:", 3)
entry_descripcion = crear_campo(marco_form, "Descripción:", 4)
entry_observaciones = crear_campo(marco_form, "Observaciones:", 5)

ttk_lib.Label(marco_form, text="Estado:", font=("Arial", 10, "bold"), bg="#f0f2f5").grid(row=6, column=0, sticky="w", pady=4, padx=5)
combo_estado = ttk.Combobox(marco_form, values=["Nuevo", "En uso", "Bueno", "Dañado / En reparación", "Obsoleto"], width=38, state="readonly")
combo_estado.grid(row=6, column=1, pady=4, padx=5)

ttk_lib.Label(marco_form, text="Área / Módulo:", font=("Arial", 10, "bold"), bg="#f0f2f5").grid(row=7, column=0, sticky="w", pady=4, padx=5)
combo_area = ttk.Combobox(marco_form, values=AREAS_ONG, width=38, state="readonly")
combo_area.grid(row=7, column=1, pady=4, padx=5)

entry_responsable = crear_campo(marco_form, "Responsable (Tarjeta):", 8)

btn_guardar = ttk_lib.Button(pestana_registro, text="Guardar en el Inventario", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", command=guardar_objeto, width=25, height=2)
btn_guardar.pack(pady=15)


# PESTAÑA 2: CONSULTAR / VER INVENTARIO
pestana_ver = ttk.Frame(notebook)
notebook.add(pestana_ver, text="Ver Inventario y Filtros")

marco_controles = ttk_lib.Frame(pestana_ver, pady=10)
marco_controles.pack(fill="x", padx=10)

ttk_lib.Label(marco_controles, text="Filtrar por Área:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
opciones_filtro = ["Todas las Áreas"] + AREAS_ONG
combo_filtro_area = ttk.Combobox(marco_controles, values=opciones_filtro, width=30, state="readonly")
combo_filtro_area.pack(side="left", padx=5)
combo_filtro_area.set("Todas las Áreas")
combo_filtro_area.bind("<<ComboboxSelected>>", filtrar_por_area)

btn_actualizar = ttk_lib.Button(marco_controles, text="Recargar Tabla", command=lambda: actualizar_tabla("Todas las Áreas"), bg="#008CBA", fg="white", font=("Arial", 9, "bold"))
btn_actualizar.pack(side="left", padx=10)

marco_tabla = ttk_lib.Frame(pestana_ver)
marco_tabla.pack(fill="both", expand=True, padx=10, pady=10)

columnas = ("ID", "Código", "Cant", "Nombre", "Marca", "Estado", "Área", "Responsable")
tree = ttk.Treeview(marco_tabla, columns=columnas, show="headings", height=22)

for col in columnas:
    tree.heading(col, text=col)
    tree.column(col, width=95, anchor="center")

tree.column("ID", width=40)
tree.column("Nombre", width=150)

scrollbar = ttk.Scrollbar(marco_tabla, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

actualizar_tabla()


# PESTAÑA 3: TARJETAS DE RESPONSABILIDAD
pestana_tarjetas = ttk.Frame(notebook)
notebook.add(pestana_tarjetas, text="Tarjeta de Responsabilidad")

marco_sup_tarjeta = ttk_lib.Frame(pestana_tarjetas, pady=15)
marco_sup_tarjeta.pack(fill="x", padx=15)

ttk_lib.Label(marco_sup_tarjeta, text="Seleccionar Responsable:", font=("Arial", 10, "bold")).pack(side="left", padx=5)

combo_responsable = ttk.Combobox(marco_sup_tarjeta, width=30, state="readonly")
combo_responsable.pack(side="left", padx=5)
combo_responsable.bind("<<ComboboxSelected>>", generar_tarjeta_responsabilidad)

btn_generar_tarjeta = ttk_lib.Button(marco_sup_tarjeta, text="Generar Tarjeta", command=generar_tarjeta_responsabilidad, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"))
btn_generar_tarjeta.pack(side="left", padx=10)

btn_guardar_txt = ttk_lib.Button(marco_sup_tarjeta, text="Guardar Reporte (.txt)", command=guardar_tarjeta_como_txt, bg="#ff9800", fg="white", font=("Arial", 9, "bold"))
btn_guardar_txt.pack(side="left", padx=10)

# Cuadro de texto para visualizar la tarjeta formal
marco_texto = ttk_lib.Frame(pestana_tarjetas)
marco_texto.pack(fill="both", expand=True, padx=15, pady=5)

texto_tarjeta = ttk_lib.Text(marco_texto, font=("Courier", 10), bg="#fff", fg="#000")
scrollbar_tarjeta = ttk.Scrollbar(marco_texto, orient="vertical", command=texto_tarjeta.yview)
texto_tarjeta.configure(yscrollcommand=scrollbar_tarjeta.set)

texto_tarjeta.pack(side="left", fill="both", expand=True)
scrollbar_tarjeta.pack(side="right", fill="y")

# Cargar los responsables iniciales al abrir
actualizar_lista_responsables()

root.mainloop()