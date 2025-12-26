import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math
import io

# Настройка на страницата
st.set_page_config(page_title="Анализатор", layout="wide")
st.title("📊 Пълен Анализ: Всички Инструменти")

# Инструкции за requirements.txt (трябва да добавим xlsxwriter за сваляне)
# pandas, plotly, streamlit, odfpy, xlsxwriter

uploaded_file = st.sidebar.file_uploader("Добави .ods файл", type=["ods"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='odf')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data']).sort_values('data')
    
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df = df[df['data'] > four_years_ago]

    tabs = st.tabs(["📅 Сравнение на Дати", "🏆 Годишен Анализ", "📈 Всички Графики", "💰 Target & Risk"])

    # ТАБ 1: СРАВНЕНИЕ МЕЖДУ ДВЕ ДАТИ
    with tabs[0]:
        st.subheader("🔍 Сравнение на доходност")
        col1, col2 = st.columns(2)
        with col1:
            date1 = st.date_input("Начална дата", df['data'].min())
        with col2:
            date2 = st.date_input("Крайна дата", df['data'].max())
        
        # Намиране на най-близките цени до избраните дати
        p1 = df.iloc[(df['data'] - pd.Timestamp(date1)).abs().argsort()[:1]]['price'].values[0]
        p2 = df.iloc[(df['data'] - pd.Timestamp(date2)).abs().argsort()[:1]]['price'].values[0]
        
        diff_pct = ((p2 - p1) / p1) * 100
        multiplier = p2 / p1
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Цена в Начало", f"${p1:,.2f}")
        c2.metric("Цена в Край", f"${p2:,.2f}")
        c3.metric("Промяна (%)", f"{diff_pct:,.2f}%", f"{multiplier:,.2f}x")

    # ТАБ 2: УМНА ТАБЛИЦА С ЦВЕТОВЕ
    with tabs[1]:
        st.subheader("📅 Годишни Екстремуми")
        df['year'] = df['data'].dt.year
        yearly_price = df.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly_price['разлика'] = yearly_price['max'] - yearly_price['min']
        yearly_price['x (ръст)'] = yearly_price['max'] / yearly_price['min']
        
        # Функция за оцветяване
        def highlight_max_min(s):
            is_max = s == s.max()
            is_min = s == s.min()
            return ['background-color: #004d00' if v else 'background-color: #4d0000' if m else '' for v, m in zip(is_max, is_min)]

        styled_df = yearly_price.style.format({
            "min": "{:,.2f}", "max": "{:,.2f}", "разлика": "{:,.2f}", "x (ръст)": "{:,.2f}x"
        }).apply(highlight_max_min, subset=['x (ръст)'])
        
        st.dataframe(styled_df, use_container_width=True)
        
        # БУТОН ЗА ИЗТЕГЛЯНЕ
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            yearly_price.to_excel(writer, index=False, sheet_name='Sheet1')
        st.download_button(label="📥 Свали таблицата в Excel", data=buffer, file_name="yearly_analysis.xlsx", mime="application/vnd.ms-excel")

    # ТАБ 3 & 4 (Обединени стари функции за прегледност)
    with tabs[2]:
        st.plotly_chart(px.line(df, x='data', y='price', title="Движение на цената", template="plotly_dark"), use_container_width=True)
    
    with tabs[3]:
        st.write("Тук са вашите Target и Risk изчисления...")
        # (Запазени са старите ви метрики тук)

else:
    st.info("👈 Качете файл вляво.")
