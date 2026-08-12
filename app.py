import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Kairós MKT - Control & Calendarios", layout="wide", page_icon="⚡")

st.title("⚡ Kairós MKT - Centro de Control")

# --- CATÁLOGO DE PAQUETES KAIRÓS MKT ---
PAQUETES_KAIROS = {
    "Actividad Constante": {
        "precio": 2500,
        "posts": 10,
        "reels": 4,
        "historias": 4,
        "total": 18
    },
    "Impulso": {
        "precio": 3400,
        "posts": 13,
        "reels": 6,
        "historias": 7,
        "total": 26
    },
    "Dominio Total": {
        "precio": 4100,
        "posts": 16,
        "reels": 9,
        "historias": 10,
        "total": 35
    }
}

# --- BASE DE DATOS TEMPORAL (SESSION STATE) ---
if "clientes" not in st.session_state:
    st.session_state.clientes = [
        {
            "id": 1,
            "nombre": "Restaurante El Faro",
            "paquete": "Impulso",
            "inicio": date(2026, 8, 1),
            "fin": date(2026, 8, 31)
        }
    ]

if "eventos" not in st.session_state:
    st.session_state.eventos = [
        {"fecha": date(2026, 8, 1), "cliente": "Restaurante El Faro", "tipo": "Inicio de Servicio", "formato": "N/A", "detalle": "Inicio del ciclo contractual"},
        {"fecha": date(2026, 8, 3), "cliente": "Restaurante El Faro", "tipo": "Día de Grabación", "formato": "N/A", "detalle": "Sesión de rodaje en sucursal"},
        {"fecha": date(2026, 8, 5), "cliente": "Restaurante El Faro", "tipo": "Publicación", "formato": "Reel", "detalle": "Reel 1: Promoción de la semana"},
        {"fecha": date(2026, 8, 8), "cliente": "Restaurante El Faro", "tipo": "Publicación", "formato": "Post Gráfico", "detalle": "Post 1: Platillo estrella"},
        {"fecha": date(2026, 8, 10), "cliente": "Restaurante El Faro", "tipo": "Reunión", "formato": "N/A", "detalle": "Revisión de métricas de mitad de mes"},
        {"fecha": date(2026, 8, 31), "cliente": "Restaurante El Faro", "tipo": "Fin de Servicio", "formato": "N/A", "detalle": "Fecha de corte / Renovación"}
    ]

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
    st.caption("Consolidado de días de grabación, reuniones, lanzamientos y publicaciones.")
    
    df_eventos = pd.DataFrame(st.session_state.eventos)
    
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
            df_filtrado, 
            column_config={
                "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "cliente": "Cliente",
                "tipo": "Tipo de Evento",
                "formato": "Formato de Contenido",
                "detalle": "Detalle / Descripción"
            },
            use_container_width=True,
            hide_index=True
        )

