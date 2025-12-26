import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="DCA Калкулатор", layout="wide")

st.title("💰 DCA Калкулатор (Синхронизиран)")

# Проверка за данни от основната страница
if 'shared_df' in st.session_state:
    df = st.session_state['shared_df']
    last_price = df['price'].iloc[-1]
    
    st.success(f"✅ Използваме данни от заредения файл. Текуща цена: ${last_price:,.2f}")
    
    st.sidebar.header("Настройки")
    inv_amount = st.sidebar.number_input("Сума на покупка (USD)", 10, 1000, 100)
    freq = st.sidebar.selectbox("Честота", ["Седмично", "Месечно"])
    years = st.sidebar.slider("Период (години)", 1, 5, 2)
    
    # Логика за DCA
    num_buys = years * (52 if freq == "Седмично" else 12)
    total_invested = num_buys * inv_amount
    
    # Симулация базирана на средната цена от последните 2 години
    avg_price = df['price'].tail(730).mean() 
    total_units = total_invested / avg_price
    
    st.subheader("📊 Резултати от симулацията")
    c1, c2, c3 = st.columns(3)
    c1.metric("Общо инвестирани", f"${total_invested:,.0f}")
    c2.metric("Средна цена на покупка (прогнозна)", f"${avg_price:,.2f}")
    c3.metric("Общо натрупани единици", f"{total_units:.4f}")

    # Графика на растежа
    dca_data = pd.DataFrame({
        'Покупка': range(1, num_buys + 1),
        'Инвестиран Капитал': [i * inv_amount for i in range(1, num_buys + 1)]
    })
    fig = px.area(dca_data, x='Покупка', y='Инвестиран Капитал', template="plotly_dark", color_discrete_sequence=['#FFA15A'])
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Първо качи .ods файла в основната страница (Анализатор), за да заредиш данните тук!")
