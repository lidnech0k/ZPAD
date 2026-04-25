import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob

st.set_page_config(layout="wide")

@st.cache_data
def load_data(path):
    all_files = glob.glob(os.path.join(path, "*.csv"))
    if not all_files:
        return pd.DataFrame()

    regions_map = {
        1: "Вінницька", 2: "Волинська", 3: "Дніпропетровська", 4: "Донецька", 5: "Житомирська",
        6: "Закарпатська", 7: "Запорізька", 8: "Івано-Франківська", 9: "Київська", 10: "Кіровоградська",
        11: "Луганська", 12: "Львівська", 13: "Миколаївська", 14: "Одеська", 15: "Полтавська",
        16: "Рівненська", 17: "Сумська", 18: "Тернопільська", 19: "Харківська", 20: "Херсонська",
        21: "Хмельницька", 22: "Черкаська", 23: "Чернівецька", 24: "Чернігівська", 25: "Крим",
        26: "Київ", 27: "Севастополь"
    }

    all_data = []

    for filename in all_files:
        parts = os.path.basename(filename).split('_')
        file_id = None
        if len(parts) > 2 and parts[2].isdigit():
            file_id = int(parts[2])
        else:
            continue

        region_name = regions_map.get(file_id, f"Область {file_id}")

        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                clean_line = line.replace('<tt><pre>', '').replace('</pre></tt>', '').strip()
                if not clean_line:
                    continue
                
                parts_line = [p.strip() for p in clean_line.split(',')]
                
                if len(parts_line) >= 7 and parts_line[0].isdigit() and len(parts_line[0]) == 4:
                    try:
                        year = int(parts_line[0])
                        week = int(parts_line[1])
                        vci = float(parts_line[4])
                        tci = float(parts_line[5])
                        vhi = float(parts_line[6])
                        
                        all_data.append([year, week, vci, tci, vhi, file_id, region_name])
                    except ValueError:
                        pass

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data, columns=['Year', 'Week', 'VCI', 'TCI', 'VHI', 'ID', 'Region'])
    return df

df_raw = load_data("vhi_data")

if df_raw.empty:
    st.error("Помилка: Файли не містять коректних даних. Переконайтеся, що це дані NOAA.")
    st.stop()

def reset_filters():
    st.session_state['idx'] = 'VHI'
    st.session_state['reg'] = sorted(df_raw['Region'].unique())[0]
    st.session_state['w_rng'] = (int(df_raw['Week'].min()), int(df_raw['Week'].max()))
    st.session_state['y_rng'] = (int(df_raw['Year'].min()), int(df_raw['Year'].max()))
    st.session_state['asc'] = False
    st.session_state['dsc'] = False

if 'idx' not in st.session_state:
    reset_filters()

cp, cr = st.columns([1, 3])

with cp:
    idx = st.selectbox("Індекс:", ['VCI', 'TCI', 'VHI'], key='idx')
    reg = st.selectbox("Область:", sorted(df_raw['Region'].unique()), key='reg')
    w_rng = st.slider("Тижні:", int(df_raw['Week'].min()), int(df_raw['Week'].max()), key='w_rng')
    y_rng = st.slider("Роки:", int(df_raw['Year'].min()), int(df_raw['Year'].max()), key='y_rng')
    asc = st.checkbox("Зростання", key='asc')
    dsc = st.checkbox("Спадання", key='dsc')
    if st.button("Скинути"):
        reset_filters()
        st.rerun()

df_f = df_raw[
    (df_raw['Region'] == reg) &
    (df_raw['Week'] >= w_rng[0]) & (df_raw['Week'] <= w_rng[1]) &
    (df_raw['Year'] >= y_rng[0]) & (df_raw['Year'] <= y_rng[1])
]

if asc and dsc: 
    st.warning("Оберіть один тип сортування")
elif asc: 
    df_f = df_f.sort_values(idx, ascending=True)
elif dsc: 
    df_f = df_f.sort_values(idx, ascending=False)

with cr:
    t1, t2, t3 = st.tabs(["📊 Таблиця", "📈 Графік", "🌍 Порівняння"])
    
    with t1:
        st.dataframe(df_f, use_container_width=True)
        
    with t2:
        if not df_f.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            df_p = df_f.sort_values(['Year', 'Week'])
            x = [f"{y}-W{w}" for y, w in zip(df_p['Year'], df_p['Week'])]
            ax.plot(x, df_p[idx], color='teal')
            if len(x) > 20: 
                ax.set_xticks(ax.get_xticks()[::len(x)//10])
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("Немає даних для графіка")

    with t3:
        df_all = df_raw[
            (df_raw['Week'] >= w_rng[0]) & (df_raw['Week'] <= w_rng[1]) &
            (df_raw['Year'] >= y_rng[0]) & (df_raw['Year'] <= y_rng[1])
        ]
        if not df_all.empty:
            fig_c, ax_c = plt.subplots(figsize=(10, 4))
            comp = df_all.groupby('Region')[idx].mean().sort_values()
            colors = ['red' if r == reg else 'skyblue' for r in comp.index]
            comp.plot(kind='bar', color=colors, ax=ax_c)
            st.pyplot(fig_c)
        else:
            st.info("Немає даних для порівняння")
