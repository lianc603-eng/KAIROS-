import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Kairós MKT - Control & Calendarios", layout="wide", page_icon="⚡")

st.title("⚡ Kairós MKT - Centro de Control")

DB_NAME = "kairos.db"

# --- INICIALIZACIÓN DE BASE DE DATOS CON MIGRACIÓN DE COLUMNAS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Crear tabla de clientes si no existe
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            paquete TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fin TEXT NOT NULL
        )
    ''')
    
    # Migrar columnas de versiones anteriores si es necesario
    try:
        c.execute("ALTER TABLE clientes ADD COLUMN fecha_pago TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE clientes ADD COLUMN estado TEXT DEFAULT 'Activo'")
    except sqlite3.OperationalError:
        pass

    # Crear tabla de eventos si no existe
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

# --- FUNCIONES DE CONSULTA Y ESCRITURA ---
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
    
    # Eventos iniciales del ciclo
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fecha_pago), nombre, "Pago Recibido", "N/A", f"Pago inicial - Paquete {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(inicio), nombre, "Inicio de Servicio", "N/A", f"Inicio de ciclo: {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fin), nombre, "Fin de Ciclo", "N/A", f"Corte de ciclo (Pendiente renovación): {paquete}"))
    
    conn.commit()
    conn.close()

def renovar_cliente_manual(id_cliente, nombre, paquete, fecha_nuevo_pago):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    nuevo_inicio = fecha_nuevo_pago
    nuevo_fin = fecha_nuevo_pago + timedelta(days=30)
    
    c.execute('''
        UPDATE clientes 
        SET fecha_pago = ?, inicio = ?, fin = ?, estado = 'Activo' 
        WHERE id = ?
    ''', (str(fecha_nuevo_pago), str(nuevo_inicio), str(nuevo_fin), id_cliente))
    
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fecha_nuevo_pago), nombre, "Pago Recibido", "N/A", f"Renovación confirmada - Paquete {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(nuevo_inicio), nombre, "Inicio de Servicio", "N/A", f"Nuevo ciclo iniciado: {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(nuevo_fin), nombre, "Fin de Ciclo", "N/A", f"Corte de nuevo ciclo: {paquete}"))
    
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

# --- CATÁLOGO OFICIAL KAIRÓS MKT ---
PAQUETES_KAIROS = {
    "Actividad Constante": {"precio": 2500, "posts": 10, "reels": 4, "historias": 4, "total": 18},
    "Impulso": {"precio": 3400, "posts": 13, "reels": 6, "historias": 7, "total": 26},
    "Dominio Total": {"precio": 4100, "posts": 16, "reels": 9, "historias": 10, "total": 35}
}

# --- NAVEGACIÓN ---
modo = st.sidebar.radio(
    "Navegación", 
    ["📅 Calendario Agencia (Kairós)", "👥 Calendario por Cliente", "🔄 Gestión de Renovaciones", "📦 Catálogo de Paquetes", "➕ Registrar Cliente / Evento"]
)

# ----------------------------------------------------
# VISTA 1: CALENDARIO GLOBAL
# ----------------------------------------------------
if modo == "📅 Calendario Agencia (Kairós)":
    st.header("🗓️ Vista General de Operaciones - Kairós MKT")
    st.caption("Consolidado de pagos, grabaciones, reuniones, entregas y cortes de ciclo.")
    
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
# VISTA 2: CALENDARIO POR CLIENTE
# ----------------------------------------------------
elif modo == "👥 Calendario por Cliente":
    st.header("👤 Control y Avance de Entregables por Cliente")
    
    if not df_clientes.empty:
        nombres_clientes = df_clientes["nombre"].tolist()
        cliente_sel = st.selectbox("Selecciona un Cliente", nombres_clientes)
        
        info_c = df_clientes[df_clientes["nombre"] == cliente_sel].iloc[0]
        pkg_info = PAQUETES_KAIROS.get(info_c["paquete"], {"precio": 0, "posts": 0, "reels": 0, "historias": 0, "total": 0})
        
        # Verificar vencimiento
        fecha_fin_str = str(info_c["fin"])
        if fecha_fin_str:
            try:
                fecha_fin_dt = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
                if date.today() > fecha_fin_dt:
                    st.warning("⚠️ **ATENCIÓN**: El ciclo contratado ha finalizado. Esperando confirmación de pago para renovar.")
            except ValueError:
                pass

        st.subheader(f"📌 Estado del Servicio: {cliente_sel}")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Paquete", info_c["paquete"])
        col2.metric("Inversión", f"${pkg_info['precio']:,} MXN")
        col3.metric("Último Pago", str(info_c["fecha_pago"]))
        col4.metric("Inicio Ciclo", str(info_c["inicio"]))
        col5.metric("Fecha Corte", str(info_c["fin"]))
        
        # Métricas de entregables
        ev_cliente = df_eventos[(df_eventos["cliente"] == cliente_sel) & (df_eventos["tipo"] == "Publicación")] if not df_eventos.empty else pd.DataFrame()
        posts_p = len(ev_cliente[ev_cliente["formato"] == "Post Gráfico"]) if not ev_cliente.empty else 0
        reels_p = len(ev_cliente[ev_cliente["formato"] == "Reel"]) if not ev_cliente.empty else 0
        hist_p = len(ev_cliente[ev_cliente["formato"] == "Historia"]) if not ev_cliente.empty else 0
        
        st.markdown("#### 📊 Progreso de Entregables de este Ciclo")
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
                "detalle": "Descripción"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Primero registra un cliente en la sección 'Registrar Cliente / Evento'.")

# ----------------------------------------------------
# VISTA 3: RENOVACIÓN MANUAL
# ----------------------------------------------------
elif modo == "🔄 Gestión de Renovaciones":
    st.header("🔄 Renovación Manual de Clientes")
    st.caption("Usa esta sección únicamente cuando el cliente haya confirmado y realizado su pago correspondiente.")
    
    if not df_clientes.empty:
        with st.form("form_renovar"):
            client_to_renew = st.selectbox("Selecciona el Cliente a Renovar", df_clientes["nombre"].tolist())
            fecha_nuevo_pago = st.date_input("Fecha en que se confirmó el pago", value=date.today())
            
            info_ren = df_clientes[df_clientes["nombre"] == client_to_renew].iloc[0]
            st.info(f"Cliente: **{client_to_renew}** | Paquete: **{info_ren['paquete']}** | Fecha de corte actual: **{info_ren['fin']}**")
            
            if st.form_submit_button("Confirmar Pago y Renovar (+30 Días)"):
                renovar_cliente_manual(info_ren["id"], client_to_renew, info_ren["paquete"], fecha_nuevo_pago)
                st.success(f"¡Servicio de '{client_to_renew}' renovado manualmente! Nuevo ciclo extendido a partir del {fecha_nuevo_pago.strftime('%d/%m/%Y')}.")
                st.rerun()
    else:
        st.warning("No hay clientes registrados en la base de datos.")

# ----------------------------------------------------
# VISTA 4: CATÁLOGO DE PAQUETES
# ----------------------------------------------------
elif modo == "📦 Catálogo de Paquetes":
    st.header("📦 Paquetes Oficiales Kairós MKT")
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
# VISTA 5: REGISTRO DE CLIENTES Y EVENTOS
# ----------------------------------------------------
elif modo == "➕ Registrar Cliente / Evento":
    st.header("⚙️ Gestión de Datos y Agendamiento")
    tab1, tab2 = st.tabs(["➕ Agregar Evento / Publicación", "👤 Registrar Nuevo Cliente"])
    
    with tab1:
        st.subheader("Agendar Evento o Publicación")
        if not df_clientes.empty:
            with st.form("form_evento"):
                cliente_ev = st.selectbox("Cliente", df_clientes["nombre"].tolist())
                tipo_ev = st.selectbox("Tipo de Evento", ["Publicación", "Día de Grabación", "Reunión con Cliente", "Pago Recibido", "Inicio de Servicio", "Fin de Ciclo"])
                formato_ev = st.selectbox("Formato", ["N/A", "Post Gráfico", "Reel", "Historia"])
                fecha_ev = st.date_input("Fecha", value=date.today())
                detalle_ev = st.text_input("Detalle / Copy / Tema")
                
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
            paquete_c = st.selectbox("Paquete Contratado", list(PAQUETES_KAIROS.keys()))
            f_pago = st.date_input("Día que se recibió el Pago", value=date.today())
            
            f_inicio = f_pago
            f_fin = f_pago + timedelta(days=30)
            
            st.caption(f"📅 Ciclo inicial: Del **{f_inicio.strftime('%d/%m/%Y')}** al **{f_fin.strftime('%d/%m/%Y')}**.")
            
            if st.form_submit_button("Registrar Cliente"):
                if nombre_c.strip():
                    guardar_cliente(nombre_c, paquete_c, f_pago, f_inicio, f_fin)
                    st.success(f"Cliente '{nombre_c}' registrado correctamente.")
                    st.rerun()
                else:
                    st.error("Por favor ingresa un nombre válido para la marca.")
