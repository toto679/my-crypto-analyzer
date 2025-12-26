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

# --- СТРАНИЧНА ЛЕНТА ---
uploaded_file = st.sidebar.file_uploader("Добави .ods файл", type=["ods"])

if uploaded_file:
    # Зареждане и основно почистване
    df = pd.read_excel(uploaded_file, engine='odf')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    
    # Глобален филтър за последните 4 години
    four_years_ago = datetime.now() - timedelta(days=4*365)
    df = df[df['data'] > four_years_ago].sort_values('data')

    # Търсене на колони
    mcap_col = [c for c in df.columns if 'market_cap' in c.lower()]
    sup_col = [c for c in df.columns if 'supply' in c.lower() or 'circulating' in c.lower()]
    ratio_col = [c for c in df.columns if 'price' in c.lower() and '/' in c.lower()]

    # ДЕФИНИРАНЕ НА ВСИЧКИ 10 ТАБА
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
            fig.update_layout(template="plotly_dark", yaxis=dict(title="Цена"), yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig, use_container_width=True)

    # 2. Укрупняване
    with tabs[1]:
        fig_vp = go.Figure()
        fig_vp.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
        fig_vp.add_trace(go.Histogram(y=df['price'], orientation='h', nbinsy=50, xaxis='x2', marker=dict(color='rgba(100,150,250,0.2)')))
        fig_vp.update_layout(template="plotly_dark", xaxis=dict(domain=[0.1, 1]), xaxis2=dict(overlaying='x', side='top', domain=[0, 0.15]), height=600)
        st.plotly_chart(fig_vp, use_container_width=True)

    # 3. Supply
    with tabs[2]:
        if sup_col:
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена"))
            fig_s.add_trace(go.Scatter(x=df['data'], y=df[sup_col[0]], name="Supply", yaxis="y2"))
            fig_s.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig_s, use_container_width=True)

    # 4. Годишни (С добавено Сравнение и Excel бутон)
    with tabs[3]:
        st.subheader("📅 Анализ на Периоди и Екстремуми")
        
        # НОВО: Сравнение между две дати
        st.write("### 🔍 Сравнение на доходност")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_start = st.date_input("Начална дата", df['data'].min())
        with col_d2:
            d_end = st.date_input("Крайна дата", df['data'].max())
        
        p_start = df.iloc[(df['data'] - pd.Timestamp(d_start)).abs().argsort()[:1]]['price'].values[0]
        p_end = df.iloc[(df['data'] - pd.Timestamp(d_end)).abs().argsort()[:1]]['price'].values[0]
        
        c_p1, c_p2, c_p3 = st.columns(3)
        c_p1.metric("Цена в начало", f"${p_start:,.2f}")
        c_p2.metric("Цена в край", f"${p_end:,.2f}")
        c_p3.metric("Ръст/Спад %", f"{((p_end-p_start)/p_start)*100:,.2f}%", f"{p_end/p_start:,.2f}x")

        # Оригиналната ти таблица и графика
        df['year'] = df['data'].dt.year
        yearly_price = df.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly_price['разлика'] = yearly_price['max'] - yearly_price['min']
        yearly_price['x (ръст)'] = yearly_price['max'] / yearly_price['min']
        
        fig_y = px.bar(yearly_price, x='year', y=['min', 'max'], barmode='group', template="plotly_dark", color_discrete_map={'min': '#EF553B', 'max': '#00CC96'}, text_auto='.2f')
        st.plotly_chart(fig_y, use_container_width=True)
        
        # УМНО ОЦВЕТЯВАНЕ (Зелено за най-доброто, Червено за най-слабото)
        def highlight_extreme(s):
            return ['background-color: #004d00' if v == s.max() else 'background-color: #4d0000' if v == s.min() else '' for v in s]
        
        st.write("### Таблица на екстремумите (с автоматично оцветяване)")
        st.dataframe(yearly_price.style.format({"min":"{:.2f}","max":"{:.2f}","разлика":"{:.2f}","x (ръст)":"{:.2f}x"}).apply(highlight_extreme, subset=['x (ръст)']), use_container_width=True)
        
        # БУТОН ЗА EXCEL
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            yearly_price.to_excel(writer, index=False)
        st.download_button("📥 Изтегли таблицата в Excel", buffer.getvalue(), "yearly_analysis.xlsx")

    # 5. MA
    with tabs[4]:
        df['MA50'] = df['price'].rolling(50).mean()
        df['MA200'] = df['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color="gray", width=1), opacity=0.4))
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
        st.subheader("⚡ Анализ на Волатилността")
        df['vol'] = df['price'].pct_change() * 100
        fig_v = px.line(df, x='data', y='vol', template="plotly_dark", title="Дневно изменение %")
        fig_v.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_v, use_container_width=True)

    # 8. Target
    with tabs[7]:
        if mcap_col and sup_col:
            min_mcap = df[mcap_col[0]].min()
            last_supply = df[sup_col[0]].iloc[-1]
            m_list = [5, 10, 15, 20, 30, 40, 50]
            cols = st.columns(len(m_list))
            for i, m in enumerate(m_list):
                t_price = math.floor((min_mcap * m) / last_supply)
                cols[i].metric(f"x{m}", f"${t_price:,}")

    # 9. Risk
    with tabs[8]:
        if mcap_col and sup_col:
            max_mcap = df[mcap_col[0]].max()
            last_supply = df[sup_col[0]].iloc[-1]
            drops = [-60, -70, -80, -90, -95]
            cols = st.columns(len(drops))
            for i, d in enumerate(drops):
                t_price = math.floor((max_mcap * (100 + d) / 100) / last_supply)
                cols[i].metric(f"{d}%", f"${t_price:,}")

    # 10. EMA 55 Mean (Твоята оригинална формула)
    with tabs[9]:
        df['EMA55'] = df['price'].ewm(span=55, adjust=False).mean()
        highs, lows = [], []
        curr = None
        t_h, t_l = 0, float('inf')

        for i in range(len(df)):
            p, e = df['price'].iloc[i], df['EMA55'].iloc[i]
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
        c1.metric("Bull Mean Target", f"${math.floor(b_m):,}")
        c2.metric("Bear Mean Target", f"${math.floor(s_m):,}")
        
        fig_e = go.Figure()
        fig_e.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", opacity=0.3))
        fig_e.add_trace(go.Scatter(x=df['data'], y=df['EMA55'], name="EMA 55"))
        fig_e.add_hline(y=b_m, line_dash="dash", line_color="green")
        fig_e.add_hline(y=s_m, line_dash="dash", line_color="red")
        fig_e.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_e, use_container_width=True)

    # Общи метрики най-отдолу
    st.write("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Макс Цена (4г)", f"{df['price'].max():.2f}")
    m2.metric("Мин Цена (4г)", f"{df['price'].min():.2f}")
    m3.metric("Записи", len(df))

else:
    st.info("👈 Качете файл, за да активирате всички 10 табла.")
