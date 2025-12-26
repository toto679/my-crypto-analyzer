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

# Ако е качен нов файл, го обновяваме в паметта
if uploaded_file is not None:
    try:
        new_df = pd.read_excel(uploaded_file, engine='odf')
        new_df['data'] = pd.to_datetime(new_df['data'], errors='coerce')
        new_df = new_df.dropna(subset=['data'])
        st.session_state['df'] = new_df
    except Exception as e:
        st.error(f"Грешка при четене на файла: {e}")

# Използваме данните от паметта
df = st.session_state['df']

if df is not None:
    # Глобален филтър за последните 4 години
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df_filtered = df[df['data'] > four_years_ago].sort_values('data').copy()

    mcap_col = [c for c in df_filtered.columns if 'market_cap' in c.lower()]
    sup_col = [c for c in df_filtered.columns if 'supply' in c.lower() or 'circulating' in c.lower()]
    ratio_col = [c for c in df_filtered.columns if 'price' in c.lower() and '/' in c.lower()]

    tabs = st.tabs(["🔗 Ratio", "🏆 Укрупняване", "📈 Supply", "📅 Годишни", "📉 MA", "🎯 Cap vs Sup", "⚡ Волатилност", "💰 Target", "📉 Risk", "⚖️ EMA 55 Mean"])

    # 1. Ratio
    with tabs[0]:
        if ratio_col:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена", line=dict(color="#00CC96")))
            fig.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered[ratio_col[0]], name="Ratio", yaxis="y2", line=dict(color="#FFA15A")))
            fig.update_layout(template="plotly_dark", yaxis=dict(title="Цена"), yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig, use_container_width=True)

    # 2. Укрупняване
    with tabs[1]:
        fig_vp = go.Figure()
        fig_vp.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена"))
        fig_vp.add_trace(go.Histogram(y=df_filtered['price'], orientation='h', nbinsy=50, xaxis='x2', marker=dict(color='rgba(100,150,250,0.2)')))
        fig_vp.update_layout(template="plotly_dark", xaxis=dict(domain=[0.1, 1]), xaxis2=dict(overlaying='x', side='top', domain=[0, 0.15]), height=600)
        st.plotly_chart(fig_vp, use_container_width=True)

    # 3. Supply
    with tabs[2]:
        if sup_col:
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена"))
            fig_s.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered[sup_col[0]], name="Supply", yaxis="y2"))
            fig_s.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig_s, use_container_width=True)

    # 4. Годишни (БЕЗ ГРЕШКИ)
    with tabs[3]:
        st.subheader("📅 Годишни Екстремуми")
        df_filtered['year'] = df_filtered['data'].dt.year
        yearly_price = df_filtered.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly_price['разлика'] = yearly_price['max'] - yearly_price['min']
        yearly_price['x (ръст)'] = yearly_price['max'] / yearly_price['min']
        st.dataframe(yearly_price, use_container_width=True)

    # 5. MA
    with tabs[4]:
        df_ma = df_filtered.copy()
        df_ma['MA50'] = df_ma['price'].rolling(50).mean()
        df_ma['MA200'] = df_ma['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df_ma['data'], y=df_ma['price'], name="Цена", opacity=0.4))
        fig_ma.add_trace(go.Scatter(x=df_ma['data'], y=df_ma['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_ma.add_trace(go.Scatter(x=df_ma['data'], y=df_ma['MA200'], name="MA 200", line=dict(color="red")))
        fig_ma.update_layout(template="plotly_dark", height=600)
        st.plotly_chart(fig_ma, use_container_width=True)

    # 6. Cap vs Sup
    with tabs[5]:
        if mcap_col and sup_col:
            st.plotly_chart(px.scatter(df_filtered, x=sup_col[0], y=mcap_col[0], color='price', template="plotly_dark"), use_container_width=True)

    # 7. Волатилност (СИНХРОНИЗИРАНИ)
    with tabs[6]:
        df_v = df_filtered.copy()
        df_v['vol'] = df_v['price'].pct_change() * 100
        fig_sync = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig_sync.add_trace(go.Scatter(x=df_v['data'], y=df_v['price'], name="Цена", line=dict(color="#00CC96")), row=1, col=1)
        fig_sync.add_trace(go.Scatter(x=df_v['data'], y=df_v['vol'], name="Волатилност %", line=dict(color="#FFA15A")), row=2, col=1)
        for h in [0, 5, 10, -5, -10]:
            fig_sync.add_hline(y=h, line_dash="dash", line_color="rgba(255,255,255,0.2)", row=2, col=1)
        fig_sync.update_layout(template="plotly_dark", height=700)
        st.plotly_chart(fig_sync, use_container_width=True)

    # 8. Target
    with tabs[7]:
        if mcap_col and sup_col:
            min_mcap = df_filtered[mcap_col[0]].min()
            last_supply = df_filtered[sup_col[0]].iloc[-1]
            m_list = [5, 10, 15, 20, 30, 40, 50]
            cols = st.columns(len(m_list))
            for i, m in enumerate(m_list):
                tp = math.floor((min_mcap * m) / last_supply)
                cols[i].metric(f"x{m}", f"${tp:,}")

    # 9. Risk
    with tabs[8]:
        if mcap_col and sup_col:
            max_mcap = df_filtered[mcap_col[0]].max()
            last_supply = df_filtered[sup_col[0]].iloc[-1]
            drops = [-60, -70, -80, -90, -95]
            cols = st.columns(len(drops))
            for i, d in enumerate(drops):
                tp = math.floor((max_mcap * (100 + d) / 100) / last_supply)
                cols[i].metric(f"{d}%", f"${tp:,}")

    # 10. EMA 55 Mean
    with tabs[9]:
        df_e = df_filtered.copy()
        df_e['EMA55'] = df_e['price'].ewm(span=55, adjust=False).mean()
        highs, lows = [], []
        curr, t_h, t_l = None, 0, float('inf')
        for i in range(len(df_e)):
            p, e = df_e['price'].iloc[i], df_e['EMA55'].iloc[i]
            if p > e:
                if curr != 'up':
                    if t_l != float('inf'): lows.append(t_l)
                    curr, t_h, t_l = 'up', p, float('inf')
                elif p > t_h: t_h = p; highs.append(p)
            else:
                if curr != 'down':
                    if t_h != 0: highs.append(t_h)
                    curr, t_l, t_h = 'down', p, 0
                elif p < t_l: t_l = p; lows.append(p)
        b_m = sum(highs)/(len(highs)+1) if highs else 0
        s_m = sum(lows)/(len(lows)+1) if lows else 0
        c1, c2 = st.columns(2)
        c1.metric("Bull Mean", f"${math.floor(b_m):,}")
        c2.metric("Bear Mean", f"${math.floor(s_m):,}")
        fig_e = go.Figure()
        fig_e.add_trace(go.Scatter(x=df_e['data'], y=df_e['price'], name="Цена", opacity=0.3))
        fig_e.add_trace(go.Scatter(x=df_e['data'], y=df_e['EMA55'], name="EMA 55"))
        fig_e.add_hline(y=b_m, line_dash="dash", line_color="green")
        fig_e.add_hline(y=s_m, line_dash="dash", line_color="red")
        fig_e.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_e, use_container_width=True)

else:
    st.info("👈 Моля, качи .ods файл от менюто вляво, за да започнем анализа.")
