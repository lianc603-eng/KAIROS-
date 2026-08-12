import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta

st.set_page_config(page_title="Kairós MKT - Control & Calendarios", layout="wide", page_icon="⚡")

st.title("⚡ Kairós MKT - Centro de Control")

# --- CONEXIÓN Y CONFIGURACIÓN DE BASE DE DATOS LOCAL (SQLITE) ---
DB_NAME = "kairos.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de clientes
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            paquete TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fin TEXT NOT NULL
        )
    ''')
    # Tabla de eventos/actividades
    c.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            cliente TEXT NOT NULL,
            tipo TEXT NOT NULL,
            formato TEXT NOT NULL,
            detalle TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Inicializar las tablas al cargar la app
init_db()

def get_clientes():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    return df

def get_eventos():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM eventos", conn)
    conn.close()
    return df

def guardar_cliente(nombre, paquete, inicio, fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO clientes (nombre, paquete, inicio, fin) VALUES (?, ?, ?, ?)",
              (nombre, paquete, str(inicio), str(fin)))
    
    # Eventos automáticos de inicio y fin de ciclo
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(inicio), nombre, "Inicio de Servicio", "N/A", f"Inicio de ciclo: Paquete {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fin), nombre, "Fin de Servicio", "N/A", f"Fin de ciclo: Paquete {paquete}"))
    
    conn.commit()
    conn.close()

def guardar_evento(fecha, cliente, tipo, formato, detalle):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fecha), cliente, tipo, formato, detalle))
    conn.commit()
    conn.close()

# Cargar datos desde SQLite
df_clientes = get_clientes()
df_eventos = get_eventos()

# --- DICCIONARIO DE PAQUETES DE KAIRÓS MKT ---
PAQUETES_KAIROS = {
    "Actividad Constante": {"precio": 2500, "posts": 10, "reels": 4, "historias": 4, "total": 18},
    "Impulso": {"precio": 3400, "posts": 13, "reels": 6, "historias": 7, "total": 26},
    "Dominio Total": {"precio": 4100, "posts": 16, "reels": 9, "historias": 10, "total": 35}
}

# --- NAVEGACIÓN ---
modo = st.sidebar.radio(
    "Navegación", 
    ["📅 Calendario Agencia (Kairós)", "👥 Calendario por Cliente", "📦 Catálogo de Paquetes", "➕ Registrar Cliente / Evento"]
)

# ----------------------------------------------------
# VISTA 1: CALENDARIO GLOBAL DE KAIRÓS
# ----------------------------------------------------
if modo == "📅 Calendario Agencia (Kairós)":
    st.header("🗓️ Vista General de Operaciones - Kairós MKT")
    st.caption("Consolidado de días de grabación, reuniones, publicaciones e inicios/cierres de contrato.")
    
    if not df_eventos.empty:
        col1, col2 = st.columns(2)
        with col1:
            tipo_filtro = st.multiselect("Filtrar por Tipo de Evento", options=df_eventos["tipo"].unique(), default=df_eventos["tipo"].unique())
        with col2:
            cliente_filtro = st.multiselect("Filtrar por Cliente", options=df_eventos["cliente"].unique(), default=df_eventos["cliente"].unique())
            
        df_filtrado = df_eventos[
            (df_eventos["tipo"].isin(tipo_filtro)) & 
            (df_eventos["cliente"].isin(cliente_filtro))
        ].sort_values("fecha")
        
        st.dataframe(
            df_filtrado[["fecha", "cliente", "tipo", "formato", "detalle"]], 
            column_config={
                "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "cliente": "Cliente",
                "tipo": "Tipo de Evento",
                "formato": "Formato",
                "detalle": "Detalle / Descripción"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay eventos registrados en la base de datos todavía.")

# ----------------------------------------------------
# VISTA 2: CALENDARIO ESPECÍFICO POR CLIENTE
# ----------------------------------------------------
elif modo == "👥 Calendario por Cliente":
    st.header("👤 Control y Avance de Entregables por Cliente")
    
    if not df_clientes.empty:
        nombres_clientes = df_clientes["nombre"].tolist()
        cliente_sel = st.selectbox("Selecciona un Cliente", nombres_clientes)
        
        info_c = df_clientes[df_clientes["nombre"] == cliente_sel].iloc[0]
        pkg_info = PAQUETES_KAIROS.get(info_c["paquete"], {"precio": 0, "posts": 0, "reels": 0, "historias": 0, "total": 0})
        
        # Ficha del servicio
        st.subheader(f"📌 Estado del Servicio: {cliente_sel}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Paquete", info_c["paquete"])
        col2.metric("Inversión", f"${pkg_info['precio']:,} MXN")
        col3.metric("Inicio de Ciclo", str(info_c["inicio"]))
        col4.metric("Fin de Ciclo", str(info_c["fin"]))
        
        # Conteo de Entregables
        ev_cliente = df_eventos[(df_eventos["cliente"] == cliente_sel) & (df_eventos["tipo"] == "Publicación")] if not df_eventos.empty else pd.DataFrame()
        posts_p = len(ev_cliente[ev_cliente["formato"] == "Post Gráfico"]) if not ev_cliente.empty else 0
        reels_p = len(ev_cliente[ev_cliente["formato"] == "Reel"]) if not ev_cliente.empty else 0
        hist_p = len(ev_cliente[ev_cliente["formato"] == "Historia"]) if not ev_cliente.empty else 0
        
        st.markdown("#### 📊 Progreso del Paquete Contratado")
        m1, m2, m3 = st.columns(3)
        m1.metric("Post Gráficos", f"{posts_p} / {pkg_info['posts']}")
        m2.metric("Reels", f"{reels_p} / {pkg_info['reels']}")
        m3.metric("Historias", f"{hist_p} / {pkg_info['historias']}")
        
        st.divider()
        st.subheader("🗓️ Cronograma de Actividades")
        df_c_ev = df_eventos[df_eventos["cliente"] == cliente_sel].sort_values("fecha") if not df_eventos.empty else pd.DataFrame()
        
        st.dataframe(
            df_c_ev[["fecha", "tipo", "formato", "detalle"]],
            column_config={
                "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "tipo": "Categoría",
                "formato": "Formato",
                "detalle": "Descripción de la Actividad / Contenido"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Primero registra un cliente en la sección 'Registrar Cliente / Evento'.")

# ----------------------------------------------------
# VISTA 3: CATÁLOGO DE PAQUETES
# ----------------------------------------------------
elif modo == "📦 Catálogo de Paquetes":
    st.header("📦 Paquetes Oficiales Kairós MKT")
    st.caption("Estructura de precios y entregables mensuales de la agencia.")
    
    cols = st.columns(len(PAQUETES_KAIROS))
    for i, (nombre, datos) in enumerate(PAQUETES_KAIROS.items()):
        with cols[i]:
            st.subheader(nombre)
            st.markdown(f"### **${datos['precio']:,} MXN** / mes")
            st.write(f"🖼️ **{datos['posts']}** Post Gráficos")
            st.write(f"🎬 **{datos['reels']}** Reels")
            st.write(f"📲 **{datos['historias']}** Historias")
            st.info(f"**Total**: {datos['total']} piezas al mes")

# ----------------------------------------------------
# VISTA 4: REGISTRO Y GUARDADO DIRECTO
# ----------------------------------------------------
elif modo == "➕ Registrar Cliente / Evento":
    st.header("⚙️ Gestión de Datos y Agendamiento")
    tab1, tab2 = st.tabs(["➕ Agregar Evento / Publicación", "👤 Registrar Nuevo Cliente"])
    
    with tab1:
        st.subheader("Agendar Evento o Publicación")
        if not df_clientes.empty:
            with st.form("form_evento"):
                cliente_ev = st.selectbox("Cliente", df_clientes["nombre"].tolist())
                tipo_ev = st.selectbox("Tipo de Evento", ["Publicación", "Día de Grabación", "Reunión con Cliente", "Inicio de Servicio", "Fin de Servicio"])
                formato_ev = st.selectbox("Formato", ["N/A", "Post Gráfico", "Reel", "Historia"])
                fecha_ev = st.date_input("Fecha", value=date.today())
                detalle_ev = st.text_input("Detalle / Copy / Tema de la sesión")
                
                if st.form_submit_button("Guardar Actividad"):
                    guardar_evento(fecha_ev, cliente_ev, tipo_ev, formato_ev, detalle_ev)
                    st.success("¡Actividad guardada correctamente en la base de datos!")
                    st.rerun()
        else:
            st.warning("Debes registrar al menos un cliente antes de agendar actividades.")

    with tab2:
        st.subheader("Registrar Cliente")
        with st.form("form_cliente"):
            nombre_c = st.text_input("Nombre de la Marca / Empresa")
            paquete_c = st.selectbox("Paquete Contratado", list(PAQUETES_KAIROS.keys()))
            f_inicio = st.date_input("Fecha Inicio de Servicio", value=date.today())
            f_fin = st.date_input("Fecha Fin de Servicio", value=date.today() + timedelta(days=30))
            
            if st.form_submit_button("Registrar Cliente"):
                if nombre_c.strip():
                    guardar_cliente(nombre_c, paquete_c, f_inicio, f_fin)
                    st.success(f"Cliente '{nombre_c}' registrado con éxito.")
                    st.rerun()
                else:
                    st.error("Por favor ingresa un nombre válido para la marca.")
