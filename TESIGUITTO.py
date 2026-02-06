import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# --- SETUP PAGINA ---
st.set_page_config(page_title="Simulatore Tesi Guitto", layout="wide")

st.markdown("# 🔬 Simulatore Diffusione Inquinanti - Analisi Oro-Urbanistica")
st.write("Modello ADR per lo studio del ristagno di inquinanti in presenza di ostacoli.")

# --- BARRA LATERALE: INPUT E SOGLIE REALI ---
st.sidebar.header("⚙️ Parametri di Controllo")

# Scelta inquinante con soglie scientifiche (ppm)
st.sidebar.subheader("🧪 Agente Chimico")
tipo_gas = st.sidebar.selectbox(
    "Inquinante analizzato",
    ["Biossido di Azoto (NO2)", "Monossido di Carbonio (CO)", "Gas Industriale (Tossico)", "Custom"]
)

if tipo_gas == "Biossido di Azoto (NO2)":
    soglia = 0.1  # Limite salute OMS
    info = "Soglia NO2: 0.1 ppm (Tipico traffico urbano)."
elif tipo_gas == "Monossido di Carbonio (CO)":
    soglia = 9.0  # Limite standard
    info = "Soglia CO: 9.0 ppm (Combustione)."
elif tipo_gas == "Gas Industriale (Tossico)":
    soglia = 0.05 # Molto sensibile
    info = "Soglia Tossica: 0.05 ppm (Rischio Chimico)."
else:
    soglia = st.sidebar.slider("Soglia manuale", 0.01, 10.0, 1.0)
    info = "Soglia impostata manualmente."

st.sidebar.caption(info)

# Parametri fisici (u, K, lambda)
u = st.sidebar.slider("Velocità del vento (u)", 0.0, 5.0, 1.5)
D = st.sidebar.slider("Coefficiente Diffusione (K)", 0.1, 2.0, 0.5)
k_reac = st.sidebar.slider("Reazione/Decadimento", 0.0, 0.1, 0.01)

# Sorgente
st.sidebar.subheader("📍 Sorgente")
src_x = st.sidebar.slider("Posiz. X", 0, 49, 5)
src_y = st.sidebar.slider("Posiz. Y", 0, 49, 25)
q_rate = st.sidebar.number_input("Portata emissione (Q)", 1.0, 500.0, 100.0)

# Ostacoli
n_obst = st.sidebar.slider("Numero edifici", 0, 15, 14)
seed = st.sidebar.number_input("Seme mappa", 0, 100, 42)

# --- INIZIALIZZAZIONE ---
nx, ny = 50, 50
dx, dy = 1.0, 1.0
dt = 0.05
C = np.zeros((nx, ny))
obstacles = np.zeros((nx, ny))

# Generazione palazzi
np.random.seed(seed)
for _ in range(n_obst):
    ox, oy = np.random.randint(15, 45), np.random.randint(5, 45)
    obstacles[ox:ox+4, oy:oy+4] = 1

# --- MOTORE DI CALCOLO ---
def run_sim():
    global C
    C = np.zeros((nx, ny))
    plot_spot = st.empty()
    text_spot = st.empty()
    
    for t in range(100):
        C_new = C.copy()
        C_new[src_x, src_y] += q_rate * dt
        
        for i in range(1, nx-1):
            for j in range(1, ny-1):
                if obstacles[i, j] == 1:
                    C_new[i, j] = 0
                    continue
                
                diff = D * dt * ((C[i+1,j]-2*C[i,j]+C[i-1,j]) + (C[i,j+1]-2*C[i,j]+C[i,j-1]))
                adv = -u * dt * (C[i,j] - C[i-1,j])
                reac = -k_reac * dt * C[i,j]
                C_new[i,j] += diff + adv + reac
        
        C = np.maximum(0, C_new)
        
        # Monitoraggio picchi sui palazzi
        c_max_p = np.max(C[obstacles == 1]) if np.any(obstacles == 1) else 0
        
        if t % 10 == 0:
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='Hot', name='Gas'),
                go.Surface(z=obstacles * (np.max(C)*0.6), colorscale='Greys', opacity=0.5, showscale=False)
            ])
            fig.update_layout(scene=dict(zaxis=dict(range=[0, np.max(C)+1])))
            plot_spot.plotly_chart(fig, use_container_width=True)
            
            alert = "🔴 ALLERTA: RISTAGNO CRITICO" if c_max_p > soglia else "🟢 CONDIZIONI SICURE"
            text_spot.subheader(f"Stato: {alert} | Picco Palazzi: {c_max_p:.3f} / Soglia: {soglia}")

if st.button("🚀 Lancia Simulazione"):
    run_sim()
