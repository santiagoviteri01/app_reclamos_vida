import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuración de usuarios y contraseñas
USUARIOS = {
    "wiga": "contraseña_secreta123",
    "admin": "admin123",
    "dany":"futbol123"
}

def visualizar_estadisticas_pendientes(pendientes_df: pd.DataFrame, titulo: str = "Reclamos Pendientes"):
    """
    Muestra estadísticas visuales de reclamos pendientes en dos columnas.
    
    Args:
        pendientes_df (pd.DataFrame): DataFrame con los reclamos pendientes
        titulo (str): Título principal de la sección
    """
    if not pendientes_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de causas
            fig = plt.figure(figsize=(10, 5))
            sns.countplot(y='CAUSA SINIESTRO', data=pendientes_df, 
                        order=pendientes_df['CAUSA SINIESTRO'].value_counts().index)
            plt.title(f'Causas de {titulo}')
            plt.xlabel('Cantidad')
            plt.ylabel('Causa del siniestro')
            st.pyplot(fig)
            plt.close(fig)
            
        with col2:
            # Gráfico de días pendientes
            pendientes_df['DIAS PENDIENTES'] = (datetime.now() - pendientes_df['FECHA SINIESTRO']).dt.days
            
            fig = plt.figure(figsize=(10, 5))
            sns.histplot(pendientes_df['DIAS PENDIENTES'], bins=20, kde=True, color='salmon')
            plt.title(f'Distribución de Días en {titulo}')
            plt.xlabel('Días transcurridos')
            plt.ylabel('Cantidad de reclamos')
            st.pyplot(fig)
            plt.close(fig)
    else:
        st.info(f"No hay {titulo.lower()} para los filtros seleccionados")
        
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

