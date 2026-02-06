import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Simulatore ADR - Urban Risk", layout="wide")
st.title("Simulatore Dispersione Inquinanti (Modello ADR)")
st.caption("Evoluzione numerica basata sui modelli di Advezione-Diffusione (Rif. F. Fedi, 2009)")

# --- PARAMETRI METEO ---
st.sidebar.header("Condizioni Ambientali")
meteo = st.sidebar.selectbox("Atmosfera", ["Instabile (Sole)", "Neutra (Coperto)", "Stabile (Inversione)"])
pioggia = st.sidebar.radio("Precipitazioni (Wet Deposition)", ["Nessuna", "Leggera", "Forte"])

# Parametri basati sulla tesi
if meteo == "Instabile (Sole)": D_val, u_val = 1.6, 1.0
elif meteo == "Neutra (Coperto)": D_val, u_val = 1.0, 2.0
else: D_val, u_val = 0.2, 0.5

k_reac = 0.01 if pioggia == "Nessuna" else 0.1 if pioggia == "Leggera" else 0.25

u = st.sidebar.slider("Vento (u) [m/s]", 0.1, 5.0, u_val)
D = st.sidebar.slider("Diffusione (K)", 0.1, 2.0, D_val)

# --- SORGENTE E GRIGLIA ---
sostanza = st.sidebar.selectbox("Sostanza (Rif. Bhopal)", ["Gas Tossico (MIC)", "NO2", "CO"])
soglia = 0.05 if sostanza == "Gas Tossico (MIC)" else 0.1 if sostanza == "NO2" else 9.0
q_rate = st.sidebar.slider("Sorgente (Q)", 50, 250, 100)

nx, ny, dx = 50, 50, 1.0
dt = 0.4 * (dx / (u + D + 0.1)) # Stabilità CFL
if dt > 0.05: dt = 0.05

# Edifici
obstacles = np.zeros((nx, ny))
np.random.seed(42)
for _ in range(12):
    ox, oy = np.random.randint(20, 45), np.random.randint(10, 40)
    obstacles[ox:ox+3, oy:oy+3] = 1

def run():
    C = np.zeros((nx, ny))
    plot = st.empty()
    info = st.empty()
    
    for t in range(130):
        C_new = C.copy()
        C_new[10, 25] += q_rate * dt # Sorgente
        
        for i in range(1, nx-1):
            for j in range(1, ny-1):
                if obstacles[i,j] == 1:
                    C_new[i,j] = 0
                    continue
                # Formula ADR (Advezione-Diffusione-Reazione)
                diff = D * dt * (C[i+1,j] + C[i-1,j] + C[i,j+1] + C[i,j-1] - 4*C[i,j])
                adv = -u * dt * (C[i,j] - C[i-1,j])
                reac = -k_reac * dt * C[i,j]
                C_new[i,j] += diff + adv + reac

        C = np.clip(C_new, 0, 50)
        
        if t % 13 == 0:
            picco = np.max(C[20:45, 10:40]) * 0.12
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='YlOrRd', showscale=True),
                go.Surface(z=obstacles * 2, colorscale='Greys', opacity=0.4, showscale=False)
            ])
            fig.update_layout(scene=dict(zaxis=dict(range=[0, 12])), margin=dict(l=0, r=0, b=0, t=0))
            plot.plotly_chart(fig, use_container_width=True)
            
            res = "ALLERTA" if picco > soglia else "SICURO"
            info.write(f"**Stato:** {res} | **Picco Edifici:** {picco:.3f} ppm | **Soglia:** {soglia}")

if st.sidebar.button("Esegui Simulazione"):
    run()
