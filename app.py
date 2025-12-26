import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import math

st.set_page_config(page_title="Анализатор", layout="wide")

# ИНИЦИАЛИЗАЦИЯ НА ПАМЕТТА (Session State)
if 'df' not in st.session_state:
    st.session_state['df'] = None

st.title("📊 Пълен Анализ: Всички Инструменти")

# --- СТРАНИЧНА ЛЕНТА ---
st.sidebar.header("Качване на данни")
uploaded_file = st.sidebar.file_uploader("Добави .ods файл", type=["ods"])

# Прочитаме файла само ако потребителят е качил нов такъв
if uploaded_file is not None:
    try:
        new_df = pd.read_excel(uploaded_file, engine='odf')
        new_df['data'] = pd.to_datetime(new_df['data'], errors='coerce')
        new_df = new_df.dropna(subset=['data'])
        st.session_state['df'] = new_df # Запазваме в паметта
    except Exception as e:
        st.error(f"Грешка при четене на файла: {e}")

# Използваме данните от паметта, за да не се губят при смяна на страници
df = st.session_state['df']

if df is not None:
    # Филтрираме данните за последните 4 години
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df_filtered = df[df['data'] > four_years_ago].sort_values('data').copy()

    # Търсене на колони
    mcap_col = [c for c in df_filtered.columns if 'market_cap' in c.lower()]
    sup_col = [c for c in df_filtered.columns if 'supply' in c.lower() or 'circulating' in c.lower()]
    ratio_col = [c for c in df_filtered.columns if 'price' in c.lower() and '/' in c.lower()]

    tabs = st.tabs(["🔗 Ratio", "🏆 Укрупняване", "📈 Supply", "📅 Годишни", "📉 MA", "🎯 Cap vs Sup", "⚡ Волатилност", "💰 Target", "📉 Risk", "⚖️ EMA 55 Mean"])

    # 4. Годишни (Коригирано без ValueError стилове)
    with tabs[3]:
        st.subheader("📅 Годишни Екстремуми")
        df_filtered['year'] = df_filtered['data'].dt.year
        yearly_price = df_filtered.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly_price['разлика'] = yearly_price['max'] - yearly_price['min']
        yearly_price['x (ръст)'] = yearly_price['max'] / yearly_price['min']
        st.dataframe(yearly_price, use_container_width=True)

    # Тук следват останалите табове (MA, Volatility и т.н.) - ползвай df_filtered
    # (За краткост не ги повтарям всички, но логиката е същата като в предишните ни версии)
    
    with tabs[4]: # Пример за MA
        df_ma = df_filtered.copy()
        df_ma['MA50'] = df_ma['price'].rolling(50).mean()
        df_ma['MA200'] = df_ma['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df_ma['data'], y=df_ma['price'], name="Цена", opacity=0.4))
        fig_ma.add_trace(go.Scatter(x=df_ma['data'], y=df_ma['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_ma.add_trace(go.Scatter(x=df_ma['data'], y=df_ma['MA200'], name="MA 200", line=dict(color="red")))
        fig_ma.update_layout(template="plotly_dark", height=600)
        st.plotly_chart(fig_ma, use_container_width=True)

    st.write("---")
    st.write(f"Макс цена в периода: {df_filtered['price'].max():.2f} | Мин цена: {df_filtered['price'].min():.2f}")

else:
    st.info("👈 Моля, качи .ods файл от менюто вляво.")
