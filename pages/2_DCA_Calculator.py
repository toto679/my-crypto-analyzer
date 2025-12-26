import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="DCA Исторически Анализ", layout="wide")

st.title("💰 Исторически DCA Калкулатор")

if 'shared_df' in st.session_state:
    df_raw = st.session_state['shared_df'].copy()
    df_raw['data'] = pd.to_datetime(df_raw['data'])
    df_raw = df_raw.sort_values('data')

    st.sidebar.header("⚙️ Настройки")
    inv_amount = st.sidebar.number_input("Сума на всяка покупка ($)", min_value=1, value=100)

    # Избор на период
    max_date = df_raw['data'].max()
    min_date = df_raw['data'].min()
    date_range = st.sidebar.date_input(
        "Избери период на натрупване",
        value=(max_date - timedelta(days=365), max_date),
        min_value=min_date, max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df_raw['data'] >= pd.Timestamp(start_date)) & (df_raw['data'] <= pd.Timestamp(end_date))
        df = df_raw.loc[mask].copy()
    else:
        st.stop()

    # Функция за изчисление с броене на покупките
    def calculate_dca_details(dataframe, days_step):
        dca_df = dataframe.iloc[::days_step, :].copy()
        count = len(dca_df)
        total_spent = count * inv_amount
        total_units = (inv_amount / dca_df['price']).sum()
        avg_price = total_spent / total_units if total_units > 0 else 0
        return avg_price, total_spent, count

    # Изчисления
    res_3d = calculate_dca_details(df, 3)
    res_7d = calculate_dca_details(df, 7)
    res_30d = calculate_dca_details(df, 30)

    last_price = df['price'].iloc[-1]
    st.write(f"Анализ за: **{start_date}** до **{end_date}** | Текуща цена: **${last_price:,.2f}**")

    # ПОКАЗВАНЕ НА РЕЗУЛТАТИТЕ
    c1, c2, c3 = st.columns(3)
    
    # Колона 1: 3 Дни
    with c1:
        st.metric("Средна (3 дни)", f"${res_3d[0]:,.2f}")
        st.caption(f"💰 Инвестирани: **${res_3d[1]:,.0f}**")
        st.caption(f"🔄 Брой покупки: **{res_3d[2]}**")

    # Колона 2: Седмица
    with c2:
        st.metric("Средна (Седмица)", f"${res_7d[0]:,.2f}")
        st.caption(f"💰 Инвестирани: **${res_7d[1]:,.0f}**")
        st.caption(f"🔄 Брой покупки: **{res_7d[2]}**")

    # Колона 3: Месец
    with c3:
        st.metric("Средна (Месец)", f"${res_30d[0]:,.2f}")
        st.caption(f"💰 Инвестирани: **${res_30d[1]:,.0f}**")
        st.caption(f"🔄 Брой покупки: **{res_30d[2]}**")

    # Графика
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color='gray', width=2), opacity=0.5))
    fig.add_hline(y=res_3d[0], line_dash="dot", line_color="#00CC96", annotation_text="DCA 3д")
    fig.add_hline(y=res_7d[0], line_dash="dash", line_color="#FFA15A", annotation_text="DCA 7д")
    fig.add_hline(y=res_30d[0], line_dash="dashdot", line_color="#AB63FA", annotation_text="DCA 30д")
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Първо качи файла в основната страница!")
