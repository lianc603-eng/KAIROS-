import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title="Kairós MKT - Control & Calendarios", layout="wide", page_icon="⚡")

st.title("⚡ Kairós MKT - Centro de Control")

DB_NAME = "kairos.db"

# --- BASE DE DATOS Y MIGRACIÓN ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            paquete TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fin TEXT NOT NULL
        )
    ''')
    try:
        c.execute("ALTER TABLE clientes ADD COLUMN fecha_pago TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE clientes ADD COLUMN estado TEXT DEFAULT 'Activo'")
    except sqlite3.OperationalError:
        pass

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

# --- FUNCIONES DE BASE DE DATOS ---
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
    
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fecha_pago), nombre, "Pago Recibido", "N/A", f"Pago inicial - Paquete {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(inicio), nombre, "Inicio de Servicio", "N/A", f"Inicio de ciclo: {paquete}"))
    c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
              (str(fin), nombre, "Fin de Ciclo", "N/A", f"Corte de ciclo: {paquete}"))
    
    conn.commit()
    conn.close()

def renovar_cliente_manual(id_cliente, nombre, paquete, fecha_nuevo_pago):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    nuevo_inicio = fecha_nuevo_pago
    nuevo_fin = fecha_nuevo_pago + timedelta(days=30)
    
    c.execute("UPDATE clientes SET fecha_pago = ?, inicio = ?, fin = ?, estado = 'Activo' WHERE id = ?", 
              (str(fecha_nuevo_pago), str(nuevo_inicio), str(nuevo_fin), id_cliente))
    
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

def actualizar_evento(id_evento, fecha, cliente, tipo, formato, detalle):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE eventos SET fecha=?, cliente=?, tipo=?, formato=?, detalle=? WHERE id=?",
              (str(fecha), cliente, tipo, formato, detalle, id_evento))
    conn.commit()
    conn.close()

def eliminar_evento(id_evento):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM eventos WHERE id=?", (id_evento,))
    conn.commit()
    conn.close()

def agendar_plan_completo(nombre_cliente, fechas_grabacion, calendario_pubs):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    for i, f in enumerate(fechas_grabacion, 1):
        c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
                  (str(f), nombre_cliente, "Día de Grabación", "N/A", f"Sesión de rodaje #{i}"))
        
    for item in calendario_pubs:
        c.execute("INSERT INTO eventos (fecha, cliente, tipo, formato, detalle) VALUES (?, ?, ?, ?, ?)",
                  (str(item['fecha']), nombre_cliente, "Publicación", item['formato'], item['detalle']))
        
    conn.commit()
    conn.close()

# Cargar datos
df_clientes = get_clientes()
df_eventos = get_eventos()

PAQUETES_KAIROS = {
    "Actividad Constante": {"precio": 2500, "posts": 10, "reels": 4, "historias": 4, "total": 18, "sesiones": 1},
    "Impulso": {"precio": 3400, "posts": 13, "reels": 6, "historias": 7, "total": 26, "sesiones": 1},
    "Dominio Total": {"precio": 4100, "posts": 16, "reels": 9, "historias": 10, "total": 35, "sesiones": 2}
}

# --- NAVEGACIÓN ---
modo = st.sidebar.radio(
    "Navegación", 
    [
        "📊 Dashboard & Calendario Visual", 
        "👥 Calendario por Cliente", 
        "✏️ Editar / Eliminar Eventos", 
        "🔄 Gestión de Renovaciones", 
        "📦 Catálogo de Paquetes", 
        "➕ Registrar Cliente / Evento"
    ]
)

# ----------------------------------------------------
# VISTA 1: DASHBOARD & CALENDARIO VISUAL GRÁFICO
# ----------------------------------------------------
if modo == "📊 Dashboard & Calendario Visual":
    st.header("📊 Dashboard Operativo & Calendario Total - Kairós MKT")
    
    # 1. METRICAS / DASHBOARD GENERAL
    if not df_clientes.empty:
        total_clientes = len(df_clientes)
        ingresos_est = sum([PAQUETES_KAIROS.get(p, {}).get("precio", 0) for p in df_clientes["paquete"]])
        
        # Conteo de eventos este mes
        mes_actual = date.today().strftime("%Y-%m")
        df_mes = df_eventos[df_eventos["fecha"].str.startswith(mes_actual)] if not df_eventos.empty else pd.DataFrame()
        
        grabaciones_mes = len(df_mes[df_mes["tipo"] == "Día de Grabación"]) if not df_mes.empty else 0
        pubs_mes = len(df_mes[df_mes["tipo"] == "Publicación"]) if not df_mes.empty else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Clientes Activos", total_clientes)
        c2.metric("Ingresos Mensuales", f"${ingresos_est:,} MXN")
        c3.metric("Grabaciones este Mes", grabaciones_mes)
        c4.metric("Publicaciones este Mes", pubs_mes)
    else:
        st.info("Agrega tu primer cliente para ver las métricas del dashboard.")

    st.divider()
    
    # 2. CALENDARIO VISUAL
    st.subheader("🗓️ Calendario Interactivo")
    
    if not df_eventos.empty:
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            filtro_cli = st.multiselect("Filtrar por Cliente", options=df_eventos["cliente"].unique(), default=df_eventos["cliente"].unique())
        
        df_ev_filtrado = df_eventos[df_eventos["cliente"].isin(filtro_cli)]
        
        # Mapeo de colores para el Calendario Visual
        COLOR_MAP = {
            "Día de Grabación": "#ef4444",   # Rojo
            "Publicación": "#3b82f6",        # Azul
            "Pago Recibido": "#10b981",      # Verde
            "Inicio de Servicio": "#8b5cf6",  # Morado
            "Fin de Ciclo": "#f59e0b",       # Naranja
            "Reunión con Cliente": "#ec4899" # Rosa
        }
        
        calendar_events = []
        for _, row in df_ev_filtrado.iterrows():
            color = COLOR_MAP.get(row["tipo"], "#6b7280")
            titulo = f"{row['cliente']}: {row['detalle']}" if row['formato'] == 'N/A' else f"{row['cliente']} ({row['formato']}): {row['detalle']}"
            
            calendar_events.append({
                "id": str(row["id"]),
                "title": titulo,
                "start": row["fecha"],
                "end": row["fecha"],
                "color": color
            })
            
        calendar_options = {
            "editable": False,
            "selectable": True,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,listMonth"
            },
            "initialView": "dayGridMonth"
        }
        
        calendar(events=calendar_events, options=calendar_options, key="kairos_full_calendar")
        
        # Leyenda de Colores
        st.caption("🎨 **Leyenda de Colores**: 🔴 Grabación | 🔵 Publicación | 🟢 Pago Confirmado | 🟣 Inicio de Servicio | 🟠 Fin de Ciclo | 💗 Reunión")
    else:
        st.info("No hay eventos agendados para desplegar en el calendario visual.")

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
# VISTA 3: EDITAR O ELIMINAR EVENTOS
# ----------------------------------------------------
elif modo == "✏️ Editar / Eliminar Eventos":
    st.header("✏️ Modificar o Eliminar Actividades del Calendario")
    st.caption("Selecciona cualquier actividad existente para corregir sus datos o eliminarla.")
    
    if not df_eventos.empty:
        df_eventos_sorted = df_eventos.sort_values("fecha", ascending=False)
        opciones_eventos = {
            row["id"]: f"ID {row['id']} | {row['fecha']} | {row['cliente']} | {row['tipo']} - {row['detalle']}" 
            for _, row in df_eventos_sorted.iterrows()
        }
        
        id_sel = st.selectbox("Selecciona la actividad a gestionar", list(opciones_eventos.keys()), format_func=lambda x: opciones_eventos[x])
        evento_info = df_eventos[df_eventos["id"] == id_sel].iloc[0]
        
        col_ed, col_del = st.columns([2, 1])
        
        with col_ed:
            st.subheader("Modificar Datos de la Actividad")
            with st.form("form_editar_evento"):
                c_cli = st.selectbox("Cliente", df_clientes["nombre"].tolist() if not df_clientes.empty else [evento_info["cliente"]], index=df_clientes["nombre"].tolist().index(evento_info["cliente"]) if evento_info["cliente"] in df_clientes["nombre"].tolist() else 0)
                c_tipo = st.selectbox("Tipo de Evento", ["Publicación", "Día de Grabación", "Reunión con Cliente", "Pago Recibido", "Inicio de Servicio", "Fin de Ciclo"], index=["Publicación", "Día de Grabación", "Reunión con Cliente", "Pago Recibido", "Inicio de Servicio", "Fin de Ciclo"].index(evento_info["tipo"]) if evento_info["tipo"] in ["Publicación", "Día de Grabación", "Reunión con Cliente", "Pago Recibido", "Inicio de Servicio", "Fin de Ciclo"] else 0)
                c_fmt = st.selectbox("Formato", ["N/A", "Post Gráfico", "Reel", "Historia"], index=["N/A", "Post Gráfico", "Reel", "Historia"].index(evento_info["formato"]) if evento_info["formato"] in ["N/A", "Post Gráfico", "Reel", "Historia"] else 0)
                
                try:
                    f_val = datetime.strptime(str(evento_info["fecha"]), "%Y-%m-%d").date()
                except ValueError:
                    f_val = date.today()
                    
                c_fecha = st.date_input("Fecha", value=f_val)
                c_det = st.text_input("Detalle / Tema", value=str(evento_info["detalle"]))
                
                if st.form_submit_button("💾 Guardar Cambios"):
                    actualizar_evento(id_sel, c_fecha, c_cli, c_tipo, c_fmt, c_det)
                    st.success("¡Actividad actualizada correctamente!")
                    st.rerun()

        with col_del:
            st.subheader("Zona de Eliminación")
            st.warning("⚠️ Esta acción borrará el evento de forma permanente.")
            if st.button("❌ Eliminar esta Actividad", type="primary"):
                eliminar_evento(id_sel)
                st.success("Actividad eliminada con éxito.")
                st.rerun()
    else:
        st.info("No hay eventos en la base de datos para modificar o eliminar.")

# ----------------------------------------------------
# VISTA 4: RENOVACIÓN MANUAL
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
# VISTA 5: CATÁLOGO DE PAQUETES
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
            st.write(f"🎥 **{datos['sesiones']}** Sesión(es) de Grabación al mes")
            st.info(f"**Total**: {datos['total']} piezas al mes")

# ----------------------------------------------------
# VISTA 6: REGISTRO CON SUGERENCIAS DE DISTRIBUCIÓN
# ----------------------------------------------------
elif modo == "➕ Registrar Cliente / Evento":
    st.header("⚙️ Gestión de Datos y Agendamiento")
    tab1, tab2 = st.tabs(["➕ Agregar Evento / Publicación", "👤 Registrar Nuevo Cliente + Sugerencia de Plan"])
    
    with tab1:
        st.subheader("Agendar Evento o Publicación Individual")
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
        st.subheader("Registrar Cliente y Elegir Plan de Publicación")
        
        nombre_c = st.text_input("Nombre de la Marca / Empresa")
        paquete_c = st.selectbox("Paquete Contratado", list(PAQUETES_KAIROS.keys()))
        f_pago = st.date_input("Día que se recibió el Pago / Inicio de Servicio", value=date.today())
        
        f_inicio = f_pago
        f_fin = f_pago + timedelta(days=30)
        
        pkg = PAQUETES_KAIROS[paquete_c]
        st.caption(f"📅 Ciclo contractual: **{f_inicio.strftime('%d/%m/%Y')}** al **{f_fin.strftime('%d/%m/%Y')}**.")
        st.info(f" Entregables del paquete **{paquete_c}**: {pkg['posts']} Posts, {pkg['reels']} Reels, {pkg['historias']} Historias | **{pkg['sesiones']} Sesión(es) de Grabación**.")

        st.markdown("---")
        st.markdown("### 💡 3 Sugerencias de Estrategia de Publicación y Grabación")
        
        if pkg['sesiones'] == 1:
            g_opt_a = [f_inicio + timedelta(days=3)]
            g_opt_b = [f_inicio + timedelta(days=2)]
            g_opt_c = [f_inicio + timedelta(days=4)]
        else:
            g_opt_a = [f_inicio + timedelta(days=3), f_inicio + timedelta(days=17)]
            g_opt_b = [f_inicio + timedelta(days=2), f_inicio + timedelta(days=14)]
            g_opt_c = [f_inicio + timedelta(days=4), f_inicio + timedelta(days=18)]

        def generar_calendario_pubs(estrategia, fecha_base, pkg_data):
            list_pubs = []
            total_posts = pkg_data['posts']
            total_reels = pkg_data['reels']
            total_hist = pkg_data['historias']
            
            if estrategia == "A":
                dias_offset = [5, 7, 9, 12, 14, 16, 19, 21, 23, 26, 28]
                for i in range(min(total_posts, len(dias_offset))):
                    list_pubs.append({"fecha": fecha_base + timedelta(days=dias_offset[i % len(dias_offset)]), "formato": "Post Gráfico", "detalle": f"Post Gráfico #{i+1}"})
                for i in range(total_reels):
                    offset = (i * 4) + 6
                    list_pubs.append({"fecha": fecha_base + timedelta(days=min(offset, 28)), "formato": "Reel", "detalle": f"Reel #{i+1}"})
                for i in range(total_hist):
                    offset = (i * 3) + 5
                    list_pubs.append({"fecha": fecha_base + timedelta(days=min(offset, 29)), "formato": "Historia", "detalle": f"Historia #{i+1}"})

            elif estrategia == "B":
                for i in range(total_posts):
                    offset = (i * 2) + 4
                    list_pubs.append({"fecha": fecha_base + timedelta(days=min(offset, 28)), "formato": "Post Gráfico", "detalle": f"Post Gráfico #{i+1}"})
                for i in range(total_reels):
                    offset = (i * 3) + 4
                    list_pubs.append({"fecha": fecha_base + timedelta(days=min(offset, 27)), "formato": "Reel", "detalle": f"Reel #{i+1}"})
                for i in range(total_hist):
                    offset = (i * 2) + 3
                    list_pubs.append({"fecha": fecha_base + timedelta(days=min(offset, 28)), "formato": "Historia", "detalle": f"Historia #{i+1}"})

            elif estrategia == "C":
                for i in range(total_posts):
                    offset = (i * 2.5) + 6
                    list_pubs.append({"fecha": fecha_base + timedelta(days=min(int(offset), 29)), "formato": "Post Gráfico", "detalle": f"Post Gráfico #{i+1}"})
                for i in range(total_reels):
                    offset = (i * 3.5) + 6
                    list_pubs.append({"fecha": fecha_base + timedelta(days=min(int(offset), 28)), "formato": "Reel", "detalle": f"Reel #{i+1}"})
                for i in range(total_hist):
                    offset = (i * 2.8) + 5
                    list_pubs.append({"fecha": fecha_base + timedelta(days=min(int(offset), 29)), "formato": "Historia", "detalle": f"Historia #{i+1}"})

            return list_pubs

        cal_a = generar_calendario_pubs("A", f_inicio, pkg)
        cal_b = generar_calendario_pubs("B", f_inicio, pkg)
        cal_c = generar_calendario_pubs("C", f_inicio, pkg)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.info(f"**Opción A: Distribución Equilibrada (Lun-Mié-Vie)**\n\n🎥 **Grabación**: {', '.join([g.strftime('%d/%m') for g in g_opt_a])}\n\n📲 **Ritmo**: Publicaciones constantes de 3 a 4 veces por semana a lo largo del mes.")
        with col_b:
            st.info(f"**Opción B: Fast-Track (Carga Inicial)**\n\n🎥 **Grabación**: {', '.join([g.strftime('%d/%m') for g in g_opt_b])}\n\n📲 **Ritmo**: Foco intensivo en los primeros 15 días tras la grabación.")
        with col_c:
            st.info(f"**Opción C: Foco Comercial (Jue-Vie-Sáb)**\n\n🎥 **Grabación**: {', '.join([g.strftime('%d/%m') for g in g_opt_c])}\n\n📲 **Ritmo**: Concentración de lanzamientos hacia los fines de semana.")

        with st.form("form_confirmar_plan"):
            plan_elegido = st.radio("Selecciona qué estrategia aplicar para agendar todo automáticamente:", ["Opción A (Equilibrada)", "Opción B (Fast-Track)", "Opción C (Foco Comercial)", "Solo registrar cliente (Agendar manualmente)"])
            
            if st.form_submit_button("🚀 Registrar Cliente y Agendar Calendario Completo"):
                if nombre_c.strip():
                    guardar_cliente(nombre_c, paquete_c, f_pago, f_inicio, f_fin)
                    
                    if "Opción A" in plan_elegido:
                        agendar_plan_completo(nombre_c, g_opt_a, cal_a)
                    elif "Opción B" in plan_elegido:
                        agendar_plan_completo(nombre_c, g_opt_b, cal_b)
                    elif "Opción C" in plan_elegido:
                        agendar_plan_completo(nombre_c, g_opt_c, cal_c)
                        
                    st.success(f"¡Cliente '{nombre_c}' registrado correctamente con su calendario agendado!")
                    st.rerun()
                else:
                    st.error("Por favor ingresa un nombre para la empresa.")
