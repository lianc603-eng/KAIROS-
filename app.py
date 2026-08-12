import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Kairós MKT - Control & Calendarios", layout="wide", page_icon="⚡")

st.title("⚡ Kairós MKT - Centro de Control")

# --- BASE DE DATOS LOCAL (SQLITE) ---
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
            fecha_pago TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fin TEXT NOT NULL,
            estado TEXT DEFAULT 'Activo'
        )
    ''')
    # Tabla de eventos
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

def guardar_cliente(nombre, paquete, fecha_pago, inicio, fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO clientes (nombre, paquete, fecha_pago, inicio, fin, estado) VALUES (?, ?, ?, ?, ?, 'Activo')",
              (nombre, paquete, str(fecha_pago), str(inicio), str(fin)))
    
    # Eventos iniciales
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fecha_pago), nombre, "Pago Recibido", "N/A", f"Pago inicial del paquete {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(inicio), nombre, "Inicio de Servicio", "N/A", f"Inicio de ciclo: {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fin), nombre, "Fin / Renovación", "N/A", f"Corte del periodo: {paquete}"))
    
    conn.commit()
    conn.close()

def renovar_cliente(id_cliente, nombre, paquete, nueva_fecha_pago):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Nuevo ciclo: inicia el día de pago y dura 30 días
    nuevo_inicio = nueva_fecha_pago
    nuevo_fin = nueva_fecha_pago + timedelta(days=30)
    
    # Actualizar ficha del cliente
    c.execute('''
        UPDATE clientes 
        SET fecha_pago = ?, inicio = ?, fin = ?, estado = 'Activo' 
        WHERE id = ?
    ''', (str(nueva_fecha_pago), str(nuevo_inicio), str(nuevo_fin), id_cliente))
    
    # Registrar los nuevos hitos en el calendario
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(nueva_fecha_pago), nombre, "Pago Recibido", "N/A", f"Renovación de pago: {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(nuevo_inicio), nombre, "Inicio de Servicio", "N/A", f"Nuevo ciclo renovado: {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(nuevo_fin), nombre, "Fin / Renovación", "N/A", f"Corte de ciclo renovado: {paquete}"))
    
    conn.commit()
    conn.close()

def guardar_evento(fecha, cliente, tipo, formato, detalle):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fecha), cliente, tipo, formato, detalle))
    conn.commit()
    conn.close()

# Cargar datos
df_clientes = get_clientes()
df_eventos = get_eventos()

PAQUETES_KAIRÓS = {
    "Actividad Constante": {"precio": 2500, "posts": 10, "reels": 4, "historias": 4, "total": 18},
    "Impulso": {"precio": 3400, "posts": 13, "reels": 6, "historias": 7, "total": 26},
    "Dominio Total": {"precio": 4100, "posts": 16, "reels": 9, "historias": 10, "total": 35}
}

# --- NAVEGACIÓN ---
modo = st.sidebar.radio(
    "Navegación", 
    ["📅 Calendario Agencia (Kairós)", "👥 Calendario por Cliente", "🔄 Renovar Servicio", "📦 Catálogo de Paquetes", "➕ Registrar Cliente / Evento"]
)

# ----------------------------------------------------
# VISTA 1: CALENDARIO GLOBAL
# ----------------------------------------------------
if modo == "📅 Calendario Agencia (Kairós)":
    st.header("🗓️ Vista General de Operaciones - Kairós MKT")
    st.caption("Consolidado de pagos, grabaciones, reuniones, entregas y renovaciones.")
    
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
                "tipo": "Evento",
                "formato": "Formato",
                "detalle": "Detalle / Descripción"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay eventos registrados en la base de datos todavía.")

# ----------------------------------------------------
# VISTA 2: CALENDARIO POR CLIENTE & RENOVACIÓN RÁPIDA
# ----------------------------------------------------
elif modo == "👥 Calendario por Cliente":
    st.header("👤 Control y Avance de Entregables por Cliente")
    
    if not df_clientes.empty:
        nombres_clientes = df_clientes["nombre"].tolist()
        cliente_sel = st.selectbox("Selecciona un Cliente", nombres_clientes)
        
        info_c = df_clientes[df_clientes["nombre"] == cliente_sel].iloc[0]
        pkg_info = PAQUETES_KAIRÓS.get(info_c["paquete"], {"precio": 0, "posts": 0, "reels": 0, "historias": 0, "total": 0})
        
        # Ficha del servicio
        st.subheader(f"📌 Estado del Servicio: {cliente_sel}")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Paquete", info_c["paquete"])
        col2.metric("Inversión", f"${pkg_info['precio']:,} MXN")
        col3.metric("Último Pago", str(info_c["fecha_pago"]))
        col4.metric("Inicio Ciclo", str(info_c["inicio"]))
        col5.metric("Próximo Corte", str(info_c["fin"]))
        
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
# VISTA 3: RENOVACIÓN DE SERVICIO
# ----------------------------------------------------
elif modo == "🔄 Renovar Servicio":
    st.header("🔄 Renovación de Mes / Contrato de Clientes")
    st.caption("Registra el nuevo pago y extiende automáticamente el periodo del cliente por 30 días más.")
    
    if not df_clientes.empty:
        with st.form("form_renovar"):
            client_to_renew = st.selectbox("Selecciona el Cliente que Renovó", df_clientes["nombre"].tolist())
            fecha_nuevo_pago = st.date_input("Fecha en que realizaró el pago", value=date.today())
            
            info_ren = df_clientes[df_clientes["nombre"] == client_to_renew].iloc[0]
            st.info(f"El cliente actualmente tiene contratado el paquete **{info_ren['paquete']}**.")
            
            if st.form_submit_button("Confirmar Renovación (+30 Días)"):
                renovar_cliente(info_ren["id"], client_to_renew, info_ren["paquete"], fecha_nuevo_pago)
                st.success(f"¡Servicio de '{client_to_renew}' renovado con éxito! Se agendó el nuevo ciclo a partir del {fecha_nuevo_pago.strftime('%d/%m/%Y')}.")
                st.rerun()
    else:
        st.warning("No hay clientes registrados en la base de datos.")

# ----------------------------------------------------
# VISTA 4: CATÁLOGO DE PAQUETES
# ----------------------------------------------------
elif modo == "📦 Catálogo de Paquetes":
    st.header("📦 Paquetes Oficiales Kairós MKT")
    cols = st.columns(len(PAQUETES_KAIRÓS))
    for i, (nombre, datos) in enumerate(PAQUETES_KAIRÓS.items()):
        with cols[i]:
            st.subheader(nombre)
            st.markdown(f"### **${datos['precio']:,} MXN** / mes")
            st.write(f"🖼️ **{datos['posts']}** Post Gráficos")
            st.write(f"🎬 **{datos['reels']}** Reels")
            st.write(f"📲 **{datos['historias']}** Historias")
            st.info(f"**Total**: {datos['total']} piezas al mes")

# ----------------------------------------------------
# VISTA 5: REGISTRO INICIAL
# ----------------------------------------------------
elif modo == "➕ Registrar Cliente / Evento":
    st.header("⚙️ Gestión de Datos y Agendamiento")
    tab1, tab2 = st.tabs(["➕ Agregar Evento / Publicación", "👤 Registrar Nuevo Cliente"])
    
    with tab1:
        st.subheader("Agendar Evento o Publicación")
        if not df_clientes.empty:
            with st.form("form_evento"):
                cliente_ev = st.selectbox("Cliente", df_clientes["nombre"].tolist())
                tipo_ev = st.selectbox("Tipo de Evento", ["Publicación", "Día de Grabación", "Reunión con Cliente", "Pago Recibido", "Inicio de Servicio", "Fin / Renovación"])
                formato_ev = st.selectbox("Formato", ["N/A", "Post Gráfico", "Reel", "Historia"])
                fecha_ev = st.date_input("Fecha", value=date.today())
                detalle_ev = st.text_input("Detalle / Copy / Tema de la sesión")
                
                if st.form_submit_button("Guardar Actividad"):
                    guardar_evento(fecha_ev, cliente_ev, tipo_ev, formato_ev, detalle_ev)
                    st.success("¡Actividad guardada correctamente!")
                    st.rerun()
        else:
            st.warning("Debes registrar al menos un cliente antes de agendar actividades.")

    with tab2:
        st.subheader("Registrar Cliente")
        with st.form("form_cliente"):
            nombre_c = st.text_input("Nombre de la Marca / Empresa")
            paquete_c = st.selectbox("Paquete Contratado", list(PAQUETES_KAIRÓS.keys()))
            f_pago = st.date_input("Día que se recibió el Pago", value=date.today())
            
            # Por defecto el inicio de servicio es el día de pago y termina en 30 días
            f_inicio = f_pago
            f_fin = f_pago + timedelta(days=30)
            
            st.caption(f"📅 Con esta fecha de pago, el ciclo iniciará el **{f_inicio.strftime('%d/%m/%Y')}** y la fecha de corte/renovación será el **{f_fin.strftime('%d/%m/%Y')}**.")
            
            if st.form_submit_button("Registrar Cliente"):
                if nombre_c.strip():
                    guardar_cliente(nombre_c, paquete_c, f_pago, f_inicio, f_fin)
                    st.success(f"Cliente '{nombre_c}' registrado correctamente con fecha de pago {f_pago.strftime('%d/%m/%Y')}.")
                    st.rerun()
                else:
                    st.error("Por favor ingresa un nombre válido para la marca.")
