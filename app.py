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
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color="#00CC96")))
            fig.add_trace(go.Scatter(x=df['data'], y=df[ratio_col[0]], name="Ratio", yaxis="y2", line=dict(color="#FFA15A")))
            fig.update_layout(template="plotly_dark", yaxis=dict(title="Цена"), yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        fig_vp = go.Figure()
        fig_vp.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
        fig_vp.add_trace(go.Histogram(y=df['price'], orientation='h', nbinsy=50, xaxis='x2', marker=dict(color='rgba(100,150,250,0.2)')))
        fig_vp.update_layout(template="plotly_dark", xaxis=dict(domain=[0.1, 1]), xaxis2=dict(overlaying='x', side='top', domain=[0, 0.15]), height=600)
        st.plotly_chart(fig_vp, use_container_width=True)

    with tabs[2]:
        if sup_col:
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
            fig_s.add_trace(go.Scatter(x=df['data'], y=df[sup_col[0]], name="Supply", yaxis="y2"))
            fig_s.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig_s, use_container_width=True)

    with tabs[3]:
        st.subheader("📅 Минимална и Максимална Цена по Години")
        df['year'] = df['data'].dt.year
        yearly_price = df.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly_price['разлика'] = yearly_price['max'] - yearly_price['min']
        yearly_price['x (ръст)'] = yearly_price['max'] / yearly_price['min']
        
        # Графика
        fig_y = px.bar(yearly_price, x='year', y=['min', 'max'], barmode='group', template="plotly_dark", color_discrete_map={'min': '#EF553B', 'max': '#00CC96'}, text_auto='.2f')
        st.plotly_chart(fig_y, use_container_width=True, key="yearly_chart_fixed")
        
        # Таблица
        st.dataframe(yearly_price.style.format({"min": "{:,.2f}", "max": "{:,.2f}", "разлика": "{:,.2f}", "x (ръст)": "{:,.2f}x"}), use_container_width=True)

        # --- НОВИТЕ МЕТРИКИ ---
        avg_diff = yearly_price['разлика'].mean()
        avg_x = yearly_price['x (ръст)'].mean()
        avg_pct = (avg_x - 1) * 100
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Средна разлика", f"${avg_diff:,.2f}")
        col_b.metric("Среден ръст (x)", f"{avg_x:,.2f}x")
        col_c.metric("Среден ръст (%)", f"{avg_pct:,.2f}%")
        # ----------------------

    with tabs[4]:
        df['MA50'] = df['price'].rolling(50).mean()
        df['MA200'] = df['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.4))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA200'], name="MA 200", line=dict(color="red")))
        fig_ma.update_layout(template="plotly_dark", height=600)
        st.plotly_chart(fig_ma, use_container_width=True)

    with tabs[5]:
        if mcap_col and sup_col:
            st.plotly_chart(px.scatter(df, x=sup_col[0], y=mcap_col[0], color='price', template="plotly_dark"), use_container_width=True)

    with tabs[6]:
        df['vol'] = df['price'].pct_change() * 100
        fig_sync = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig_sync.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color="#00CC96")), row=1, col=1)
        fig_sync.add_trace(go.Scatter(x=df['data'], y=df['vol'], name="Волатилност %", line=dict(color="#FFA15A")), row=2, col=1)
        for h in [0, 5, 10, -5, -10]:
            fig_sync.add_hline(y=h, line_dash="dash", line_color="rgba(255,255,255,0.2)", row=2, col=1)
        fig_sync.update_layout(template="plotly_dark", height=700)
        st.plotly_chart(fig_sync, use_container_width=True)

    with tabs[7]:
        if mcap_col and sup_col:
            min_mcap = df[mcap_col[0]].min()
            last_supply = df[sup_col[0]].iloc[-1]
            m_list = [5, 10, 15, 20, 30, 40, 50]
            cols = st.columns(len(m_list))
            for i, m in enumerate(m_list):
                tp = math.floor((min_mcap * m) / last_supply)
                cols[i].metric(f"x{m}", f"${tp:,}")

    with tabs[8]:
        if mcap_col and sup_col:
            max_mcap = df[mcap_col[0]].max()
            last_supply = df[sup_col[0]].iloc[-1]
            drops = [-60, -70, -80, -90, -95]
            cols = st.columns(len(drops))
            for i, d in enumerate(drops):
                t_price = math.floor((max_mcap * (100 + d) / 100) / last_supply)
                cols[i].metric(f"{d}%", f"${t_price:,}")

    with tabs[9]:
        df['EMA55'] = df['price'].ewm(span=55, adjust=False).mean()
        # Опростена логика за Bull/Bear Mean за стабилност
        b_mean = df[df['price'] > df['EMA55']]['price'].mean()
        s_mean = df[df['price'] < df['EMA55']]['price'].mean()
        c1, c2 = st.columns(2)
        c1.metric("Bull Mean", f"${math.floor(b_mean or 0):,}")
        c2.metric("Bear Mean", f"${math.floor(s_mean or 0):,}")
        fig_e = go.Figure()
        fig_e.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.3))
        fig_e.add_trace(go.Scatter(x=df['data'], y=df['EMA55'], name="EMA 55"))
        fig_e.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_e, use_container_width=True)

    st.write("---")
    st.metric("Макс Цена (4г)", f"${df['price'].max():,.2f}")

else:
    st.info("👈 Качете .ods файл от страничната лента.")