# Interfaz de usuario
st.title("Análisis de Reclamos")
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        st.success("Datos cargados correctamente ✅")
        df['FECHA SINIESTRO'] = pd.to_datetime(df['FECHA SINIESTRO'], errors='coerce')
        df['FECHA NOTIFICACION SINIESTRO'] = pd.to_datetime(df['FECHA NOTIFICACION SINIESTRO'], errors='coerce')
        
        # Sidebar controls
        with st.sidebar:
            st.header("Configuración del Análisis")
            año_analisis = st.selectbox("Seleccionar Año", sorted(df['FECHA SINIESTRO'].dt.year.unique()))
            top_n = st.slider("Top N Causas", 3, 10, 5)
            bins_hist = st.slider("Bins para Histograma", 10, 100, 30)
                            # Filtros principales
          # Generar lista de productos con manejo seguro de NaN
            
            # Opción 2: Reemplazar NaN con un valor por defecto
            df['BASE'] = df['BASE'].fillna('No especificado').str.upper()
            base_values = df['BASE'].copy()
            producto = ['Todas'] + sorted(base_values.unique().tolist())
            producto_sel = st.selectbox("Seleccionar Producto", producto)
            df_filtrado = df.copy()
            if producto_sel != 'Todas':
                df = df_filtrado[df_filtrado['BASE'] == producto_sel]

        liquidados = df[df['ESTADO'] == 'LIQUIDADO']
        pendientes = df[df['ESTADO'] == 'PENDIENTE DE DOCUMENTOS']
        negados= df[df['ESTADO'] == 'NEGADO']
        procesados= df[df['ESTADO'] == 'EN PROCESO']
        
        # Filtrar datos por año
        liquidados_filtrados = liquidados[liquidados['FECHA SINIESTRO'].dt.year == año_analisis]
        pendientes_filtrados = pendientes[pendientes['FECHA SINIESTRO'].dt.year == año_analisis]
        negados_filtrados = negados[negados['FECHA SINIESTRO'].dt.year == año_analisis]
        procesados_filtrados = procesados[procesados['FECHA SINIESTRO'].dt.year == año_analisis]
        df2=df[df['FECHA SINIESTRO'].dt.year == año_analisis]
        # Análisis temporal
        st.header("📈 Reclamos Liquidados")

        if not liquidados_filtrados.empty:
            # Gráfico de reclamos por mes
            fig, ax = plt.subplots(figsize=(10, 4))
            liquidados_filtrados['MES'] = liquidados_filtrados['FECHA SINIESTRO'].dt.month
            liquidados_filtrados['MES'] = pd.Categorical(liquidados_filtrados['MES'], ordered=True)
            liquidados_filtrados['MES'].value_counts().sort_index().plot(kind='bar', color='teal', ax=ax)
            plt.title('Reclamos Liquidados por Mes')
            plt.xlabel('Mes')
            plt.ylabel('Cantidad de Reclamos')
            st.pyplot(fig)
            
            # Métricas resumen
            col1, col2 = st.columns(2)
            liquidados_filtrados['TIEMPO_RESPUESTA'] = (liquidados_filtrados['FECHA NOTIFICACION SINIESTRO'] - liquidados_filtrados['FECHA SINIESTRO']).dt.days
            tiempo_promedio = liquidados_filtrados['TIEMPO_RESPUESTA'].mean()
            with col1:
                st.metric("Total Reclamos Liquidados", f"{len(liquidados_filtrados):,}")
                st.metric(
                    label="Días promedio entre siniestro y notificación",
                    value=f"{tiempo_promedio:.1f} días",
                    help="Tiempo promedio desde que ocurre el siniestro hasta su notificación"
                )
            with col2:
                st.metric("Valor Total Liquidado", f"${liquidados_filtrados['VALOR INDEMNIZADO'].sum():,.2f}")
                st.metric("Edad Promedio de Fallecimiendo", f"{df['EDAD'].mean():,.2f}")
            
            # Análisis de VALOR INDEMNIZADOes
            st.header("💰 Análisis de Valores Asegurados")
            
            col4, col5 = st.columns(2)
            with col4:
                # Histograma
                fig = plt.figure(figsize=(10, 5))
                sns.histplot(liquidados_filtrados['VALOR INDEMNIZADO'], bins=bins_hist, kde=True, color='purple')
                plt.title('Distribución de Valores Asegurados')
                st.pyplot(fig)
            
            with col5:
                # Boxplot
                fig = plt.figure(figsize=(10, 5))
                sns.boxplot(x=liquidados_filtrados['VALOR INDEMNIZADO'], color='orange')
                plt.title('Distribución de Valores (Boxplot)')
                st.pyplot(fig)
            
            # Análisis de causas
            st.header("🩺 Análisis de Causas de Siniestros")
            
            # Top causas
            top_causas = liquidados_filtrados['CAUSA SINIESTRO'].value_counts().nlargest(top_n)
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(x=top_causas.values, y=top_causas.index, palette='viridis')
            plt.title(f'Top {top_n} Causas de Siniestros')
            plt.xlabel('Cantidad de Reclamos')
            st.pyplot(fig)
            
            # Análisis de parentesco
            st.header("👪 Distribución por Parentesco")
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.countplot(y='PARENTESCO', data=liquidados_filtrados, order=liquidados_filtrados['PARENTESCO'].value_counts().index)
            plt.title('Distribución de Reclamos por Parentesco')
            st.pyplot(fig)
    
            # --- Sección 2: Distribución de Edades ---
            st.subheader("👥 Distribución de Edades")
                    
            # Crear bins personalizados
            bins = [0, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 120]
            labels = [
                '0-20', '20-25', '25-30', '30-35', '35-40', 
                '40-45', '45-50', '50-55', '55-60', '60-65',
                '65-70', '70-75', '75-80', '80-85', '85+'
            ]
            
            liquidados_filtrados['GRUPO_EDAD'] = pd.cut(
                liquidados_filtrados['EDAD'],
                bins=bins,
                labels=labels,
                right=False
            )
            
            # Calcular distribución
            distribucion_edades = liquidados_filtrados['GRUPO_EDAD'].value_counts().sort_index()
            
            # Gráfico
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(
                x=distribucion_edades.index,
                y=distribucion_edades.values,
                palette="viridis",
                ax=ax
            )
            
            plt.title('Distribución de Edades por Grupo', fontsize=14)
            plt.xlabel('Grupo de Edad', fontsize=12)
            plt.ylabel('Cantidad de Casos', fontsize=12)
            plt.xticks(rotation=45)
            
            # Añadir etiquetas
            for p in ax.patches:
                ax.annotate(
                    f'{int(p.get_height())}', 
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', 
                    xytext=(0, 5), 
                    textcoords='offset points'
                )
            
            st.pyplot(fig)
          
            st.subheader("Análisis de Agencias y de Personal")
            # Calcular distribución
            distribucion_agrencias = liquidados_filtrados['AGENCIA'].value_counts().sort_index()
            cola, colb = st.columns(2)
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(
                    x=distribucion_agrencias.index,
                    y=distribucion_agrencias.values,
                    palette="viridis",
                    ax=ax
                )
                
            plt.title('Reclamos por Agencias', fontsize=14)
            plt.xlabel('Agencia', fontsize=12)
            plt.ylabel('Cantidad de Casos', fontsize=12)
            plt.xticks(rotation=45)
            st.pyplot(fig)

            distribucion_asesores = liquidados_filtrados['ASESOR'].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(
                    x=distribucion_asesores.index,
                    y=distribucion_asesores.values,
                    palette="viridis",
                    ax=ax
                )
            plt.title('Reclamos por Asesor', fontsize=14)
            plt.xlabel('Asesor', fontsize=12)
            plt.ylabel('Cantidad de Casos', fontsize=12)
            plt.xticks(rotation=45)
            st.pyplot(fig)

            # --- Sección 3: Tabla detallada ---
            with st.expander("📊 Ver datos detallados por grupo de edad"):
                st.dataframe(
                    distribucion_edades.reset_index().rename(
                        columns={'index': 'Grupo de Edad', 'GRUPO_EDAD': 'Casos'}
                    ).style.background_gradient(cmap='Blues'),
                    use_container_width=True
                )
        else:
            st.info("No hay reclamos liquidados para el año seleccionado")

        # Análisis de pendientes
        st.header("⏳ Reclamos Pendientes")
        
        if not pendientes_filtrados.empty:
            col6, col7 = st.columns(2)
            
            with col6:
              
                # Distribución de causas pendientes
                fig = plt.figure(figsize=(10, 5))
                sns.countplot(y='CAUSA SINIESTRO', data=pendientes_filtrados)
                plt.title('Causas de Reclamos Pendientes')
                st.pyplot(fig)
            
            with col7:
                # Tiempo pendiente
                pendientes_filtrados['DIAS PENDIENTES'] = (datetime.now() - pendientes_filtrados['FECHA SINIESTRO']).dt.days
                fig = plt.figure(figsize=(10, 5))
                sns.histplot(pendientes_filtrados['DIAS PENDIENTES'], bins=20, kde=True)
                plt.title('Distribución de Días Pendientes')
                st.pyplot(fig)

        else:
            st.info("No hay reclamos pendientes para el año seleccionado")

        visualizar_estadisticas_pendientes(negados_filtrados,titulo="Reclamos Negados en el Año")
        visualizar_estadisticas_pendientes(procesados_filtrados,titulo="Reclamos Procesados en el Año")

        
        # Mostrar datos crudos
        st.header("📄 Datos Crudos")
        st.dataframe(df2, use_container_width=True)

    
    else:
        st.warning("No se pudo cargar el archivo. Verifica el formato.")
else:
    st.info("👋 Por favor sube un archivo Excel para comenzar")

