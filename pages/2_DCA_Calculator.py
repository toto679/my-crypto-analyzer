import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="DCA Анализ", layout="wide")

st.title("💰 Исторически DCA Калкулатор")

# Проверка дали имаме данни от основната страница
if 'df' in st.session_state and st.session_state['df'] is not None:
    df_raw = st.session_state['df'].copy()
    df_raw['data'] = pd.to_datetime(df_raw['data'])
    df_raw = df_raw.sort_values('data')

    st.sidebar.header("⚙️ Настройки")
    inv_amount = st.sidebar.number_input("Сума на покупка ($)", min_value=1, value=100)

    # ОПРАВЯНЕ НА КАЛЕНДАРА: Задаваме начална и крайна дата ръчно
    max_d = df_raw['data'].max().date()
    min_d = df_raw['data'].min().date()
    
    st.sidebar.subheader("📅 Избор на период")
    start_date = st.sidebar.date_input("Начална дата", value=max_d - timedelta(days=365), min_value=min_d, max_value=max_d)
    end_date = st.sidebar.date_input("Крайна дата", value=max_d, min_value=min_d, max_value=max_d)

    if start_date < end_date:
        mask = (df_raw['data'].dt.date >= start_date) & (df_raw['data'].dt.date <= end_date)
        df = df_raw.loc[mask].copy()
    else:
        st.error("Грешка: Началната дата трябва да е преди крайната.")
        st.stop()

    # Изчисления за различните периоди
    def calculate_dca(dataframe, days_step):
        dca_df = dataframe.iloc[::days_step, :].copy()
        count = len(dca_df)
        total_spent = count * inv_amount
        total_units = (inv_amount / dca_df['price']).sum()
        avg_price = total_spent / total_units if total_units > 0 else 0
        return avg_price, total_spent, count

    res_3d = calculate_dca(df, 3)
    res_7d = calculate_dca(df, 7)
    res_30d = calculate_dca(df, 30)

    # Резултати
    st.info(f"Анализ за периода: **{start_date}** до **{end_date}**")
    
    c1, c2, c3 = st.columns(3)
    periods = [("3 Дни", res_3d), ("Седмица", res_7d), ("Месец", res_30d)]
    cols = [c1, c2, c3]

    for i, (name, res) in enumerate(periods):
        with cols[i]:
            st.metric(f"Средна ({name})", f"${res[0]:,.2f}")
            st.write(f"💰 Инвестирани: **${res[1]:,.0f}**")
            st.write(f"🔄 Покупки: **{res[2]}**")

    # Графика
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color='gray', width=1.5), opacity=0.4))
    
    # Средни линии
    fig.add_hline(y=res_3d[0], line_dash="dot", line_color="#00CC96", annotation_text="DCA 3д")
    fig.add_hline(y=res_7d[0], line_dash="dash", line_color="#FFA15A", annotation_text="DCA 7д")
    fig.add_hline(y=res_30d[0], line_dash="dashdot", line_color="#AB63FA", annotation_text="DCA 30д")
    
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Първо качи файла в основната страница!")
