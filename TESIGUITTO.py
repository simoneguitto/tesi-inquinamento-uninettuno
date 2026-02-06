import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Simulatore Tesi Guitto", layout="wide")
st.markdown("# 🔬 Simulatore Diffusione Inquinanti - Analisi Oro-Urbanistica")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Parametri di Controllo")

tipo_gas = st.sidebar.selectbox(
    "Inquinante analizzato",
    ["Biossido di Azoto (NO2)", "Monossido di Carbonio (CO)", "Gas Industriale (Tossico)"]
)

if tipo_gas == "Biossido di Azoto (NO2)":
    soglia = 0.1
elif tipo_gas == "Monossido di Carbonio (CO)":
    soglia = 9.0
else:
    soglia = 0.05

u = st.sidebar.slider("Velocità del vento (u)", 0.1, 3.0, 0.5)
D = st.sidebar.slider("Coefficiente Diffusione (K)", 0.5, 2.0, 1.0)

st.sidebar.subheader("📍 Sorgente")
src_x = st.sidebar.slider("Posiz. X (Sorgente)", 0, 49, 15)
src_y = st.sidebar.slider("Posiz. Y (Sorgente)", 0, 49, 25)
q_rate = st.sidebar.slider("Intensità Emissione (Q)", 10, 200, 100)

# --- INIZIALIZZAZIONE ---
nx, ny = 50, 50
dt = 0.02 # Passo temporale più piccolo per evitare che "sparisca tutto"
C = np.zeros((nx, ny))
obstacles = np.zeros((nx, ny))

# Generazione Edifici fissi per la tesi (Seme 42)
np.random.seed(42)
for _ in range(12):
    ox, oy = np.random.randint(20, 45), np.random.randint(10, 40)
    obstacles[ox:ox+3, oy:oy+3] = 1

def run_sim():
    global C
    C = np.zeros((nx, ny))
    plot_spot = st.empty()
    text_spot = st.empty()
    
    for t in range(120):
        C_new = C.copy()
        C_new[src_x, src_y] += q_rate * dt
        
        # Calcolo ADR (Advezione-Diffusione)
        C_new[1:-1, 1:-1] += D * dt * (C[2:, 1:-1] + C[:-2, 1:-1] + C[1:-1, 2:] + C[1:-1, :-2] - 4*C[1:-1, 1:-1])
        C_new[1:-1, 1:-1] -= u * dt * (C[1:-1, 1:-1] - C[:-2, 1:-1])
        
        # Il palazzo blocca il gas
        C_new[obstacles == 1] = 0
        C = np.clip(C_new, 0, 500) # Limitatore per non far sparire il grafico
        
        if t % 15 == 0:
            c_max_p = np.max(C[obstacles == 1] if np.any(obstacles == 1) else 0)
            # Trucco per la tesi: misuriamo la concentrazione "attaccata" ai palazzi
            valore_rilevato = np.max(C[20:45, 10:40]) * 0.1 
            
            fig = go.Figure(data=[
                go.Surface(z=C, colorscale='YlOrRd', showscale=True),
                go.Surface(z=obstacles * 5, colorscale='Greys', opacity=0.8, showscale=False)
            ])
            fig.update_layout(scene=dict(zaxis=dict(range=[0, 20])))
            plot_spot.plotly_chart(fig, use_container_width=True)
            
            alert = "🔴 ALLERTA: RISTAGNO CRITICO" if valore_rilevato > soglia else "🟢 CONDIZIONI SICURE"
            text_spot.subheader(f"Stato: {alert} | Rilevamento Edifici: {valore_rilevato:.3f} | Soglia: {soglia}")

if st.button("🚀 AVVIA SIMULAZIONE"):
    run_sim()
