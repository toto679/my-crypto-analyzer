import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="DCA Исторически Анализ", layout="wide")

st.title("💰 Исторически DCA Калкулатор с Избор на Период")

if 'shared_df' in st.session_state:
    # 1. Подготовка на данните
    df_raw = st.session_state['shared_df'].copy()
    df_raw['data'] = pd.to_datetime(df_raw['data'])
    df_raw = df_raw.sort_values('data')

    # --- СТРАНИЧНА ЛЕНТА: НАСТРОЙКИ ---
    st.sidebar.header("⚙️ Настройки на Анализа")
    inv_amount = st.sidebar.number_input("Сума на всяка покупка ($)", min_value=1, value=100)

    # Добавяне на избор на период
    max_date = df_raw['data'].max()
    min_date = df_raw['data'].min()
    
    st.sidebar.subheader("📅 Период на натрупване")
    date_range = st.sidebar.date_input(
        "Избери дати",
        value=(max_date - timedelta(days=365), max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Проверка дали са избрани две дати
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        # Филтриране на данните според избрания период
        mask = (df_raw['data'] >= pd.Timestamp(start_date)) & (df_raw['data'] <= pd.Timestamp(end_date))
        df = df_raw.loc[mask].copy()
    else:
        st.info("Изберете начална и крайна дата от календара вляво.")
        st.stop()

    if df.empty:
        st.error("Няма данни за избрания период!")
        st.stop()

    last_price = df['price'].iloc[-1]

    # 2. Функция за изчисляване на DCA
    def calculate_dca(dataframe, days_step):
        dca_df = dataframe.iloc[::days_step, :].copy()
        total_spent = len(dca_df) * inv_amount
        total_units = (inv_amount / dca_df['price']).sum()
        real_avg = total_spent / total_units if total_units > 0 else 0
        return real_avg, total_spent, total_units

    # Изчисления
    avg_3d, spent_3d, units_3d = calculate_dca(df, 3)
    avg_7d, spent_7d, units_7d = calculate_dca(df, 7)
    avg_30d, spent_30d, units_30d = calculate_dca(df, 30)

    # 3. ПОКАЗВАНЕ НА РЕЗУЛТАТИ
    st.write(f"Анализ за периода: **{start_date}** до **{end_date}**")
    
    col1, col2, col3 = st.columns(3)
    
    # Сравнение със сегашната цена
    def get_delta(avg):
        return f"{((last_price/avg)-1)*100:.1f}%" if avg > 0 else "0%"

    col1.metric("Средна (3 дни)", f"${avg_3d:,.2f}", delta=get_delta(avg_3d))
    col2.metric("Средна (Седмица)", f"${avg_7d:,.2f}", delta=get_delta(avg_7d))
    col3.metric("Средна (Месец)", f"${avg_30d:,.2f}", delta=get_delta(avg_30d))

    # 4. ГРАФИКА
    st.subheader("📈 Графика на периода със средните нива")
    
    fig = go.Figure()
    # Линия на цената
    fig.add_trace(go.Scatter(x=df['data'], y=df['price'], name="Цена", line=dict(color='gray', width=2), opacity=0.6))

    # Хоризонтални линии за DCA нивата
    fig.add_hline(y=avg_3d, line_dash="dot", line_color="#00CC96", annotation_text="DCA 3д")
    fig.add_hline(y=avg_7d, line_dash="dash", line_color="#FFA15A", annotation_text="DCA 7д")
    fig.add_hline(y=avg_30d, line_dash="dashdot", line_color="#AB63FA", annotation_text="DCA 30д")

    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # 5. ИНФОРМАЦИЯ ЗА ПЕЧАЛБАТА
    with st.expander("💰 Колко би спечелил/загубил?"):
        st.write(f"Инвестирана сума за периода: **${spent_7d:,.2f}**")
        current_value = units_7d * last_price
        profit = current_value - spent_7d
        st.write(f"Текуща стойност на активите: **${current_value:,.2f}**")
        st.write(f"Чиста печалба/загуба: **${profit:,.2f}** ({get_delta(avg_7d)})")

else:
    st.warning("⚠️ Първо качи файла в основната страница 'Анализатор'!")
