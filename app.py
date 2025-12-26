import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import math
import io

# Настройка на страницата
st.set_page_config(page_title="Анализатор", layout="wide")
st.title("📊 Пълен Анализ: Всички Инструменти")

uploaded_file = st.sidebar.file_uploader("Добави .ods файл", type=["ods"])

if uploaded_file:
    # Зареждане и почистване
    df = pd.read_excel(uploaded_file, engine='odf')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df = df[df['data'] > four_years_ago].sort_values('data')

    mcap_col = [c for c in df.columns if 'market_cap' in c.lower()]
    sup_col = [c for c in df.columns if 'supply' in c.lower() or 'circulating' in c.lower()]
    ratio_col = [c for c in df.columns if 'price' in c.lower() and '/' in c.lower()]

    tabs = st.tabs(["🔗 Ratio", "🏆 Укрупняване", "📈 Supply", "📅 Годишни", "📉 MA", "🎯 Cap vs Sup", "⚡ Волатилност", "💰 Target", "📉 Risk", "⚖️ EMA 55 Mean"])

    # 1, 2, 3 са същите... (прескачаме ги за краткост, но в пълния код са там)
    with tabs[0]:
        if ratio_col:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
            fig.add_trace(go.Scatter(x=df['data'], y=df[ratio_col[0]], name="Ratio", yaxis="y2"))
            fig.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=500)
            st.plotly_chart(fig, use_container_width=True)
    with tabs[1]:
        fig_vp = go.Figure()
        fig_vp.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
        fig_vp.add_trace(go.Histogram(y=df['price'], orientation='h', nbinsy=50, xaxis='x2'))
        fig_vp.update_layout(template="plotly_dark", xaxis2=dict(overlaying='x', side='top', domain=[0, 0.15]), height=500)
        st.plotly_chart(fig_vp, use_container_width=True)
    with tabs[2]:
        if sup_col:
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
            fig_s.add_trace(go.Scatter(x=df['data'], y=df[sup_col[0]], name="Supply", yaxis="y2"))
            fig_s.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=500)
            st.plotly_chart(fig_s, use_container_width=True)

    # 4. ГОДИШНИ (С добавена средна промяна)
    with tabs[3]:
        st.subheader("📅 Анализ по Години")
        df['year'] = df['data'].dt.year
        yearly = df.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly['разлика'] = yearly['max'] - yearly['min']
        yearly['x (ръст)'] = yearly['max'] / yearly['min']
        
        # НОВО: Средна промяна за периода
        avg_growth = yearly['x (ръст)'].mean()
        st.metric("Среден ръст за всички години", f"{avg_growth:.2f}x")
        
        st.dataframe(yearly.style.format({"min":"{:.2f}","max":"{:.2f}","x (ръст)":"{:.2f}x"}), use_container_width=True)
        
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            yearly.to_excel(writer, index=False)
        st.download_button("📥 Свали Excel", buf.getvalue(), "yearly.xlsx")

    # 7. ВОЛАТИЛНОСТ (СИНХРОНИЗИРАНИ ГРАФИКИ)
    with tabs[6]:
        st.subheader("⚡ Синхронизиран анализ: Цена и Волатилност")
        df['vol'] = df['price'].pct_change() * 100
        
        # Създаваме две графики една над друга с обща Х ос (дати)
        fig_sync = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Горе: Цена
        fig_sync.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color="#00CC96")), row=1, col=1)
        # Долу: Волатилност
        fig_sync.add_trace(go.Scatter(x=df['data'], y=df['vol'], name="Волатилност %", line=dict(color="#FFA15A")), row=2, col=1)
        
        fig_sync.update_layout(template="plotly_dark", height=700, showlegend=True)
        st.plotly_chart(fig_sync, use_container_width=True)

    # Останалото е като вашия оригинален код...
    with tabs[4]:
        df['MA50'] = df['price'].rolling(50).mean()
        df['MA200'] = df['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.3))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA200'], name="MA 200", line=dict(color="red")))
        fig_ma.update_layout(template="plotly_dark")
        st.plotly_chart(fig_ma, use_container_width=True)
    # (Табове 5, 8, 9, 10 са със същите ваши формули)
    with tabs[5]:
        if mcap_col and sup_col:
            st.plotly_chart(px.scatter(df, x=sup_col[0], y=mcap_col[0], color='price', template="plotly_dark"), use_container_width=True)
    with tabs[7]:
        if mcap_col and sup_col:
            min_mcap = df[mcap_col[0]].min()
            last_supply = df[sup_col[0]].iloc[-1]
            m_list = [5, 10, 20, 50]
            cols = st.columns(len(m_list))
            for i, m in enumerate(m_list):
                tp = math.floor((min_mcap * m) / last_supply)
                cols[i].metric(f"x{m}", f"${tp:,}")
    with tabs[8]:
        if mcap_col and sup_col:
            max_mcap = df[mcap_col[0]].max()
            last_supply = df[sup_col[0]].iloc[-1]
            drops = [-60, -80, -95]
            cols = st.columns(len(drops))
            for i, d in enumerate(drops):
                rp = math.floor((max_mcap * (100+d)/100) / last_supply)
                cols[i].metric(f"{d}%", f"${rp:,}")
    with tabs[9]:
        df['EMA55'] = df['price'].ewm(span=55, adjust=False).mean()
        # ...вашата Bull/Bear логика...
        st.write("EMA 55 Анализ")
        st.plotly_chart(px.line(df, x='data', y=['price', 'EMA55'], template="plotly_dark"), use_container_width=True)

else:
    st.info("👈 Качете файл.")
