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
        st.header(titulo)
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
            pendientes_df['DIAS PENDIENTES'] = (pendientes_df['FECHA NOTIFICACION SINIESTRO'] - pendientes_df['FECHA SINIESTRO']).dt.days
            
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
# Funciones auxiliares
# ==============================================

def load_data(uploaded_file):
    if uploaded_file is not None:
        return pd.read_excel(uploaded_file, engine='openpyxl')
    return None

# ==============================================
# Configuración de la aplicación principal
# ==============================================

# Configuración de página
st.set_page_config(page_title="Análisis de Reclamos", layout="wide")

# Botón de logout en sidebar
with st.sidebar:
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# Interfaz principal
st.title("📊 Análisis de Reclamos de Seguros")

# Tabs para separar los análisis
tab1, tab2 = st.tabs(["👤 Reclamos de Vida", "🏠 Reclamos de Hogar/Propiedad"])

# ==============================================
# TAB 1: ANÁLISIS DE RECLAMOS DE VIDA (DESGRAVAMEN)
# ==============================================
with tab1:
    st.header("Análisis de Reclamos de Vida - Desgravamen")
    uploaded_file_vida = st.file_uploader("Sube tu archivo Excel - Reclamos de Vida/Desgravamen", type=["xlsx", "xls"], key="vida")

    if uploaded_file_vida:
        df = load_data(uploaded_file_vida)
        
        if df is not None:
            st.success("Datos cargados correctamente ✅")
            
            # Procesar fechas
            df['FECHA SINIESTRO'] = pd.to_datetime(df['FECHA SINIESTRO'], errors='coerce')
            df['FECHA NOTIFICACION SINIESTRO'] = pd.to_datetime(df['FECHA NOTIFICACION SINIESTRO'], errors='coerce')
            df['FECHA DE CIERRE/INDEMNIZACION'] = pd.to_datetime(df['FECHA DE CIERRE/INDEMNIZACION'], errors='coerce')
            df['INICIO VIGENCIA'] = pd.to_datetime(df['INICIO VIGENCIA'], errors='coerce')
            df['FIN VIGENCIA'] = pd.to_datetime(df['FIN VIGENCIA'], errors='coerce')
            
            # Verificar si tiene columna EDAD (para bases antiguas) o calcularla
            if 'EDAD' not in df.columns:
                st.info("ℹ️ Este archivo no contiene columna EDAD. Algunas métricas de edad no estarán disponibles.")
                tiene_edad = False
            else:
                tiene_edad = True
            
            # Verificar si tiene columna PARENTESCO
            tiene_parentesco = 'PARENTESCO' in df.columns
            
            # Verificar si tiene columnas AGENCIA y ASESOR
            tiene_agencia = 'AGENCIA' in df.columns
            tiene_asesor = 'ASESOR' in df.columns
            
            # Sidebar controls
            with st.sidebar:
                st.header("⚙️ Configuración - Vida")
                año_analisis = st.selectbox("Seleccionar Año", sorted(df['FECHA SINIESTRO'].dt.year.unique()), key="año_vida")
                top_n = st.slider("Top N Causas", 3, 10, 5, key="top_vida")
                bins_hist = st.slider("Bins para Histograma", 10, 100, 30, key="bins_vida")
                
                # Filtros principales
                df['BASE'] = df['BASE'].fillna('No especificado').str.upper()
                base_values = df['BASE'].copy()
                producto = ['Todas'] + sorted(base_values.unique().tolist())
                producto_sel = st.selectbox("Seleccionar Producto", producto, key="prod_vida")
                df_filtrado = df.copy()
                if producto_sel != 'Todas':
                    df = df_filtrado[df_filtrado['BASE'] == producto_sel]

            liquidados = df[df['ESTADO'] == 'LIQUIDADO']
            pendientes = df[df['ESTADO'] == 'PENDIENTE DOCUMENTOS'] if 'PENDIENTE DOCUMENTOS' in df['ESTADO'].values else pd.DataFrame()
            negados = df[df['ESTADO'] == 'NEGADO']
            procesados = df[df['ESTADO'] == 'EN PROCESO']
            
            # Filtrar datos por año
            liquidados_filtrados = liquidados[liquidados['FECHA SINIESTRO'].dt.year == año_analisis]
            pendientes_filtrados = pendientes[pendientes['FECHA SINIESTRO'].dt.year == año_analisis] if not pendientes.empty else pd.DataFrame()
            negados_filtrados = negados[negados['FECHA SINIESTRO'].dt.year == año_analisis]
            procesados_filtrados = procesados[procesados['FECHA SINIESTRO'].dt.year == año_analisis]
            df2 = df[df['FECHA SINIESTRO'].dt.year == año_analisis]
            
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
                liquidados_filtrados['TIEMPO_CIERRE'] = (liquidados_filtrados['FECHA DE CIERRE/INDEMNIZACION'] - liquidados_filtrados['FECHA SINIESTRO']).dt.days
                tiempo_promedio = liquidados_filtrados['TIEMPO_RESPUESTA'].mean()
                
                with col1:
                    st.metric("Total Reclamos Liquidados", f"{len(liquidados_filtrados):,}")
                    st.metric(
                        label="Días promedio entre siniestro y notificación",
                        value=f"{tiempo_promedio:.1f} días",
                        help="Tiempo promedio desde que ocurre el siniestro hasta su notificación"
                    )
                with col2:
                    st.metric("Valor Total Indemnizado", f"${liquidados_filtrados['VALOR INDEMNIZADO'].sum():,.2f}")
                    if tiene_edad:
                        st.metric("Edad Promedio", f"{df['EDAD'].mean():.1f} años")
                    else:
                        st.metric("Plazo Promedio Crédito", f"{liquidados_filtrados['PLAZO'].mean():.1f} meses")
                
                # Análisis de valores
                st.header("💰 Análisis de Valores Asegurados")
                
                fig = plt.figure(figsize=(10, 5))
                sns.histplot(liquidados_filtrados['VALOR INDEMNIZADO'], bins=bins_hist, kde=True, color='purple')
                plt.title('Distribución de Valores Asegurados')
                st.pyplot(fig)
                
                # Análisis de causas
                st.header("🩺 Análisis de Causas de Siniestros")
                
                top_causas = liquidados_filtrados['CAUSA SINIESTRO'].value_counts().nlargest(top_n)
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=top_causas.values, y=top_causas.index, palette='viridis')
                plt.title(f'Top {top_n} Causas de Siniestros')
                plt.xlabel('Cantidad de Reclamos')
                st.pyplot(fig)
                
                # Análisis de parentesco (solo si existe la columna)
                if tiene_parentesco:
                    st.header("👪 Distribución por Parentesco")
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.countplot(y='PARENTESCO', data=liquidados_filtrados, order=liquidados_filtrados['PARENTESCO'].value_counts().index)
                    plt.title('Distribución de Reclamos por Parentesco')
                    st.pyplot(fig)
        
                # Distribución de Edades (solo si existe la columna)
                if tiene_edad:
                    st.subheader("👥 Distribución de Edades")
                            
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
                    
                    distribucion_edades = liquidados_filtrados['GRUPO_EDAD'].value_counts().sort_index()
                    
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
                    
                    for p in ax.patches:
                        ax.annotate(
                            f'{int(p.get_height())}', 
                            (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='center', 
                            xytext=(0, 5), 
                            textcoords='offset points'
                        )
                    
                    st.pyplot(fig)
                    
                    with st.expander("📊 Ver datos detallados por grupo de edad"):
                        st.dataframe(
                            distribucion_edades.reset_index().rename(
                                columns={'index': 'Grupo de Edad', 'GRUPO_EDAD': 'Casos'}
                            ).style.background_gradient(cmap='Blues'),
                            use_container_width=True
                        )
            
                # Análisis de agencias y personal (solo si existen las columnas)
                if tiene_agencia or tiene_asesor:
                    st.subheader("📍 Análisis de Agencias y Personal")
                    
                    if tiene_agencia:
                        distribucion_agencias = liquidados_filtrados['AGENCIA'].value_counts().sort_index()
                        fig, ax = plt.subplots(figsize=(12, 6))
                        sns.barplot(
                                x=distribucion_agencias.index,
                                y=distribucion_agencias.values,
                                palette="viridis",
                                ax=ax
                            )
                            
                        plt.title('Reclamos por Agencias', fontsize=14)
                        plt.xlabel('Agencia', fontsize=12)
                        plt.ylabel('Cantidad de Casos', fontsize=12)
                        plt.xticks(rotation=45)
                        st.pyplot(fig)

                    if tiene_asesor:
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
            else:
                st.info("No hay reclamos liquidados para el año seleccionado")

            # Análisis de pendientes
            st.header("⏳ Reclamos Pendientes")
            
            if not pendientes_filtrados.empty:
                col6, col7 = st.columns(2)
                
                with col6:
                    fig = plt.figure(figsize=(10, 5))
                    sns.countplot(y='CAUSA SINIESTRO', data=pendientes_filtrados)
                    plt.title('Causas de Reclamos Pendientes')
                    st.pyplot(fig)
                
                with col7:
                    pendientes_filtrados['DIAS PENDIENTES'] = (datetime.now() - pendientes_filtrados['FECHA SINIESTRO']).dt.days
                    fig = plt.figure(figsize=(10, 5))
                    sns.histplot(pendientes_filtrados['DIAS PENDIENTES'], bins=20, kde=True)
                    plt.title('Distribución de Días Pendientes')
                    st.pyplot(fig)
            else:
                st.info("No hay reclamos pendientes para el año seleccionado")

            visualizar_estadisticas_pendientes(negados_filtrados, titulo="Reclamos Negados")
            visualizar_estadisticas_pendientes(procesados_filtrados, titulo="Reclamos Procesados")

            # Mostrar datos crudos
            st.header("📄 Datos Crudos")
            st.dataframe(df2, use_container_width=True)

        else:
            st.warning("No se pudo cargar el archivo. Verifica el formato.")
    else:
        st.info("👋 Por favor sube un archivo Excel para comenzar")

# ==============================================
# TAB 2: ANÁLISIS DE RECLAMOS DE HOGAR/PROPIEDAD
# ==============================================
with tab2:
    st.header("Análisis de Reclamos de Hogar/Propiedad")
    uploaded_file_hogar = st.file_uploader("Sube tu archivo Excel - Reclamos de Hogar", type=["xlsx", "xls"], key="hogar")

    if uploaded_file_hogar:
        df_hogar = load_data(uploaded_file_hogar)
        
        if df_hogar is not None:
            st.success("Datos de hogar cargados correctamente ✅")
            
            # Procesar fechas
            df_hogar['FECHA SINIESTRO'] = pd.to_datetime(df_hogar['FECHA SINIESTRO'], errors='coerce')
            df_hogar['FECHA NOTIFICACION SINIESTRO'] = pd.to_datetime(df_hogar['FECHA NOTIFICACION SINIESTRO'], errors='coerce')
            df_hogar['FECHA DE CIERRE/INDEMNIZACION'] = pd.to_datetime(df_hogar['FECHA DE CIERRE/INDEMNIZACION'], errors='coerce')
            df_hogar['INICIO VIGENCIA'] = pd.to_datetime(df_hogar['INICIO VIGENCIA'], errors='coerce')
            df_hogar['FIN VIGENCIA'] = pd.to_datetime(df_hogar['FIN VIGENCIA'], errors='coerce')
            
            # Sidebar controls
            with st.sidebar:
                st.header("⚙️ Configuración - Hogar")
                año_analisis_hogar = st.selectbox("Seleccionar Año", sorted(df_hogar['FECHA SINIESTRO'].dt.year.unique()), key="año_hogar")
                top_n_hogar = st.slider("Top N Causas", 3, 10, 5, key="top_hogar")
                bins_hist_hogar = st.slider("Bins para Histograma", 10, 100, 30, key="bins_hogar")
                
                # Filtro por producto
                df_hogar['BASE'] = df_hogar['BASE'].fillna('No especificado').str.upper()
                productos_hogar = ['Todas'] + sorted(df_hogar['BASE'].unique().tolist())
                producto_sel_hogar = st.selectbox("Seleccionar Producto", productos_hogar, key="prod_hogar")
                
                df_hogar_filtrado = df_hogar.copy()
                if producto_sel_hogar != 'Todas':
                    df_hogar = df_hogar_filtrado[df_hogar_filtrado['BASE'] == producto_sel_hogar]

            # Separar por estado
            liquidados_hogar = df_hogar[df_hogar['ESTADO'] == 'LIQUIDADO']
            negados_hogar = df_hogar[df_hogar['ESTADO'] == 'NEGADO']
            procesados_hogar = df_hogar[df_hogar['ESTADO'] == 'EN PROCESO']
            
            # Filtrar por año
            liquidados_hogar_f = liquidados_hogar[liquidados_hogar['FECHA SINIESTRO'].dt.year == año_analisis_hogar]
            negados_hogar_f = negados_hogar[negados_hogar['FECHA SINIESTRO'].dt.year == año_analisis_hogar]
            procesados_hogar_f = procesados_hogar[procesados_hogar['FECHA SINIESTRO'].dt.year == año_analisis_hogar]
            df_hogar_año = df_hogar[df_hogar['FECHA SINIESTRO'].dt.year == año_analisis_hogar]
            
            # Análisis de reclamos liquidados
            st.header("📈 Reclamos de Hogar Liquidados")
            
            if not liquidados_hogar_f.empty:
                # Gráfico temporal
                fig, ax = plt.subplots(figsize=(10, 4))
                liquidados_hogar_f['MES'] = liquidados_hogar_f['FECHA SINIESTRO'].dt.month
                liquidados_hogar_f['MES'].value_counts().sort_index().plot(kind='bar', color='darkgreen', ax=ax)
                plt.title('Reclamos de Hogar Liquidados por Mes')
                plt.xlabel('Mes')
                plt.ylabel('Cantidad de Reclamos')
                st.pyplot(fig)
                
                # Métricas principales
                col1, col2, col3 = st.columns(3)
                
                liquidados_hogar_f['TIEMPO_RESPUESTA'] = (liquidados_hogar_f['FECHA NOTIFICACION SINIESTRO'] - liquidados_hogar_f['FECHA SINIESTRO']).dt.days
                liquidados_hogar_f['TIEMPO_CIERRE'] = (liquidados_hogar_f['FECHA DE CIERRE/INDEMNIZACION'] - liquidados_hogar_f['FECHA SINIESTRO']).dt.days
                
                with col1:
                    st.metric("Total Reclamos", f"{len(liquidados_hogar_f):,}")
                    st.metric("Días promedio notificación", f"{liquidados_hogar_f['TIEMPO_RESPUESTA'].mean():.1f} días")
                
                with col2:
                    st.metric("Valor Total Indemnizado", f"${liquidados_hogar_f['VALOR INDEMNIZADO'].sum():,.2f}")
                    st.metric("Días promedio cierre", f"{liquidados_hogar_f['TIEMPO_CIERRE'].mean():.1f} días")
                
                with col3:
                    st.metric("Valor Promedio", f"${liquidados_hogar_f['VALOR INDEMNIZADO'].mean():,.2f}")
                    st.metric("Plazo Promedio Crédito", f"{liquidados_hogar_f['PLAZO'].mean():.1f} meses")
                
                # Distribución de valores indemnizados
                st.header("💰 Análisis de Valores Indemnizados")
                
                fig = plt.figure(figsize=(10, 5))
                sns.histplot(liquidados_hogar_f['VALOR INDEMNIZADO'], bins=bins_hist_hogar, kde=True, color='darkblue')
                plt.title('Distribución de Valores Indemnizados')
                plt.xlabel('Valor Indemnizado')
                plt.ylabel('Frecuencia')
                st.pyplot(fig)
                
                # Análisis de causas
                st.header("🌧️ Análisis de Causas de Siniestros")
                
                top_causas_hogar = liquidados_hogar_f['CAUSA SINIESTRO'].value_counts().nlargest(top_n_hogar)
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=top_causas_hogar.values, y=top_causas_hogar.index, palette='Blues_r')
                plt.title(f'Top {top_n_hogar} Causas de Siniestros de Hogar')
                plt.xlabel('Cantidad de Reclamos')
                st.pyplot(fig)
                
                # Análisis temporal
                st.header("⏱️ Análisis de Tiempos de Respuesta")
                
                col_t1, col_t2 = st.columns(2)
                
                with col_t1:
                    fig = plt.figure(figsize=(10, 5))
                    sns.histplot(liquidados_hogar_f['TIEMPO_RESPUESTA'].dropna(), bins=20, kde=True, color='orange')
                    plt.title('Distribución - Días hasta Notificación')
                    plt.xlabel('Días')
                    plt.ylabel('Frecuencia')
                    st.pyplot(fig)
                
                with col_t2:
                    fig = plt.figure(figsize=(10, 5))
                    sns.histplot(liquidados_hogar_f['TIEMPO_CIERRE'].dropna(), bins=20, kde=True, color='red')
                    plt.title('Distribución - Días hasta Cierre')
                    plt.xlabel('Días')
                    plt.ylabel('Frecuencia')
                    st.pyplot(fig)
                
                # Tabla resumen de estadísticas
                with st.expander("📊 Ver estadísticas detalladas de tiempos"):
                    stats_df = pd.DataFrame({
                        'Métrica': ['Notificación', 'Cierre'],
                        'Promedio (días)': [
                            liquidados_hogar_f['TIEMPO_RESPUESTA'].mean(),
                            liquidados_hogar_f['TIEMPO_CIERRE'].mean()
                        ],
                        'Mediana (días)': [
                            liquidados_hogar_f['TIEMPO_RESPUESTA'].median(),
                            liquidados_hogar_f['TIEMPO_CIERRE'].median()
                        ],
                        'Mínimo (días)': [
                            liquidados_hogar_f['TIEMPO_RESPUESTA'].min(),
                            liquidados_hogar_f['TIEMPO_CIERRE'].min()
                        ],
                        'Máximo (días)': [
                            liquidados_hogar_f['TIEMPO_RESPUESTA'].max(),
                            liquidados_hogar_f['TIEMPO_CIERRE'].max()
                        ]
                    })
                    st.dataframe(stats_df.style.format({
                        'Promedio (días)': '{:.1f}',
                        'Mediana (días)': '{:.1f}',
                        'Mínimo (días)': '{:.0f}',
                        'Máximo (días)': '{:.0f}'
                    }), use_container_width=True)
                
            else:
                st.info("No hay reclamos liquidados para el año seleccionado")
            
            # Reclamos negados y en proceso
            visualizar_estadisticas_pendientes(negados_hogar_f, titulo="Reclamos de Hogar Negados")
            visualizar_estadisticas_pendientes(procesados_hogar_f, titulo="Reclamos de Hogar en Proceso")
            
            # Datos crudos
            st.header("📄 Datos Crudos - Hogar")
            st.dataframe(df_hogar_año, use_container_width=True)
            
        else:
            st.warning("No se pudo cargar el archivo. Verifica el formato.")
    else:
        st.info("👋 Por favor sube un archivo Excel de reclamos de hogar para comenzar")
            st.warning("No se pudo cargar el archivo. Verifica el formato.")
    else:
        st.info("👋 Por favor sube un archivo Excel de reclamos de hogar para comenzar")

