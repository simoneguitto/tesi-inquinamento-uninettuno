import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from io import BytesIO

# 1. Impostazioni Iniziali
st.set_page_config(page_title="Tesi ADR", layout="wide")
st.title("Simulatore Dispersione Inquinanti")

# 2. Sidebar per i parametri (Stile Tesi Fedi)
st.sidebar.header("Parametri di Input")
scelta_meteo = st.sidebar.selectbox("Meteo", ["Instabile", "Neutro", "Inversione"])
scelta_pioggia = st.sidebar.select_slider("Pioggia", options=["No", "Bassa", "Forte"])

# Dati fisici (derivati dai capitoli 4 e 5 della tesi di riferimento)
if scelta_meteo == "Instabile":
    D_val, u_val = 1.7, 0.7
elif scelta_meteo == "Neutro":
    D_val, u_val = 1.0, 1.4
else:
    D_val, u_val = 0.2, 0.4

u = st.sidebar.slider("Vento u (m/s)", 0.1, 5.0, u_val)
K = st.sidebar.slider("Diffusione K", 0.1, 2.5, D_val)

gas = st.sidebar.selectbox("Gas", ["Tossico", "NO2", "CO"])
if gas == "Tossico":
    soglia, sol = 0.05, 1.0
elif gas == "NO2":
    soglia, sol = 0.1, 0.8
else:
    soglia, sol = 9.0, 0.3 # CO meno solubile

Q = st.sidebar.slider("Sorgente Q", 50, 250, 100)

# 3. Griglia di calcolo
N = 50
dx = 1.0
dt = 0.04 # Passo tempo per stabilità numerica

# Fattore abbattimento pioggia
kp = {"No": 0.0, "Bassa": 0.08, "Forte": 0.25}[scelta_pioggia]

# Creazione ostacoli (Edifici)
muri = np.zeros((N, N))
np.random.seed(42)
for _ in range(10):
    ix, iy = np.random.randint(20, 44), np.random.randint(10, 39)
    muri[ix:ix+3, iy:iy+3] = 1

# 4. Esecuzione Simulazione
if st.sidebar.button("AVVIA CALCOLO"):
    C = np.zeros((N, N))
    mappa = st.empty()
    avviso = st.empty()
    
    # Punto di rilascio
    sx, sy = 10, 25

    for t in range(140):
        Cn = C.copy()
        Cn[sx, sy] += Q * dt
        
        # Algoritmo Differenze Finite (Metodo Upwind)
        for i in range(1, N-1):
            for j in range(1, N-1):
                if muri[i,j] == 1:
                    Cn[i,j] = 0
                    continue
                
                # Formula ADR (Advezione + Diffusione + Reazione)
                diff = K * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                adv = -u * dt * (C[i,j] - C[i-1,j]) 
                reac = -(kp * sol) * dt * C[i,j]
                
                Cn[i,j] += diff + adv + reac

        C = np.clip(Cn, 0, 100)
        
        if t % 15 == 0:
            picco = np.max(C[20:45, 10:40]) * 0.13
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='Reds'),
                go.Surface(z=muri * 2.5, colorscale='Greys', opacity=0.3, showscale=False)
            ])
            fig.update_layout(scene=dict(zaxis=dict(range=[0, 15])), margin=dict(l=0, r=0, b=0, t=0))
            mappa.plotly_chart(fig, use_container_width=True)
            
            if picco > soglia:
                avviso.error(f"SOGLIA SUPERATA: {picco:.4f} ppm")
            else:
                avviso.success(f"LIVELLI SICURI: {picco:.4f} ppm")

    # 5. Generazione Report Excel (Solo a fine calcolo)
    picco_finale = np.max(C[20:45, 10:40]) * 0.13
    df = pd.DataFrame({
        "Parametro": ["Gas", "Meteo", "Pioggia", "Vento (u)", "Picco Rilevato", "Soglia"],
        "Valore": [gas, scelta_meteo, scelta_pioggia, u, round(picco_finale, 4), soglia]
    })
    
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📩 Scarica Report Excel",
        data=buf.getvalue(),
        file_name="risultati_tesi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
