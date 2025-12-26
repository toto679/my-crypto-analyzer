import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

# Настройка на страницата
st.set_page_config(page_title="Анализатор", layout="wide")
st.title("📊 Пълен Анализ: Графики и Резултати")

uploaded_file = st.sidebar.file_uploader("Добави .ods файл", type=["ods"])

if uploaded_file:
    # 1. Зареждане и почистване
    df = pd.read_excel(uploaded_file, engine='odf')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data']).sort_values('data')
    
    # Филтър за последните 4 години
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df = df[df['data'] > four_years_ago]

    # Търсене на колони
    mcap_col = [c for c in df.columns if 'market_cap' in c.lower()]
    sup_col = [c for c in df.columns if 'supply' in c.lower() or 'circulating' in c.lower()]

    # СЪЗДАВАНЕ НА ТАБОВЕ - Графиките са първи!
    tabs = st.tabs(["📈 Главни Графики", "🔍 Сравнение & Таблица", "🎯 Target & Risk", "⚡ MA & Volatility"])

    # ТАБ 1: ГРАФИКИ
    with tabs[0]:
        st.subheader("Движение на цената")
        fig_p = px.line(df, x='data', y='price', template="plotly_dark", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig_p, use_container_width=True)
        
        if sup_col:
            st.subheader("Supply спрямо Цена")
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
            fig_s.add_trace(go.Scatter(x=df['data'], y=df[sup_col[0]], name="Supply", yaxis="y2"))
            fig_s.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"))
            st.plotly_chart(fig_s, use_container_width=True)

    # ТАБ 2: СРАВНЕНИЕ И ТАБЛИЦА (Поправена!)
    with tabs[1]:
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.write("### 🔍 Изчисли доходност")
            d1 = st.date_input("От дата", df['data'].min())
            d2 = st.date_input("До дата", df['data'].max())
            p1 = df.iloc[(df['data'] - pd.Timestamp(d1)).abs().argsort()[:1]]['price'].values[0]
            p2 = df.iloc[(df['data'] - pd.Timestamp(d2)).abs().argsort()[:1]]['price'].values[0]
            diff = ((p2-p1)/p1)*100
            st.metric("Резултат %", f"{diff:,.2f}%", f"{p2/p1:,.2f}x")
            
        with col_right:
            st.write("### 📅 Годишни данни")
            df['year'] = df['data'].dt.year
            yearly = df.groupby('year')['price'].agg(['min', 'max']).reset_index()
            yearly['x (ръст)'] = yearly['max'] / yearly['min']
            
            # Поправено оцветяване и форматиране
            def style_growth(s):
                return ['background-color: #4d0000' if v == s.min() else 'background-color: #004d00' if v == s.max() else '' for v in s]
            
            # ВАЖНО: Тук променихме на .2f, за да не дава грешка
            st.dataframe(yearly.style.format({"min":"{:.2f}", "max":"{:.2f}", "x (ръст)":"{:.2f}x"}).apply(style_growth, subset=['x (ръст)']), use_container_width=True)
            
            # Бутон за Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                yearly.to_excel(writer, index=False)
            st.download_button("📥 Свали Годишния Анализ", buffer.getvalue(), "crypto_analysis.xlsx")

    # ТАБ 3: TARGETS
    with tabs[2]:
        if mcap_col and sup_col:
            st.subheader("🎯 Прогнози според Market Cap")
            min_cap = df[mcap_col[0]].min()
            last_s = df[sup_col[0]].iloc[-1]
            multipliers = [5, 10, 20, 50, 100]
            c_cols = st.columns(len(multipliers))
            for i, m in enumerate(multipliers):
                target_p = (min_cap * m) / last_s
                c_cols[i].metric(f"При x{m}", f"${target_p:,.2f}")

    # ТАБ 4: ТЕХНИЧЕСКИ
    with tabs[3]:
        df['MA50'] = df['price'].rolling(50).mean()
        df['MA200'] = df['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.3))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['MA200'], name="MA 200", line=dict(color="red")))
        fig_ma.update_layout(template="plotly_dark", title="Пълзящи средни")
        st.plotly_chart(fig_ma, use_container_width=True)

else:
    st.info("👈 Качете вашия .ods файл от менюто вляво.")
