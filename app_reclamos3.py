import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuración de usuarios y contraseñas
USUARIOS = {
    "wiga": "contraseña_secreta123",
    "admin": "admin123"
}

# Función de autenticación básica
def autenticacion():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
        
    if not st.session_state.autenticado:
        with st.container():
            st.title("🔒 Inicio de Sesión")
            usuario = st.text_input("Usuario")
            contraseña = st.text_input("Contraseña", type="password")
            
            if st.button("Ingresar"):
                if USUARIOS.get(usuario) == contraseña:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
        return False
    return True

# Verificar autenticación antes de mostrar la app
if not autenticacion():
    st.stop()

# ==============================================
# Configuración de la aplicación principal
# ==============================================

def load_data(uploaded_file):
    if uploaded_file is not None:
        return pd.read_excel(uploaded_file, engine='openpyxl')
    return None

# Configuración de página
st.set_page_config(page_title="Análisis de Reclamos", layout="wide")

# Botón de logout en sidebar
with st.sidebar:
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# Interfaz principal
st.title("📊 Análisis de Reclamos de Seguros")
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        st.success("✅ Datos cargados correctamente")
        
        # Procesamiento de fechas
        df['FECHA SINIESTRO'] = pd.to_datetime(df['FECHA SINIESTRO'], errors='coerce')
        df['FECHA NOTIFICACION SINIESTRO'] = pd.to_datetime(df['FECHA NOTIFICACION SINIESTRO'], errors='coerce')
        
        # Sidebar controls
        with st.sidebar:
            st.header("⚙️ Configuración del Análisis")
            
            # Filtro de año
            años_disponibles = sorted(df['FECHA SINIESTRO'].dt.year.unique())
            año_analisis = st.selectbox("Seleccionar Año", años_disponibles)
            
            # Filtro de producto
            df['BASE'] = df['BASE'].fillna('No especificado').str.upper()
            producto = ['Todas'] + sorted(df['BASE'].unique().tolist())
            producto_sel = st.selectbox("Seleccionar Producto", producto)
            
            # Otros controles
            top_n = st.slider("🔝 Top N Causas", 3, 10, 5)
            bins_hist = st.slider("📊 Bins para Histograma", 10, 100, 30)

        # Aplicar filtros
        df_filtrado = df.copy()
        if producto_sel != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['BASE'] == producto_sel]
        
        # Filtrar por año
        df_filtrado = df_filtrado[df_filtrado['FECHA SINIESTRO'].dt.year == año_analisis]
        
        # Separar liquidados y pendientes
        liquidados = df_filtrado[df_filtrado['ESTADO'] == 'LIQUIDADO']
        pendientes = df_filtrado[df_filtrado['ESTADO'] == 'PENDIENTE']

        # ======================
        # Sección de Liquidados
        # ======================
        st.header("📈 Reclamos Liquidados")
        
        if not liquidados.empty:
            # Gráfico temporal
            fig, ax = plt.subplots(figsize=(10, 4))
            liquidados['MES'] = liquidados['FECHA SINIESTRO'].dt.month_name(locale='Spanish')
            meses_orden = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            liquidados['MES'] = pd.Categorical(liquidados['MES'], categories=meses_orden, ordered=True)
            liquidados['MES'].value_counts().sort_index().plot(kind='bar', color='teal', ax=ax)
            plt.title('Reclamos Liquidados por Mes')
            plt.xlabel('Mes')
            plt.ylabel('Cantidad')
            st.pyplot(fig)
            
            # Métricas
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Liquidados", len(liquidados))
                liquidados['TIEMPO_RESPUESTA'] = (liquidados['FECHA NOTIFICACION SINIESTRO'] - liquidados['FECHA SINIESTRO']).dt.days
                st.metric("Días promedio respuesta", f"{liquidados['TIEMPO_RESPUESTA'].mean():.1f}")
                
            with col2:
                st.metric("Valor Total Liquidado", f"${liquidados['VALOR ASEGURADO'].sum():,.2f}")
                st.metric("Edad Promedio", f"{liquidados['EDAD'].mean():.1f} años")
            
            # Análisis de valores
            st.header("💰 Distribución de Valores")
            col3, col4 = st.columns(2)
            with col3:
                fig = plt.figure(figsize=(10, 5))
                sns.histplot(liquidados['VALOR ASEGURADO'], bins=bins_hist, kde=True, color='purple')
                plt.title('Distribución de Valores Asegurados')
                st.pyplot(fig)
            
            with col4:
                fig = plt.figure(figsize=(10, 5))
                sns.boxplot(x=liquidados['VALOR ASEGURADO'], color='orange')
                plt.title('Distribución de Valores (Boxplot)')
                st.pyplot(fig)
            
            # Análisis de causas
            st.header("🩺 Principales Causas")
            top_causas = liquidados['CAUSA SINIESTRO'].value_counts().nlargest(top_n)
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(x=top_causas.values, y=top_causas.index, palette='viridis')
            plt.title(f'Top {top_n} Causas de Siniestros')
            plt.xlabel('Cantidad')
            st.pyplot(fig)
            
        else:
            st.info("ℹ️ No hay reclamos liquidados para los filtros seleccionados")

        # ======================
        # Sección de Pendientes
        # ======================
        st.header("⏳ Reclamos Pendientes")
        
        if not pendientes.empty:
            col5, col6 = st.columns(2)
            
            with col5:
                fig = plt.figure(figsize=(10, 5))
                sns.countplot(y='CAUSA SINIESTRO', data=pendientes)
                plt.title('Causas Pendientes')
                st.pyplot(fig)
            
            with col6:
                pendientes['DIAS_PENDIENTES'] = (datetime.now() - pendientes['FECHA SINIESTRO']).dt.days
                fig = plt.figure(figsize=(10, 5))
                sns.histplot(pendientes['DIAS_PENDIENTES'], bins=20, kde=True)
                plt.title('Días Pendientes')
                st.pyplot(fig)
        else:
            st.info("ℹ️ No hay reclamos pendientes para los filtros seleccionados")

        # Datos crudos
        st.header("📄 Datos Originales")
        st.dataframe(df_filtrado, use_container_width=True)
        
    else:
        st.error("❌ Error al cargar el archivo")
else:
    st.info("👋 Por favor sube un archivo Excel para comenzar")