# ----------------------------------------------------
# VISTA 2: CALENDARIO ESPECÍFICO POR CLIENTE
# ----------------------------------------------------
elif modo == "👥 Calendario por Cliente":
    st.header("👤 Control y Avance de Entregables por Cliente")
    
    nombres_clientes = [c["nombre"] for c in st.session_state.clientes]
    if nombres_clientes:
        cliente_sel = st.selectbox("Selecciona un Cliente", nombres_clientes)
        info_cliente = next(c for c in st.session_state.clientes if c["nombre"] == cliente_sel)
        pkg_info = PAQUETES_KAIROS[info_cliente["paquete"]]
        
        # Ficha Resumen del Paquete Contratado
        st.subheader(f"📌 Estado del Servicio: {cliente_sel}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Paquete", info_cliente["paquete"])
        col2.metric("Inversión", f"${pkg_info['precio']:,} MXN")
        col3.metric("Inicio de Ciclo", info_cliente["inicio"].strftime("%d/%m/%Y"))
        col4.metric("Fin de Ciclo", info_cliente["fin"].strftime("%d/%m/%Y"))
        
        # Conteo de Avance de Entregables
        df_ev = pd.DataFrame(st.session_state.eventos)
        ev_cliente = df_ev[(df_ev["cliente"] == cliente_sel) & (df_ev["tipo"] == "Publicación")] if not df_ev.empty else pd.DataFrame()
        
        posts_programados = len(ev_cliente[ev_cliente["formato"] == "Post Gráfico"]) if not ev_cliente.empty else 0
        reels_programados = len(ev_cliente[ev_cliente["formato"] == "Reel"]) if not ev_cliente.empty else 0
        historias_programadas = len(ev_cliente[ev_cliente["formato"] == "Historia"]) if not ev_cliente.empty else 0
        
        st.markdown("#### 📊 Progreso del Paquete Contratado")
        m1, m2, m3 = st.columns(3)
        m1.metric("Post Gráficos", f"{posts_programados} / {pkg_info['posts']}")
        m2.metric("Reels", f"{reels_programados} / {pkg_info['reels']}")
        m3.metric("Historias", f"{historias_programadas} / {pkg_info['historias']}")
        
        st.divider()
        
        # Cronograma Completo del Cliente
        st.subheader("🗓️ Cronograma de Actividades")
        df_cliente = df_ev[df_ev["cliente"] == cliente_sel].sort_values("fecha") if not df_ev.empty else pd.DataFrame()
        
        st.dataframe(
            df_cliente[["fecha", "tipo", "formato", "detalle"]],
            column_config={
                "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "tipo": "Categoría",
                "formato": "Formato",
                "detalle": "Descripción de la Actividad / Contenido"
            },
            use_container_width=True,
            hide_index=True
        )

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
# VISTA 4: REGISTRO DE CLIENTES Y EVENTOS
# ----------------------------------------------------
elif modo == "➕ Registrar Cliente / Evento":
    st.header("⚙️ Gestión de Datos y Agendamiento")
    
    tab1, tab2 = st.tabs(["➕ Agregar Evento / Publicación", "👤 Registrar Nuevo Cliente"])
    
    with tab1:
        st.subheader("Agendar Evento o Publicación")
        with st.form("form_evento"):
            cliente_ev = st.selectbox("Cliente", [c["nombre"] for c in st.session_state.clientes])
            tipo_ev = st.selectbox("Tipo de Evento", ["Publicación", "Día de Grabación", "Reunión con Cliente", "Inicio de Servicio", "Fin de Servicio"])
            formato_ev = st.selectbox("Formato (Si es publicación)", ["N/A", "Post Gráfico", "Reel", "Historia"])
            fecha_ev = st.date_input("Fecha del Evento", value=date.today())
            detalle_ev = st.text_input("Detalle / Copy / Tema de la sesión")
            
            if st.form_submit_button("Guardar Actividad"):
                st.session_state.eventos.append({
                    "fecha": fecha_ev,
                    "cliente": cliente_ev,
                    "tipo": tipo_ev,
                    "formato": formato_ev,
                    "detalle": detalle_ev
                })
                st.success("¡Actividad registrada correctamente!")
                st.rerun()

    with tab2:
        st.subheader("Registrar Cliente de Kairós MKT")
        with st.form("form_cliente"):
            nombre_c = st.text_input("Nombre de la Marca / Empresa")
            paquete_c = st.selectbox("Paquete Contratado", list(PAQUETES_KAIROS.keys()))
            f_inicio = st.date_input("Fecha Inicio de Servicio", value=date.today())
            f_fin = st.date_input("Fecha Fin de Servicio", value=date.today() + timedelta(days=30))
            
            if st.form_submit_button("Registrar Cliente"):
                nuevo_id = len(st.session_state.clientes) + 1
                
                # Registrar cliente
                st.session_state.clientes.append({
                    "id": nuevo_id,
                    "nombre": nombre_c,
                    "paquete": paquete_c,
                    "inicio": f_inicio,
                    "fin": f_fin
                })
                
                # Generar eventos automáticos de Inicio y Fin de ciclo
                st.session_state.eventos.append({"fecha": f_inicio, "cliente": nombre_c, "tipo": "Inicio de Servicio", "formato": "N/A", "detalle": f"Inicio de ciclo: Paquete {paquete_c}"})
                st.session_state.eventos.append({"fecha": f_fin, "cliente": nombre_c, "tipo": "Fin de Servicio", "formato": "N/A", "detalle": f"Fin de ciclo: Paquete {paquete_c}"})
                
                st.success(f"Cliente '{nombre_c}' registrado con éxito.")
                st.rerun()
