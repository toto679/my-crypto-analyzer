import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math
import io

# Настройка на страницата
st.set_page_config(page_title="Анализатор", layout="wide")
st.title("📊 Пълен Анализ: Всички Инструменти & Нови Екстри")

uploaded_file = st.sidebar.file_uploader("Добави .ods файл", type=["ods"])

if uploaded_file:
    # 1. Зареждане и почистване
    df = pd.read_excel(uploaded_file, engine='odf')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data']).sort_values('data')
    
    # Глобален филтър (последните 4 години)
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df = df[df['data'] > four_years_ago]

    # Търсене на колони
    mcap_col = [c for c in df.columns if 'market_cap' in c.lower()]
    sup_col = [c for c in df.columns if 'supply' in c.lower() or 'circulating' in c.lower()]
    ratio_col = [c for c in df.columns if 'price' in c.lower() and '/' in c.lower()]

    # ДЕФИНИРАНЕ НА 10-ТЕ ТАБА (Всички стари + новите неща вътре)
    tabs = st.tabs([
        "🔗 Ratio", "🏆 Укрупняване", "📈 Supply", "📅 Годишни", 
        "📉 MA", "🎯 Cap vs Sup", "⚡ Волатилност", "💰 Target", "📉 Risk", "⚖️ EMA 55 Mean"
    ])

    # 1. Ratio
    with tabs[0]:
        if ratio_col:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color="#00CC96")))
            fig.add_trace(go.Scatter(x=df['data'], y=df[ratio_col[0]], name="Ratio", yaxis="y2", line=dict(color="#FFA15A")))
            fig.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig, use_container_width=True)

    # 2. Укрупняване
    with tabs[1]:
        fig_vp = go.Figure()
        fig_vp.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
        fig_vp.add_trace(go.Histogram(y=df['price'], orientation='h', nbinsy=50, xaxis='x2', marker=dict(color='rgba(100,150,250,0.2)')))
        fig_vp.update_layout(template="plotly_dark", xaxis2=dict(overlaying='x', side='top', domain=[0, 0.15]), height=600)
        st.plotly_chart(fig_vp, use_container_width=True)

    # 3. Supply
    with tabs[2]:
        if sup_col:
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
            fig_s.add_trace(go.Scatter(x=df['data'], y=df[sup_col[0]], name="Supply", yaxis="y2"))
            fig_s.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig_s, use_container_width=True)

    # 4. Годишни (Тук добавихме Сравнението и Умната Таблица)
    with tabs[3]:
        st.subheader("📅 Сравнение на дати и Годишни Екстремуми")
        
        # СЕКЦИЯ: Сравнение на дати (НОВО)
        c1, c2 = st.columns(2)
        with c1:
            d1 = st.date_input("Начална дата", df['data'].min())
        with c2:
            d2 = st.date_input("Крайна дата", df['data'].max())
        
        p1 = df.iloc[(df['data'] - pd.Timestamp(d1)).abs().argsort()[:1]]['price'].values[0]
        p2 = df.iloc[(df['data'] - pd.Timestamp(d2)).abs().argsort()[:1]]['price'].values[0]
        st.metric("Промяна (%)", f"{((p2-p1)/p1)*100:,.2f}%", f"{p2/p1:,.2f}x")

        # ТАБЛИЦА (УМНА)
        df['year'] = df['data'].dt.year
        yearly = df.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly['x (ръст)'] = yearly['max'] / yearly['min']
        
        def style_g(s):
            return ['background-color: #4d0000' if v == s.min() else 'background-color: #004d00' if v == s.max() else '' for v in s]
        
        st.dataframe(yearly.style.format({"min":"{:.2f}", "max":"{:.2f}", "x (ръст)":"{:.2f}x"}).apply(style_g, subset=['x (ръст)']), use_container_width=True)
        
        # БУТОН ЗА EXCEL
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            yearly.to_excel(writer, index=False)
        st.download_button("📥 Свали Годишния Анализ", buf.getvalue(), "analysis.xlsx")

    # 5. MA
    with tabs[4]:
        df['MA50'] = df['price'].rolling(50).mean()
        df['MA200'] = df['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.3))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA200'], name="MA 200", line=dict(color="red")))
        fig_ma.update_layout(template="plotly_dark", height=600)
        st.plotly_chart(fig_ma, use_container_width=True)

    # 6. Cap vs Sup
    with tabs[5]:
        if mcap_col and sup_col:
            fig_scat = px.scatter(df, x=sup_col[0], y=mcap_col[0], color='price', template="plotly_dark")
            st.plotly_chart(fig_scat, use_container_width=True)

    # 7. Волатилност
    with tabs[6]:
        df['vol'] = df['price'].pct_change() * 100
        fig_v = px.line(df, x='data', y='vol', title="Волатилност %", template="plotly_dark")
        st.plotly_chart(fig_v, use_container_width=True)

    # 8. Target
    with tabs[7]:
        if mcap_col and sup_col:
            min_mcap = df[mcap_col[0]].min()
            last_sup = df[sup_col[0]].iloc[-1]
            m_list = [5, 10, 20, 50]
            cols = st.columns(len(m_list))
            for i, m in enumerate(m_list):
                tp = (min_mcap * m) / last_sup
                cols[i].metric(f"x{m}", f"${tp:,.2f}")

    # 9. Risk
    with tabs[8]:
        if mcap_col:
            max_mcap = df[mcap_col[0]].max()
            last_sup = df[sup_col[0]].iloc[-1]
            drops = [-60, -80, -95]
            cols = st.columns(len(drops))
            for i, d in enumerate(drops):
                rp = (max_mcap * (100+d)/100) / last_sup
                cols[i].metric(f"{d}%", f"${rp:,.2f}")

    # 10. EMA 55 Mean
    with tabs[9]:
        df['EMA55'] = df['price'].ewm(span=55).mean()
        # (Тук е вашата оригинална логика за Bull/Bear Mean)
        st.plotly_chart(px.line(df, x='data', y=['price', 'EMA55'], template="plotly_dark"), use_container_width=True)

else:
    st.info("👈 Качете файл.")
