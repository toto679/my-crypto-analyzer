import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math
import io

st.set_page_config(page_title="Анализатор", layout="wide")
st.title("📊 Пълен Анализ: Всички Инструменти & Графики")

uploaded_file = st.sidebar.file_uploader("Добави .ods файл", type=["ods"])

if uploaded_file:
    # Зареждане на данни
    df = pd.read_excel(uploaded_file, engine='odf')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data']).sort_values('data')
    
    # Филтър за последните 4 години
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df = df[df['data'] > four_years_ago]

    # Търсене на колони за MCap и Supply
    mcap_col = [c for c in df.columns if 'market_cap' in c.lower()]
    sup_col = [c for c in df.columns if 'supply' in c.lower() or 'circulating' in c.lower()]

    # ТАБОВЕ
    tabs = st.tabs(["📈 Основни Графики", "📅 Сравнение & Таблица", "🎯 Target & Risk", "⚡ Технически"])

    # ТАБ 1: ВСИЧКИ ГРАФИКИ (Връщаме ги тук!)
    with tabs[0]:
        st.subheader("Цена и Пълна История")
        fig_p = px.line(df, x='data', y='price', template="plotly_dark", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig_p, use_container_width=True)
        
        if sup_col:
            st.subheader("Supply спрямо Цената")
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
            fig_s.add_trace(go.Scatter(x=df['data'], y=df[sup_col[0]], name="Supply", yaxis="y2"))
            fig_s.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"))
            st.plotly_chart(fig_s, use_container_width=True)

    # ТАБ 2: СРАВНЕНИЕ И УМНА ТАБЛИЦА
    with tabs[1]:
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("### 🔍 Сравнение на дати")
            d1 = st.date_input("Начало", df['data'].min())
            d2 = st.date_input("Край", df['data'].max())
            p1 = df.iloc[(df['data'] - pd.Timestamp(d1)).abs().argsort()[:1]]['price'].values[0]
            p2 = df.iloc[(df['data'] - pd.Timestamp(d2)).abs().argsort()[:1]]['price'].values[0]
            st.metric("Промяна", f"{((p2-p1)/p1)*100:,.2f}%", f"{p2/p1:,.2f}x")
            
        with col_b:
            st.write("### 📅 Годишни Екстремуми")
            df['year'] = df['data'].dt.year
            yearly = df.groupby('year')['price'].agg(['min', 'max']).reset_index()
            yearly['x (ръст)'] = yearly['max'] / yearly['min']
            
            def style_growth(s):
                return ['background-color: #004d00' if v == s.max() else 'background-color: #4d0000' if v == s.min() else '' for v in s]
            
            st.dataframe(yearly.style.format({"min":"{:.2f}","max":"{:.2f}","x (ръст)":"{:.2x}"}).apply(style_growth, subset=['x (ръст)']))
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                yearly.to_excel(writer, index=False)
            st.download_button("📥 Свали в Excel", buffer, "analysis.xlsx")

    # ТАБ 3: TARGET & RISK
    with tabs[2]:
        if mcap_col and sup_col:
            st.subheader("🎯 Целеви цени (Target)")
            min_mcap = df[mcap_col[0]].min()
            last_sup = df[sup_col[0]].iloc[-1]
            m_list = [5, 10, 20, 50]
            cols = st.columns(len(m_list))
            for i, m in enumerate(m_list):
                t_price = (min_mcap * m) / last_sup
                cols[i].metric(f"При x{m} Cap", f"${t_price:,.2f}")

    # ТАБ 4: ТЕХНИЧЕСКИ (MA & Volatility)
    with tabs[3]:
        df['MA50'] = df['price'].rolling(50).mean()
        df['MA200'] = df['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.3))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA200'], name="MA 200", line=dict(color="red")))
        fig_ma.update_layout(template="plotly_dark", title="Moving Averages (50/200)")
        st.plotly_chart(fig_ma, use_container_width=True)

else:
    st.info("👈 Качете файл, за да видите анализите.")
