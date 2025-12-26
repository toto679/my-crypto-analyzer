import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import math

st.set_page_config(page_title="Анализатор", layout="wide")

# 1. Инициализираме паметта
if 'df' not in st.session_state:
    st.session_state['df'] = None

st.title("📊 Пълен Анализ: Всички Инструменти")

# 2. Странична лента за качване
uploaded_file = st.sidebar.file_uploader("Добави .ods файл", type=["ods"])

if uploaded_file is not None:
    try:
        df_new = pd.read_excel(uploaded_file, engine='odf')
        df_new['data'] = pd.to_datetime(df_new['data'], errors='coerce')
        df_new = df_new.dropna(subset=['data'])
        st.session_state['df'] = df_new
    except Exception as e:
        st.error(f"Грешка при четене: {e}")

# Използваме данните от паметта
df_main = st.session_state['df']

if df_main is not None:
    # Глобален филтър за 4 години
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df = df_main[df_main['data'] > four_years_ago].sort_values('data').copy()

    # Търсене на колони
    mcap_col = [c for c in df.columns if 'market_cap' in c.lower()]
    sup_col = [c for c in df.columns if 'supply' in c.lower() or 'circulating' in c.lower()]
    ratio_col = [c for c in df.columns if 'price' in c.lower() and '/' in c.lower()]

    # ДЕФИНИРАНЕ НА ТАБОВЕТЕ
    tabs = st.tabs([
        "🔗 Ratio", "🏆 Укрупняване", "📈 Supply", "📅 Годишни", 
        "📉 MA", "🎯 Cap vs Sup", "⚡ Волатилност", "💰 Target", "📉 Risk", "⚖️ EMA 55 Mean"
    ])

    with tabs[0]:
        if ratio_col:
            fig_0 = go.Figure()
            fig_0.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color="#00CC96")))
            fig_0.add_trace(go.Scatter(x=df['data'], y=df[ratio_col[0]], name="Ratio", yaxis="y2", line=dict(color="#FFA15A")))
            fig_0.update_layout(template="plotly_dark", yaxis=dict(title="Цена"), yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig_0, use_container_width=True, key="ratio_chart_unique")

    with tabs[1]:
        fig_1 = go.Figure()
        fig_1.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
        fig_1.add_trace(go.Histogram(y=df['price'], orientation='h', nbinsy=50, xaxis='x2', marker=dict(color='rgba(100,150,250,0.2)')))
        fig_1.update_layout(template="plotly_dark", xaxis=dict(domain=[0.1, 1]), xaxis2=dict(overlaying='x', side='top', domain=[0, 0.15]), height=600)
        st.plotly_chart(fig_1, use_container_width=True, key="vol_profile_chart_unique")

    with tabs[2]:
        if sup_col:
            fig_2 = go.Figure()
            fig_2.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
            fig_2.add_trace(go.Scatter(x=df['data'], y=df[sup_col[0]], name="Supply", yaxis="y2"))
            fig_2.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig_2, use_container_width=True, key="supply_chart_unique")

    with tabs[3]:
        st.subheader("📅 Минимална и Максимална Цена по Години")
        df['year'] = df['data'].dt.year
        yearly_price = df.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly_price['разлика'] = yearly_price['max'] - yearly_price['min']
        yearly_price['x (ръст)'] = yearly_price['max'] / yearly_price['min']
        
        fig_3 = px.bar(yearly_price, x='year', y=['min', 'max'], barmode='group', template="plotly_dark", color_discrete_map={'min': '#EF553B', 'max': '#00CC96'}, text_auto='.2f')
        st.plotly_chart(fig_3, use_container_width=True, key="yearly_chart_unique")
        
        st.dataframe(yearly_price.style.format({"min": "{:,.2f}", "max": "{:,.2f}", "разлика": "{:,.2f}", "x (ръст)": "{:,.2f}x"}), use_container_width=True)

        avg_diff = yearly_price['разлика'].mean()
        avg_x = yearly_price['x (ръст)'].mean()
        avg_pct = (avg_x - 1) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Средна разлика", f"${avg_diff:,.2f}")
        c2.metric("Среден ръст (x)", f"{avg_x:,.2f}x")
        c3.metric("Среден ръст (%)", f"{avg_pct:,.2f}%")

    with tabs[4]:
        df['MA50'] = df['price'].rolling(50).mean()
        df['MA200'] = df['price'].rolling(200).mean()
        fig_4 = go.Figure()
        fig_4.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.4))
        fig_4.add_trace(go.Scatter(x=df['data'], y=df['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_4.add_trace(go.Scatter(x=df['data'], y=df['MA200'], name="MA 200", line=dict(color="red")))
        fig_4.update_layout(template="plotly_dark", height=600)
        st.plotly_chart(fig_4, use_container_width=True, key="ma_chart_unique")

    with tabs[5]:
        if mcap_col and sup_col:
            fig_5 = px.scatter(df, x=sup_col[0], y=mcap_col[0], color='price', template="plotly_dark")
            st.plotly_chart(fig_5, use_container_width=True, key="cap_sup_chart_unique")

    with tabs[6]:
        df['vol'] = df['price'].pct_change() * 100
        fig_6 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig_6.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color="#00CC96")), row=1, col=1)
        fig_6.add_trace(go.Scatter(x=df['data'], y=df['vol'], name="Волатилност %", line=dict(color="#FFA15A")), row=2, col=1)
        for h in [0, 5, 10, -5, -10]:
            fig_6.add_hline(y=h, line_dash="dash", line_color="rgba(255,255,255,0.2)", row=2, col=1)
        fig_6.update_layout(template="plotly_dark", height=700)
        st.plotly_chart(fig_6, use_container_width=True, key="volatility_chart_unique")

    with tabs[7]:
        if mcap_col and sup_col:
            min_mcap = df[mcap_col[0]].min()
            last_supply = df[sup_col[0]].iloc[-1]
            m_list = [5, 10, 15, 20, 30, 40, 50]
            cols_t = st.columns(len(m_list))
            for i, m in enumerate(m_list):
                tp = math.floor((min_mcap * m) / last_supply)
                cols_t[i].metric(f"x{m}", f"${tp:,}")

    with tabs[8]:
        if mcap_col and sup_col:
            max_mcap = df[mcap_col[0]].max()
            last_supply = df[sup_col[0]].iloc[-1]
            drops = [-60, -70, -80, -90, -95]
            cols_r = st.columns(len(drops))
            for i, d in enumerate(drops):
                t_price = math.floor((max_mcap * (100 + d) / 100) / last_supply)
                cols_r[i].metric(f"{d}%", f"${t_price:,}")

    with tabs[9]:
        df['EMA55'] = df['price'].ewm(span=55, adjust=False).mean()
        b_mean = df[df['price'] > df['EMA55']]['price'].mean()
        s_mean = df[df['price'] < df['EMA55']]['price'].mean()
        ca, cb = st.columns(2)
        ca.metric("Bull Mean", f"${math.floor(b_mean or 0):,}")
        cb.metric("Bear Mean", f"${math.floor(s_mean or 0):,}")
        fig_9 = go.Figure()
        fig_9.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.3))
        fig_9.add_trace(go.Scatter(x=df['data'], y=df['EMA55'], name="EMA 55"))
        fig_9.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_9, use_container_width=True, key="ema_mean_chart_unique")

    st.write("---")
    st.metric("Макс Цена (4г)", f"${df['price'].max():,.2f}")

else:
    st.info("👈 Качете .ods файл от страничната лента.")
