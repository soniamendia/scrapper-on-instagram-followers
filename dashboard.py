import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuración de la página de Streamlit
st.set_page_config(page_title='Follower Comparative Analysis', layout='wide')

## Cambiar el color de fondo
st.markdown(
    """
    <style>
    .stApp {
        background-color: #fdfcee;
    }
    .stSidebar {
        background-color: #ffffff !important;
    }
    .css-1cpxqw2, .css-1d391kg, .css-2b097c-container {
        background-color: #e8e8e8 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #333333;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Conectar a las bases de datos
conn1 = sqlite3.connect('seguidores.db')
conn2 = sqlite3.connect('seguidores_2.db')
conn_common = sqlite3.connect('seguidores_comunes.db')

# Leer las tablas
seguidores_df_1 = pd.read_sql_query("SELECT * FROM seguidores", conn1)
hourly_stats_df_1 = pd.read_sql_query("SELECT * FROM hourly_stats ORDER BY timestamp", conn1)

seguidores_df_2 = pd.read_sql_query("SELECT * FROM seguidores", conn2)
hourly_stats_df_2 = pd.read_sql_query("SELECT * FROM hourly_stats ORDER BY timestamp", conn2)

seguidores_comunes_df = pd.read_sql_query("SELECT * FROM seguidores_comunes", conn_common)

# Cerrar las conexiones
conn1.close()
conn2.close()
conn_common.close()

# Convertir 'timestamp' a tipo datetime
hourly_stats_df_1['timestamp'] = pd.to_datetime(hourly_stats_df_1['timestamp'])
hourly_stats_df_2['timestamp'] = pd.to_datetime(hourly_stats_df_2['timestamp'])

# Selector de cuentas en la barra lateral
with st.sidebar:
    st.header('Control Panel')
    selected_accounts = st.multiselect(
        "Select accounts for analysis:",
        ['@caricakez', '@caricanread'],
        default=['@caricakez', '@caricanread']
    )

# Filtrar datos según las fechas seleccionadas
start_date = datetime.now() - timedelta(days=10)
end_date = datetime.now()
start_time = datetime.combine(start_date, datetime.min.time())
end_time = datetime.combine(end_date, datetime.max.time())

filtered_stats_df_1 = hourly_stats_df_1[
    (hourly_stats_df_1['timestamp'] >= start_time) & 
    (hourly_stats_df_1['timestamp'] <= end_time)
].copy()

filtered_stats_df_2 = hourly_stats_df_2[
    (hourly_stats_df_2['timestamp'] >= start_time) & 
    (hourly_stats_df_2['timestamp'] <= end_time)
].copy()

# Crear pestañas para la navegación
st.title('Follower Comparative Analysis')
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Home Page", "General Statistics", "Hourly Growth",
    "Cumulative Growth", "Today´s News", "Followers List"
])

# Home Page
tab1.subheader('General Statistics')

# Seguidores generales
total_seguidores_1 = len(seguidores_df_1)
verificados_1 = seguidores_df_1['isVerified'].sum()
porcentaje_verificados_1 = (verificados_1 / total_seguidores_1) * 100 if total_seguidores_1 > 0 else 0

total_seguidores_2 = len(seguidores_df_2)
verificados_2 = seguidores_df_2['isVerified'].sum()
porcentaje_verificados_2 = (verificados_2 / total_seguidores_2) * 100 if total_seguidores_2 > 0 else 0

col1, col2, col3, col4 = tab1.columns(4)
if '@caricakez' in selected_accounts:
    with col1:
        col1.metric(label="Total Followers - @caricakez", value=total_seguidores_1)
    with col2:
        col2.metric(label="Verified Followers - @caricakez", value=f"{verificados_1} ({porcentaje_verificados_1:.2f}%)")
if '@caricanread' in selected_accounts:
    with col3:
        col3.metric(label="Total Followers - @caricanread", value=total_seguidores_2)
    with col4:
        col4.metric(label="Verified Followers - @caricanread", value=f"{verificados_2} ({porcentaje_verificados_2:.2f}%)")

# Nuevos Seguidores Hoy (sección agregada)
#tab1.subheader("Today's New Followers and Common Followers")

# Filtrar los seguidores nuevos del día de hoy
today = datetime.now().date()
start_of_today = datetime.combine(today, datetime.min.time())
end_of_today = datetime.combine(today, datetime.max.time())

# Seguidores nuevos hoy para ambas cuentas
new_followers_today_1 = filtered_stats_df_1[
    (filtered_stats_df_1['timestamp'] >= start_of_today) & 
    (filtered_stats_df_1['timestamp'] <= end_of_today)
]['new_followers'].sum()

new_followers_today_2 = filtered_stats_df_2[
    (filtered_stats_df_2['timestamp'] >= start_of_today) & 
    (filtered_stats_df_2['timestamp'] <= end_of_today)
]['new_followers'].sum()

# Verificar si la columna 'timestamp' existe en la tabla de seguidores comunes
if 'timestamp' in seguidores_comunes_df.columns:
    # Seguidores comunes nuevos del día de hoy
    new_common_followers_today = seguidores_comunes_df[
        (seguidores_comunes_df['timestamp'] >= start_of_today) & 
        (seguidores_comunes_df['timestamp'] <= end_of_today)
    ].shape[0]  # Contar el número de seguidores comunes nuevos
else:
    new_common_followers_today = 0  # Si no hay timestamp, no se puede filtrar por el día de hoy

# Mostrar el número de nuevos seguidores hoy y cuántos son comunes
total_new_followers_today = new_followers_today_1 + new_followers_today_2

# Mostrar el mensaje con letras más grandes y los números resaltados
tab1.markdown(f"""
    <div style="font-size:24px;">
        <strong>Today you’ve got</strong> <span style="font-size:32px; color:#f76a6a;"><strong>{total_new_followers_today}</strong></span> <strong>total followers</strong>
    </div>
    <div style="font-size:24px;">
        <strong>and</strong> <span style="font-size:32px; color:#f5d963;"><strong>{new_common_followers_today}</strong></span> <strong>are common followers</strong>
    </div>
    """, unsafe_allow_html=True)

# Hourly Growth of New Followers (Comparison)
tab1.subheader('Hourly Growth of New Followers')

# Crear las columnas para la gráfica y las etiquetas
col1, col2 = tab1.columns([4, 1])

# Filtrar la primera descarga masiva (se elimina el primer registro de descarga masiva)
# Vamos a asumir que la primera descarga masiva es el primer registro en la tabla y lo eliminamos
if not filtered_stats_df_1.empty:
    filtered_stats_df_1 = filtered_stats_df_1[filtered_stats_df_1['new_followers'] < 4000]  # Eliminar el valor masivo para @caricakez
if not filtered_stats_df_2.empty:
    filtered_stats_df_2 = filtered_stats_df_2[filtered_stats_df_2['new_followers'] < 4000]  # Eliminar el valor masivo para @caricanread

# Crear la gráfica en col1
with col1:
    fig1 = go.Figure()

    # Línea para @caricakez
    if '@caricakez' in selected_accounts and not filtered_stats_df_1.empty:
        fig1.add_trace(go.Scatter(x=filtered_stats_df_1['timestamp'], y=filtered_stats_df_1['new_followers'],
                                  mode='lines+markers', name='@caricakez', line=dict(color='#f76a6a')))

    # Línea para @caricanread
    if '@caricanread' in selected_accounts and not filtered_stats_df_2.empty:
        fig1.add_trace(go.Scatter(x=filtered_stats_df_2['timestamp'], y=filtered_stats_df_2['new_followers'],
                                  mode='lines+markers', name='@caricanread', line=dict(color='#f5d963')))

    # Personalizar el layout de la gráfica para limitar el rango del eje Y
    if fig1.data:
        fig1.update_layout(title=' ',
                           paper_bgcolor='#fdfcee',
                           plot_bgcolor='#fdfcee',
                           xaxis_title='Date and Time', yaxis_title='New Followers',
                           yaxis=dict(range=[0, 100]),  # Limitar el eje Y a un máximo de 300
                           xaxis=dict(rangeslider=dict(visible=True)))
        col1.plotly_chart(fig1, key='fig1_home_filtered')
    else:
        col1.write("No data available for the selected range.")

# Mostrar etiquetas adicionales en col2 para reforzar la información
with col2:
    col2.subheader('New Followers Today')
    
    # Calcular nuevos seguidores hoy
    new_followers_today_1 = filtered_stats_df_1[
        (filtered_stats_df_1['timestamp'] >= start_of_today) & 
        (filtered_stats_df_1['timestamp'] <= end_of_today)
    ]['new_followers'].sum()

    new_followers_today_2 = filtered_stats_df_2[
        (filtered_stats_df_2['timestamp'] >= start_of_today) & 
        (filtered_stats_df_2['timestamp'] <= end_of_today)
    ]['new_followers'].sum()

    # Mostrar etiquetas
    col2.markdown(f"<span style='color:#f76a6a;'>@caricakez:</span> <strong>{new_followers_today_1} followers</strong>", unsafe_allow_html=True)
    col2.markdown(f"<span style='color:#f5d963;'>@caricanread:</span> <strong>{new_followers_today_2} followers</strong>", unsafe_allow_html=True)

# Cumulative Follower Growth
tab1.subheader('Cumulative Follower Growth')
fig2 = go.Figure()

# Agregar los datos de @caricakez
if '@caricakez' in selected_accounts and not filtered_stats_df_1.empty:
    filtered_stats_df_1 = filtered_stats_df_1.sort_values('timestamp')
    filtered_stats_df_1['total_followers'] = filtered_stats_df_1['new_followers'].cumsum()
    fig2.add_trace(go.Scatter(x=filtered_stats_df_1['timestamp'], y=filtered_stats_df_1['total_followers'],
                              mode='lines+markers', name='@caricakez', line=dict(color='#f76a6a')))

# Agregar los datos de @caricanread
if '@caricanread' in selected_accounts and not filtered_stats_df_2.empty:
    filtered_stats_df_2 = filtered_stats_df_2.sort_values('timestamp')
    filtered_stats_df_2['total_followers'] = filtered_stats_df_2['new_followers'].cumsum()
    fig2.add_trace(go.Scatter(x=filtered_stats_df_2['timestamp'], y=filtered_stats_df_2['total_followers'],
                              mode='lines+markers', name='@caricanread', line=dict(color='#f5d963')))

# Personalizar la gráfica, eliminando el range slider
if fig2.data:
    fig2.update_layout(
        title='',  # Sin título
        paper_bgcolor='#fdfcee',
        plot_bgcolor='#fdfcee',
        xaxis=dict(rangeslider=dict(visible=False)),  # Desactivar el range slider
        showlegend=True  # Mantener la leyenda para identificar cada cuenta
    )
    tab1.plotly_chart(fig2, key='fig2_home')
else:
    tab1.write("No data available for the selected range.")

# Follower List of Both Accounts
tab1.subheader('Total Followers List')

# Verificar que la columna 'isVerified' exista en ambos DataFrames
if 'isVerified' in seguidores_df_1.columns and 'isVerified' in seguidores_df_2.columns:

    # Filtrar por verificación en la barra lateral
    verification_filter_home = tab1.radio("Filter Followers by Verification:", ("All", "Verified", "No Verified"), key='verification_filter_home')

    # Unir ambos DataFrames y eliminar duplicados
    todos_seguidores_df_home = pd.concat([seguidores_df_1, seguidores_df_2]).drop_duplicates(subset='userName').reset_index(drop=True)

    # Aplicar el filtro según la opción seleccionada
    if verification_filter_home == "Verified":
        todos_seguidores_df_home = todos_seguidores_df_home[todos_seguidores_df_home['isVerified'] == 1]
    elif verification_filter_home == "No Verified":
        todos_seguidores_df_home = todos_seguidores_df_home[todos_seguidores_df_home['isVerified'] == 0]

    # Mostrar la lista filtrada
    if not todos_seguidores_df_home.empty:
        tab1.dataframe(todos_seguidores_df_home[['userName', 'profileUrl', 'isVerified']], key='followers_list_home')
    else:
        tab1.write("No followers to display.")
else:
    tab1.write("The 'isVerified' column is missing in one of the datasets.")

#TABS


# General Statistics (in another tab)
tab2.header('General Statistics')
col1, col2, col3, col4 = tab2.columns(4)
if '@caricakez' in selected_accounts:
    with col1:
        col1.metric(label="Total Followers - @caricakez", value=total_seguidores_1)
    with col2:
        col2.metric(label="Verified Followers - @caricakez", value=f"{verificados_1} ({porcentaje_verificados_1:.2f}%)")
if '@caricanread' in selected_accounts:
    with col3:
        col3.metric(label="Total Followers - @caricanread", value=total_seguidores_2)
    with col4:
        col4.metric(label="Verified Followers - @caricanread", value=f"{verificados_2} ({porcentaje_verificados_2:.2f}%)")

# Hourly Growth of New Followers (Comparison)
tab3.header('Hourly Growth of New Followers (Comparison)')

# Crear las columnas para la gráfica y las etiquetas
col1, col2 = tab3.columns([4, 1])

# Filtrar la primera descarga masiva (se elimina el primer registro de descarga masiva)
# Vamos a asumir que la primera descarga masiva es el primer registro en la tabla y lo eliminamos
if not filtered_stats_df_1.empty:
    filtered_stats_df_1 = filtered_stats_df_1[filtered_stats_df_1['new_followers'] < 4000]  # Eliminar el valor masivo para @caricakez
if not filtered_stats_df_2.empty:
    filtered_stats_df_2 = filtered_stats_df_2[filtered_stats_df_2['new_followers'] < 4000]  # Eliminar el valor masivo para @caricanread

# Crear la gráfica en col1
with col1:
    fig1 = go.Figure()

    # Agregar línea de nuevos seguidores para @caricakez
    if '@caricakez' in selected_accounts and not filtered_stats_df_1.empty:
        fig1.add_trace(go.Scatter(x=filtered_stats_df_1['timestamp'], y=filtered_stats_df_1['new_followers'],
                                  mode='lines+markers', name='@caricakez', line=dict(color='#f76a6a')))

    # Agregar línea de nuevos seguidores para @caricanread
    if '@caricanread' in selected_accounts and not filtered_stats_df_2.empty:
        fig1.add_trace(go.Scatter(x=filtered_stats_df_2['timestamp'], y=filtered_stats_df_2['new_followers'],
                                  mode='lines+markers', name='@caricanread', line=dict(color='#f5d963')))

    # Personalizar el layout de la gráfica para limitar el rango del eje Y
    if fig1.data:
        fig1.update_layout(title=' ',
                           paper_bgcolor='#fdfcee',
                           plot_bgcolor='#fdfcee',
                           xaxis_title='Date and Time', yaxis_title='New Followers',
                           yaxis=dict(range=[0, 100]),  # Limitar el eje Y a un máximo de 100
                           xaxis=dict(rangeslider=dict(visible=True)))
        col1.plotly_chart(fig1, key='fig1_tab3_filtered')
    else:
        col1.write("No data available for the selected range.")

# Mostrar etiquetas adicionales en col2 para reforzar la información
with col2:
    col2.subheader('New Followers Today')
    
    # Calcular nuevos seguidores hoy
    new_followers_today_1 = filtered_stats_df_1[
        (filtered_stats_df_1['timestamp'] >= start_of_today) & 
        (filtered_stats_df_1['timestamp'] <= end_of_today)
    ]['new_followers'].sum()

    new_followers_today_2 = filtered_stats_df_2[
        (filtered_stats_df_2['timestamp'] >= start_of_today) & 
        (filtered_stats_df_2['timestamp'] <= end_of_today)
    ]['new_followers'].sum()

    # Mostrar etiquetas
    col2.markdown(f"<span style='color:#f76a6a;'>@caricakez:</span> <strong>{new_followers_today_1} followers</strong>", unsafe_allow_html=True)
    col2.markdown(f"<span style='color:#f5d963;'>@caricanread:</span> <strong>{new_followers_today_2} followers</strong>", unsafe_allow_html=True)

# Cumulative Follower Growth
tab4.header('Cumulative Follower Growth')
fig2 = go.Figure()

# Agregar los datos de @caricakez
if '@caricakez' in selected_accounts and not filtered_stats_df_1.empty:
    filtered_stats_df_1 = filtered_stats_df_1.sort_values('timestamp')
    filtered_stats_df_1['total_followers'] = filtered_stats_df_1['new_followers'].cumsum()
    fig2.add_trace(go.Scatter(x=filtered_stats_df_1['timestamp'], y=filtered_stats_df_1['total_followers'],
                              mode='lines+markers', name='@caricakez', line=dict(color='#f76a6a')))

# Agregar los datos de @caricanread
if '@caricanread' in selected_accounts and not filtered_stats_df_2.empty:
    filtered_stats_df_2 = filtered_stats_df_2.sort_values('timestamp')
    filtered_stats_df_2['total_followers'] = filtered_stats_df_2['new_followers'].cumsum()
    fig2.add_trace(go.Scatter(x=filtered_stats_df_2['timestamp'], y=filtered_stats_df_2['total_followers'],
                              mode='lines+markers', name='@caricanread', line=dict(color='#f5d963')))

# Personalizar la gráfica, eliminando el range slider
if fig2.data:
    fig2.update_layout(
        title='',  # Sin título
        paper_bgcolor='#fdfcee',
        plot_bgcolor='#fdfcee',
        xaxis_title='Date and Time', yaxis_title='Cumulative Followers',
        xaxis=dict(rangeslider=dict(visible=False)),  # Desactivar el range slider
        showlegend=True  # Mantener la leyenda para identificar cada cuenta
    )
    tab4.plotly_chart(fig2, key='fig2_tab4')
else:
    tab4.write("No data available for the selected range.")

# Common Followers (modified to show new followers today and common new followers)
tab5.header('Today´s New Followers and Common Followers')

# Filtrar los seguidores nuevos del día de hoy
today = datetime.now().date()
start_of_today = datetime.combine(today, datetime.min.time())
end_of_today = datetime.combine(today, datetime.max.time())

# Seguidores nuevos hoy para ambas cuentas
new_followers_today_1 = filtered_stats_df_1[
    (filtered_stats_df_1['timestamp'] >= start_of_today) & 
    (filtered_stats_df_1['timestamp'] <= end_of_today)
]['new_followers'].sum()

new_followers_today_2 = filtered_stats_df_2[
    (filtered_stats_df_2['timestamp'] >= start_of_today) & 
    (filtered_stats_df_2['timestamp'] <= end_of_today)
]['new_followers'].sum()

# Verificar si la columna 'timestamp' existe en la tabla de seguidores comunes
if 'timestamp' in seguidores_comunes_df.columns:
    # Seguidores comunes nuevos del día de hoy
    new_common_followers_today = seguidores_comunes_df[
        (seguidores_comunes_df['timestamp'] >= start_of_today) & 
        (seguidores_comunes_df['timestamp'] <= end_of_today)
    ].shape[0]  # Contar el número de seguidores comunes nuevos
else:
    new_common_followers_today = 0  # Si no hay timestamp, no se puede filtrar por el día de hoy

# Mostrar el número de nuevos seguidores hoy y cuántos son comunes
total_new_followers_today = new_followers_today_1 + new_followers_today_2

# Mostrar el mensaje con letras más grandes y los números resaltados
tab5.markdown(f"""
    <div style="font-size:24px;">
        <strong>Today you’ve got</strong> <span style="font-size:32px; color:#f76a6a;"><strong>{total_new_followers_today}</strong></span> <strong>total followers</strong>
    </div>
    <div style="font-size:24px;">
        <strong>and</strong> <span style="font-size:32px; color:#f5d963;"><strong>{new_common_followers_today}</strong></span> <strong>are common followers</strong>
    </div>
    """, unsafe_allow_html=True)

# Calcular las tasas de crecimiento
if total_new_followers_today > 0:
    crecimiento_ratio_1 = new_followers_today_1 / total_new_followers_today
    crecimiento_ratio_2 = new_followers_today_2 / total_new_followers_today
else:
    crecimiento_ratio_1, crecimiento_ratio_2 = 0, 0

# Crear la gráfica de comparación del crecimiento por cuenta
fig3 = go.Figure()
if '@caricanread' in selected_accounts:
    fig3.add_trace(go.Bar(y=['@caricanread'], x=[crecimiento_ratio_2],
                          orientation='h', marker=dict(color='#f5d963')))
if '@caricakez' in selected_accounts:
    fig3.add_trace(go.Bar(y=['@caricakez'], x=[crecimiento_ratio_1],
                          orientation='h', marker=dict(color='#f76a6a')))
fig3.update_traces(width=0.4)  # Hacer las barras más delgadas
fig3.update_layout(title='Comparison of New Follower Growth Between Accounts',
                   paper_bgcolor='#fdfcee',
                   plot_bgcolor='#fdfcee',
                   showlegend=False,
                   xaxis_title='Growth Ratio', yaxis_title='Accounts')
tab5.plotly_chart(fig3, key='fig3_tab5')


# Follower List of Both Accounts
tab6.header('Total Followers List')

# Verificar que la columna 'isVerified' exista en ambos DataFrames
if 'isVerified' in seguidores_df_1.columns and 'isVerified' in seguidores_df_2.columns:
    
    # Filtrar por verificación en la barra lateral
    verification_filter = tab6.radio("Filter Followers by Verification:", ("All", "Verified", "No Verified"))
    
    # Unir ambos DataFrames
    todos_seguidores_df = pd.concat([seguidores_df_1, seguidores_df_2]).drop_duplicates(subset='userName').reset_index(drop=True)
    
    # Aplicar el filtro según la opción seleccionada
    if verification_filter == "Verified":
        todos_seguidores_df = todos_seguidores_df[todos_seguidores_df['isVerified'] == 1]
    elif verification_filter == "No Verified":
        todos_seguidores_df = todos_seguidores_df[todos_seguidores_df['isVerified'] == 0]
    
    # Mostrar la lista filtrada
    if not todos_seguidores_df.empty:
        tab6.dataframe(todos_seguidores_df[['userName', 'profileUrl', 'isVerified']])
    else:
        tab6.write("No followers to display.")
else:
    tab6.write("The 'isVerified' column is missing in one of the datasets.")