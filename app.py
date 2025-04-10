import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from folium.plugins import HeatMap, MarkerCluster
import folium
import time
from io import BytesIO
from tqdm import tqdm
from streamlit_folium import folium_static

# Função para geocodificar endereços
geolocator = Nominatim(user_agent="incident_mapper")

def geocode_address(address):
    try:
        # Aumentando o tempo de espera (timeout) para 10 segundos
        location = geolocator.geocode(address, timeout=10)  
        time.sleep(2)  # Aumentando o tempo entre as requisições para 2 segundos
        if location:
            return pd.Series([location.latitude, location.longitude])
    except Exception as e:
        st.error(f"Erro ao geocodificar: {address} -> {e}")
    return pd.Series([None, None])

# Interface do Streamlit
st.title("Mapeamento de Incidentes")

# Upload do arquivo Excel
st.subheader("Faça o upload da planilha com colunas 'Motivo' 'Endereço', 'Data Abertura', 'Data Fechamento'")
uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx"])

if uploaded_file is not None:
    # Carregar a planilha
    df = pd.read_excel(uploaded_file)

    # Verificar se a coluna 'Endereço' está presente
    if 'Endereço' not in df.columns:
        st.error("A planilha precisa ter uma coluna chamada 'Endereço'.")
    else:
        st.success("Planilha carregada com sucesso!")

        # Geocodificando os endereços
        st.subheader("Geocodificando Endereços...")
        tqdm.pandas()
        df[['Latitude', 'Longitude']] = df['Endereço'].progress_apply(geocode_address)

        # Remover entradas sem geolocalização
        df = df.dropna(subset=['Latitude', 'Longitude'])

        # Criando o mapa
        st.subheader("Criando o Mapa...")
        m = folium.Map(location=[-20.3222, -40.3381], zoom_start=12)

        # HeatMap
        heat_data = df[['Latitude', 'Longitude']].values.tolist()
        HeatMap(heat_data).add_to(m)

        # Adiciona marcadores com informações personalizadas
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df.iterrows():
            popup_text = f"""
            <strong>Endereço:</strong> {row['Endereço']}<br>
            <strong>Data Abertura:</strong> {row['Data Abertura']}<br>
            <strong>Motivo:</strong> {row.get('Motivo', 'N/A')}<br>
            <strong>Data Fechamento:</strong> {row['Data Fechamento']}
            """
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(marker_cluster)

        # Gerar o mapa em HTML
        map_html = "mapa_incidentes_com_popups.html"
        df.to_excel("incidentes_com_coords.xlsx", index=False)
        m.save(map_html)

        # Exibir mapa
        st.subheader("Mapa de Incidentes")
        folium_static(m)

        # Botão para download dos arquivos
        st.download_button(
            label="Baixar Mapa como HTML",
            data=open(map_html, 'rb').read(),
            file_name="mapa_incidentes_com_popups.html",
            mime="application/octet-stream"
        )

        st.download_button(
            label="Baixar Planilha com Coordenadas",
            data=open("incidentes_com_coords.xlsx", 'rb').read(),
            file_name="incidentes_com_coords.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
