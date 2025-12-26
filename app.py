# ДЕФИНИРАНЕ НА ВСИЧКИ 10 ТАБА
    tabs = st.tabs([
        "🔗 Ratio", "🏆 Укрупняване", "📈 Supply", "📅 Годишни", 
        "📉 MA", "🎯 Cap vs Sup", "⚡ Волатилност", "💰 Target", "📉 Risk", "⚖️ EMA 55 Mean"
    ])

    # 1. Ratio
    with tabs[0]:
        if ratio_col:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена", line=dict(color="#00CC96")))
            fig.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered[ratio_col[0]], name="Ratio", yaxis="y2", line=dict(color="#FFA15A")))
            fig.update_layout(template="plotly_dark", yaxis=dict(title="Цена"), yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig, use_container_width=True)

    # 2. Укрупняване
    with tabs[1]:
        fig_vp = go.Figure()
        fig_vp.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена"))
        fig_vp.add_trace(go.Histogram(y=df_filtered['price'], orientation='h', nbinsy=50, xaxis='x2', marker=dict(color='rgba(100,150,250,0.2)')))
        fig_vp.update_layout(template="plotly_dark", xaxis=dict(domain=[0.1, 1]), xaxis2=dict(overlaying='x', side='top', domain=[0, 0.15]), height=600)
        st.plotly_chart(fig_vp, use_container_width=True)

    # 3. Supply
    with tabs[2]:
        if sup_col:
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена"))
            fig_s.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered[sup_col[0]], name="Supply", yaxis="y2"))
            fig_s.update_layout(template="plotly_dark", yaxis2=dict(overlaying="y", side="right"), height=600)
            st.plotly_chart(fig_s, use_container_width=True)

    # 4. Годишни
    with tabs[3]:
        st.subheader("📅 Минимална и Максимална Цена по Години")
        df_filtered['year'] = df_filtered['data'].dt.year
        yearly_price = df_filtered.groupby('year')['price'].agg(['min', 'max']).reset_index()
        yearly_price['разлика'] = yearly_price['max'] - yearly_price['min']
        yearly_price['x (ръст)'] = yearly_price['max'] / yearly_price['min']
        
        fig_y = px.bar(yearly_price, x='year', y=['min', 'max'], barmode='group', template="plotly_dark", color_discrete_map={'min': '#EF553B', 'max': '#00CC96'}, text_auto='.2f')
        st.plotly_chart(fig_y, use_container_width=True)
        
        st.write("### Таблица на екстремумите")
        st.dataframe(yearly_price.style.format({"min": "{:,.2f}", "max": "{:,.2f}", "разлика": "{:,.2f}", "x (ръст)": "{:,.2f}x"}), use_container_width=True)

        avg_diff = yearly_price['разлика'].mean()
        avg_x = yearly_price['x (ръст)'].mean()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Средна разлика", f"${avg_diff:,.2f}")
        c2.metric("Среден ръст (%)", f"{(avg_x-1)*100:,.2f}%")
        c3.metric("Среден ръст (x)", f"{avg_x:,.2f}x")

    # 5. MA
    with tabs[4]:
        df_filtered['MA50'] = df_filtered['price'].rolling(50).mean()
        df_filtered['MA200'] = df_filtered['price'].rolling(200).mean()
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена", opacity=0.4))
        fig_ma.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['MA50'], name="MA 50", line=dict(color="yellow")))
        fig_ma.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['MA200'], name="MA 200", line=dict(color="red")))
        fig_ma.update_layout(template="plotly_dark", height=600)
        st.plotly_chart(fig_ma, use_container_width=True)

    # 6. Cap vs Sup
    with tabs[5]:
        if mcap_col and sup_col:
            st.plotly_chart(px.scatter(df_filtered, x=sup_col[0], y=mcap_col[0], color='price', template="plotly_dark"), use_container_width=True)

    # 7. Волатилност
    with tabs[6]:
        st.subheader("⚡ Анализ на Волатилността и Цената")
        df_filtered['vol'] = df_filtered['price'].pct_change() * 100
        fig_sync = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig_sync.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена", line=dict(color="#00CC96")), row=1, col=1)
        fig_sync.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['vol'], name="Волатилност %", line=dict(color="#FFA15A")), row=2, col=1)
        for h in [0, 5, 10, -5, -10]:
            fig_sync.add_hline(y=h, line_dash="dash", line_color="rgba(255,255,255,0.2)", row=2, col=1)
        fig_sync.update_layout(template="plotly_dark", height=700)
        st.plotly_chart(fig_sync, use_container_width=True)

    # 8. Target
    with tabs[7]:
        if mcap_col and sup_col:
            min_mcap = df_filtered[mcap_col[0]].min()
            last_supply = df_filtered[sup_col[0]].iloc[-1]
            m_list = [5, 10, 15, 20, 30, 40, 50]
            cols = st.columns(len(m_list))
            for i, m in enumerate(m_list):
                tp = math.floor((min_mcap * m) / last_supply)
                cols[i].metric(f"x{m}", f"${tp:,}")

    # 9. Risk
    with tabs[8]:
        if mcap_col and sup_col:
            max_mcap = df_filtered[mcap_col[0]].max()
            last_supply = df_filtered[sup_col[0]].iloc[-1]
            drops = [-60, -70, -80, -90, -95]
            st.write(f"Базов макс. MCap (4г): **${max_mcap:,.0f}**")
            cols = st.columns(len(drops))
            for i, d in enumerate(drops):
                t_price = math.floor((max_mcap * (100 + d) / 100) / last_supply)
                cols[i].metric(f"{d}%", f"${t_price:,}")

    # 10. EMA 55 Mean
    with tabs[9]:
        df_filtered['EMA55'] = df_filtered['price'].ewm(span=55, adjust=False).mean()
        highs, lows = [], []
        curr, t_h, t_l = None, 0, float('inf')
        for i in range(len(df_filtered)):
            p, e = df_filtered['price'].iloc[i], df_filtered['EMA55'].iloc[i]
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
        fig_e.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['price'], name="Цена", opacity=0.3))
        fig_e.add_trace(go.Scatter(x=df_filtered['data'], y=df_filtered['EMA55'], name="EMA 55"))
        fig_e.add_hline(y=b_m, line_dash="dash", line_color="green")
        fig_e.add_hline(y=s_m, line_dash="dash", line_color="red")
        fig_e.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_e, use_container_width=True)

    # ОБЩИ МЕТРИКИ
    st.write("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Макс Цена (4г)", f"${df_filtered['price'].max():,.2f}")
    m2.metric("Мин Цена (4г)", f"${df_filtered['price'].min():,.2f}")
    m3.metric("Записи", len(df_filtered))

else:
    st.info("👈 Моля, качи .ods файл от менюто вляво.")
